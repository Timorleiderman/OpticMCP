"""Camera streaming module - serves MJPEG streams over HTTP."""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional

import cv2


class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP request handler that serves MJPEG streams."""

    def log_message(self, format, *args):
        """Suppress HTTP server logs to avoid polluting MCP stdio."""
        pass

    def do_GET(self):
        """Handle GET requests - serve MJPEG stream or status page."""
        if self.path == "/":
            self._serve_status_page()
        elif self.path == "/stream":
            self._serve_mjpeg_stream()
        else:
            self.send_error(404, "Not Found")

    def _serve_status_page(self):
        """Serve a simple HTML page with the stream embedded."""
        stream_server: StreamServer = self.server  # type: ignore[assignment]
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>OpticMCP Stream</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; background: #1a1a1a; color: #fff; }}
        img {{ max-width: 100%; border: 2px solid #333; }}
        h1 {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>OpticMCP Camera Stream</h1>
    <p>Camera Index: {stream_server.camera_index}</p>
    <img src="/stream" alt="Camera Stream">
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_mjpeg_stream(self):
        """Serve the MJPEG stream."""
        stream_server: StreamServer = self.server  # type: ignore[assignment]
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

        try:
            while stream_server.streaming:
                frame_data = stream_server.get_frame()
                if frame_data is not None:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(frame_data)
                    self.wfile.write(b"\r\n")
                else:
                    time.sleep(0.01)
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected
            pass


class StreamServer(HTTPServer):
    """HTTP server that captures and serves camera frames."""

    def __init__(self, camera_index: int, port: int):
        """
        Initialize the stream server.

        Args:
            camera_index: The camera index to stream from
            port: The port to serve the stream on
        """
        super().__init__(("localhost", port), MJPEGHandler)
        self.camera_index = camera_index
        self.port = port
        self.streaming = False
        self._frame: Optional[bytes] = None
        self._frame_lock = threading.Lock()
        self._cap: Optional[cv2.VideoCapture] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._server_thread: Optional[threading.Thread] = None

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame as JPEG bytes."""
        with self._frame_lock:
            return self._frame

    def _capture_loop(self):
        """Continuously capture frames from the camera."""
        self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            self.streaming = False
            return

        # Minimize buffer size to reduce latency - only keep the latest frame
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Warm up the camera
        for _ in range(3):
            self._cap.grab()

        while self.streaming:
            # Grab the latest frame (flush any buffered frames)
            if self._cap.grab():
                ret, frame = self._cap.retrieve()
                if ret and frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    with self._frame_lock:
                        self._frame = buffer.tobytes()
            # Minimal sleep to yield CPU but maintain low latency
            time.sleep(0.001)

        self._cap.release()
        self._cap = None

    def start(self):
        """Start the camera capture and HTTP server."""
        if self.streaming:
            return

        self.streaming = True

        # Start capture thread
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

        # Wait a bit for camera to initialize
        time.sleep(0.5)

        if not self.streaming:
            raise RuntimeError(f"Could not open camera at index {self.camera_index}")

        # Start server thread
        self._server_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._server_thread.start()

    def stop(self):
        """Stop the camera capture and HTTP server."""
        self.streaming = False
        self.shutdown()

        if self._capture_thread:
            self._capture_thread.join(timeout=2)
            self._capture_thread = None

        if self._server_thread:
            self._server_thread.join(timeout=2)
            self._server_thread = None


