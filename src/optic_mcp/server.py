import os


# Suppress OpenCV's stderr noise BEFORE importing cv2
# This is critical for MCP stdio communication
def _suppress_opencv_stderr():
    """Redirect stderr to /dev/null at the OS level to silence OpenCV debug messages."""
    original_stderr_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    return original_stderr_fd


# Suppress stderr before cv2 import
_original_stderr = _suppress_opencv_stderr()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from optic_mcp import usb as usb  # noqa: E402
from optic_mcp import rtsp as rtsp  # noqa: E402
from optic_mcp import hls as hls  # noqa: E402
from optic_mcp import stream as stream  # noqa: E402

# Initialize the MCP server
mcp = FastMCP("optic-mcp")


# USB Camera Tools
@mcp.tool()
def list_cameras():
    """
    Scans for available USB cameras connected to the system.
    Returns a list of available camera indices and their status.
    """
    return usb.list_cameras()


@mcp.tool()
def save_image(file_path: str, camera_index: int = 0):
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.
    """
    return usb.save_image(file_path, camera_index)


# RTSP Stream Tools
@mcp.tool()
def rtsp_save_image(rtsp_url: str, file_path: str, timeout_seconds: int = 10):
    """
    Captures a frame from an RTSP stream and saves it to the given file path.
    Returns a success message with the file path.

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    return rtsp.save_image(rtsp_url, file_path, timeout_seconds)


@mcp.tool()
def rtsp_check_stream(rtsp_url: str, timeout_seconds: int = 10):
    """
    Validates an RTSP stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Returns a dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code
    """
    return rtsp.check_stream(rtsp_url, timeout_seconds)


# HLS Stream Tools
@mcp.tool()
def hls_save_image(hls_url: str, file_path: str, timeout_seconds: int = 30):
    """
    Captures a frame from an HLS stream and saves it to the given file path.
    Returns a success message with the file path.

    HLS streams are commonly used by webcams, surveillance systems,
    and streaming services. They typically use .m3u8 playlist files.

    Common HLS URL formats:
        - http://server/stream.m3u8
        - https://server/live/stream.m3u8
        - http://server/streams/{stream_id}/stream.m3u8
    """
    return hls.save_image(hls_url, file_path, timeout_seconds)


@mcp.tool()
def hls_check_stream(hls_url: str, timeout_seconds: int = 30):
    """
    Validates an HLS stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Returns a dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code
    """
    return hls.check_stream(hls_url, timeout_seconds)


# Camera Streaming Tools
@mcp.tool()
def start_stream(camera_index: int = 0, port: int = 8080):
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
    return stream.start_stream(camera_index, port)


@mcp.tool()
def stop_stream(camera_index: int = 0):
    """
    Stop streaming a camera.

    Args:
        camera_index: The camera index to stop streaming

    Returns:
        Dictionary with status
    """
    return stream.stop_stream(camera_index)


@mcp.tool()
def list_streams():
    """
    List all active camera streams.

    Returns:
        List of active stream information including URLs and ports
    """
    return stream.list_streams()


@mcp.tool()
def start_dashboard(port: int = 9000):
    """
    Start the multi-camera dashboard server.

    The dashboard automatically detects all active camera streams
    and displays them in a responsive grid layout. Streams can be
    started/stopped dynamically and the dashboard will update.

    Args:
        port: The port to serve the dashboard on (default 9000)

    Returns:
        Dictionary with dashboard URL and status
    """
    return stream.start_dashboard(port)


@mcp.tool()
def stop_dashboard():
    """
    Stop the multi-camera dashboard server.

    Returns:
        Dictionary with status
    """
    return stream.stop_dashboard()


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