class StreamManager:
    """Manages all active camera streams."""

    _instance: Optional["StreamManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize the stream manager."""
        self._streams: Dict[int, StreamServer] = {}

    def __new__(cls):
        """Singleton pattern to ensure only one manager exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def start_stream(self, camera_index: int = 0, port: int = 8080) -> dict:
        """
        Start streaming a camera to a localhost HTTP server.

        Args:
            camera_index: The camera index to stream (default 0)
            port: The port to serve the stream on (default 8080)

        Returns:
            Dictionary with stream URL and status
        """
        if camera_index in self._streams:
            existing = self._streams[camera_index]
            return {
                "status": "already_running",
                "camera_index": camera_index,
                "port": existing.port,
                "url": f"http://localhost:{existing.port}",
                "stream_url": f"http://localhost:{existing.port}/stream",
            }

        # Check if port is already in use by another stream
        for idx, server in self._streams.items():
            if server.port == port:
                raise RuntimeError(
                    f"Port {port} is already in use by camera {idx}. Choose a different port."
                )

        server = StreamServer(camera_index, port)
        server.start()
        self._streams[camera_index] = server

        return {
            "status": "started",
            "camera_index": camera_index,
            "port": port,
            "url": f"http://localhost:{port}",
            "stream_url": f"http://localhost:{port}/stream",
        }

    def stop_stream(self, camera_index: int = 0) -> dict:
        """
        Stop streaming a camera.

        Args:
            camera_index: The camera index to stop streaming

        Returns:
            Dictionary with status
        """
        if camera_index not in self._streams:
            return {
                "status": "not_running",
                "camera_index": camera_index,
            }

        server = self._streams.pop(camera_index)
        server.stop()

        return {
            "status": "stopped",
            "camera_index": camera_index,
        }

    def list_streams(self) -> list:
        """
        List all active streams.

        Returns:
            List of active stream information
        """
        streams = []
        for camera_index, server in self._streams.items():
            streams.append(
                {
                    "camera_index": camera_index,
                    "port": server.port,
                    "url": f"http://localhost:{server.port}",
                    "stream_url": f"http://localhost:{server.port}/stream",
                    "streaming": server.streaming,
                }
            )
        return streams

    def stop_all(self):
        """Stop all active streams."""
        for camera_index in list(self._streams.keys()):
            self.stop_stream(camera_index)


# Module-level functions for easy access
_manager = StreamManager()


def start_stream(camera_index: int = 0, port: int = 8080) -> dict:
    """
    Start streaming a camera to a localhost HTTP server.

    The stream can be viewed in any browser at http://localhost:{port}
    or the raw MJPEG stream at http://localhost:{port}/stream

    Args:
        camera_index: The camera index to stream (default 0)
        port: The port to serve the stream on (default 8080)

    Returns:
        Dictionary with stream URL and status
    """
    return _manager.start_stream(camera_index, port)


def stop_stream(camera_index: int = 0) -> dict:
    """
    Stop streaming a camera.

    Args:
        camera_index: The camera index to stop streaming

    Returns:
        Dictionary with status
    """
    return _manager.stop_stream(camera_index)


def list_streams() -> list:
    """
    List all active camera streams.

    Returns:
        List of active stream information including URLs and ports
    """
    return _manager.list_streams()


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the multi-camera dashboard."""

    def log_message(self, format, *args):
        """Suppress HTTP server logs to avoid polluting MCP stdio."""
        pass

    def do_GET(self):
        """Handle GET requests - serve dashboard or API."""
        if self.path == "/":
            self._serve_dashboard()
        elif self.path == "/api/streams":
            self._serve_streams_api()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests - stop streams."""
        if self.path == "/api/stop-all":
            self._stop_all_streams()
        elif self.path.startswith("/api/stop/"):
            camera_index = int(self.path.split("/")[-1])
            self._stop_stream(camera_index)
        else:
            self.send_error(404, "Not Found")

    def _stop_stream(self, camera_index: int):
        """Stop a specific camera stream."""
        result = _manager.stop_stream(camera_index)
        data = json.dumps(result)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data.encode())

    def _stop_all_streams(self):
        """Stop all camera streams."""
        _manager.stop_all()
        data = json.dumps({"status": "stopped_all"})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data.encode())

    def _serve_dashboard(self):
        """Serve the dynamic multi-camera dashboard HTML page."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>OpticMCP Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }
        h1 { color: #4CAF50; font-size: 1.8em; }
        .header-controls {
            margin-top: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }
        .status { color: #888; font-size: 0.9em; }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover { background: #c82333; }
        .btn-danger:disabled {
            background: #555;
            cursor: not-allowed;
        }
        .btn-stop {
            background: #ff6b6b;
            color: white;
            padding: 4px 10px;
            font-size: 0.8em;
        }
        .btn-stop:hover { background: #ee5a5a; }
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 15px;
            max-width: 1800px;
            margin: 0 auto;
        }
        .camera-card {
            background: #1a1a1a;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #333;
        }
        .camera-header {
            padding: 10px 15px;
            background: #222;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .camera-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .camera-title { font-weight: 600; }
        .camera-port { color: #4CAF50; font-size: 0.85em; }
        .camera-card img {
            width: 100%;
            display: block;
            background: #000;
            min-height: 200px;
        }
        .no-streams {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        .no-streams p { margin-top: 10px; }
    </style>
</head>
<body>
    <header>
        <h1>OpticMCP Dashboard</h1>
        <div class="header-controls">
            <span class="status" id="status">Loading...</span>
            <button class="btn btn-danger" id="stop-all-btn" onclick="stopAllStreams()">Stop All</button>
        </div>
    </header>
    <div class="camera-grid" id="grid"></div>

    <script>
        let lastStreamCount = -1;

        async function stopStream(cameraIndex) {
            try {
                await fetch('/api/stop/' + cameraIndex, { method: 'POST' });
                lastStreamCount = -1;
                updateDashboard();
            } catch (e) {
                console.error('Failed to stop stream:', e);
            }
        }

        async function stopAllStreams() {
            try {
                await fetch('/api/stop-all', { method: 'POST' });
                lastStreamCount = -1;
                updateDashboard();
            } catch (e) {
                console.error('Failed to stop all streams:', e);
            }
        }

        async function updateDashboard() {
            try {
                const response = await fetch('/api/streams');
                const streams = await response.json();
                const grid = document.getElementById('grid');
                const status = document.getElementById('status');
                const stopAllBtn = document.getElementById('stop-all-btn');

                status.textContent = streams.length + ' active stream' + (streams.length !== 1 ? 's' : '');
                stopAllBtn.disabled = streams.length === 0;

                if (streams.length === 0) {
                    grid.innerHTML = '<div class="no-streams"><h2>No Active Streams</h2><p>Start a camera stream to see it here.</p></div>';
                    lastStreamCount = 0;
                    return;
                }

                // Only rebuild DOM if stream count changed
                if (streams.length !== lastStreamCount) {
                    grid.innerHTML = streams.map(s => `
                        <div class="camera-card" id="cam-${s.camera_index}">
                            <div class="camera-header">
                                <div class="camera-info">
                                    <span class="camera-title">Camera ${s.camera_index}</span>
                                    <span class="camera-port">:${s.port}</span>
                                </div>
                                <button class="btn btn-stop" onclick="stopStream(${s.camera_index})">Stop</button>
                            </div>
                            <img src="${s.stream_url}" alt="Camera ${s.camera_index}">
                        </div>
                    `).join('');
                    lastStreamCount = streams.length;
                }
            } catch (e) {
                document.getElementById('status').textContent = 'Connection error';
            }
        }

        updateDashboard();
        setInterval(updateDashboard, 3000);
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_streams_api(self):
        """Serve JSON API with list of active streams."""
        streams = _manager.list_streams()
        data = json.dumps(streams)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode())


class DashboardServer(HTTPServer):
    """HTTP server for the multi-camera dashboard."""

    def __init__(self, port: int):
        """
        Initialize the dashboard server.

        Args:
            port: The port to serve the dashboard on
        """
        super().__init__(("localhost", port), DashboardHandler)
        self.port = port
        self._server_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the dashboard server."""
        self._server_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._server_thread.start()

    def stop(self):
        """Stop the dashboard server."""
        self.shutdown()
        if self._server_thread:
            self._server_thread.join(timeout=2)
            self._server_thread = None


# Dashboard singleton
_dashboard: Optional[DashboardServer] = None


def start_dashboard(port: int = 9000) -> dict:
    """
    Start the multi-camera dashboard server.

    The dashboard automatically detects all active camera streams
    and displays them in a responsive grid layout.

    Args:
        port: The port to serve the dashboard on (default 9000)

    Returns:
        Dictionary with dashboard URL and status
    """
    global _dashboard

    if _dashboard is not None:
        return {
            "status": "already_running",
            "port": _dashboard.port,
            "url": f"http://localhost:{_dashboard.port}",
        }

    _dashboard = DashboardServer(port)
    _dashboard.start()

    return {
        "status": "started",
        "port": port,
        "url": f"http://localhost:{port}",
    }


def stop_dashboard() -> dict:
    """
    Stop the multi-camera dashboard server.

    Returns:
        Dictionary with status
    """
    global _dashboard

    if _dashboard is None:
        return {"status": "not_running"}

    _dashboard.stop()
    _dashboard = None

    return {"status": "stopped"}
