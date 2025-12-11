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
from optic_mcp import mjpeg as mjpeg  # noqa: E402
from optic_mcp import screen as screen  # noqa: E402
from optic_mcp import http_image as http_image  # noqa: E402

# decode module requires libzbar system library, import conditionally
try:
    from optic_mcp import decode as decode  # noqa: E402

    DECODE_AVAILABLE = True
except ImportError:
    decode = None  # noqa: E402
    DECODE_AVAILABLE = False

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


# MJPEG Stream Tools
@mcp.tool()
def mjpeg_save_image(mjpeg_url: str, file_path: str, timeout_seconds: int = 10):
    """
    Captures a frame from an MJPEG stream and saves it to the given file path.
    MJPEG streams are common in basic IP cameras, ESP32-CAM, Arduino cameras,
    and legacy surveillance systems.

    Common MJPEG URL formats:
        - http://camera/video.mjpg
        - http://192.168.1.100:8080/mjpg/video.mjpg
        - http://camera:8080/?action=stream
        - http://user:pass@camera/video.mjpeg

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://)
        file_path: Path where the image will be saved
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, file_path, and size_bytes
    """
    return mjpeg.save_image(mjpeg_url, file_path, timeout_seconds)


@mcp.tool()
def mjpeg_check_stream(mjpeg_url: str, timeout_seconds: int = 10):
    """
    Validates an MJPEG stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://)
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, url (sanitized), content_type, and error if unavailable
    """
    return mjpeg.check_stream(mjpeg_url, timeout_seconds)


# Screen Capture Tools
@mcp.tool()
def screen_list_monitors():
    """
    Lists all available monitors/displays connected to the system.
    Monitor 0 represents all monitors combined, monitor 1+ are individual displays.

    Returns:
        List of monitors with id, left, top, width, height, and primary flag
    """
    return screen.list_monitors()


@mcp.tool()
def screen_save_image(file_path: str, monitor: int = 0):
    """
    Captures full screenshot of specified monitor and saves to file.
    Monitor 0 captures all monitors combined into one image.
    Monitor 1+ captures specific individual monitors.

    Args:
        file_path: Path where the image will be saved
        monitor: Monitor index to capture (0 = all monitors, 1+ = specific monitor)

    Returns:
        Dictionary with status, file_path, width, height, and monitor index
    """
    return screen.save_image(file_path, monitor)


@mcp.tool()
def screen_save_region(file_path: str, x: int, y: int, width: int, height: int):
    """
    Captures a specific region of the screen and saves to file.
    Coordinates are absolute screen coordinates (0,0 is top-left of primary monitor).

    Args:
        file_path: Path where the image will be saved
        x: X coordinate of region's top-left corner
        y: Y coordinate of region's top-left corner
        width: Width of region in pixels
        height: Height of region in pixels

    Returns:
        Dictionary with status, file_path, width, height, and region details
    """
    return screen.save_region(file_path, x, y, width, height)


# HTTP Image Tools
@mcp.tool()
def http_save_image(url: str, file_path: str, timeout_seconds: int = 30):
    """
    Downloads image from URL and saves to the given file path.
    Supports redirects and basic authentication in URL.

    Args:
        url: URL of the image (http:// or https://)
        file_path: Path where the image will be saved
        timeout_seconds: Connection timeout in seconds (default 30)

    Returns:
        Dictionary with status, file_path, size_bytes, and content_type
    """
    return http_image.save_image(url, file_path, timeout_seconds)


@mcp.tool()
def http_check_image(url: str, timeout_seconds: int = 10):
    """
    Validates an HTTP image URL using a HEAD request.
    Useful for checking image availability without downloading.

    Args:
        url: URL of the image (http:// or https://)
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, url (sanitized), content_type, size_bytes, and error if unavailable
    """
    return http_image.check_image(url, timeout_seconds)


# QR/Barcode Decode Tools (requires libzbar system library)
if DECODE_AVAILABLE:

    @mcp.tool()
    def decode_qr(file_path: str):
        """
        Decodes QR codes from an image file.
        Only detects QR codes, ignores other barcode types.

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type, rect (bounding box), and polygon (corner points)
        """
        return decode.decode_qr(file_path)

    @mcp.tool()
    def decode_barcode(file_path: str):
        """
        Decodes barcodes from an image file.
        Detects common barcode formats: EAN, UPC, Code128, Code39, etc.
        Does NOT detect QR codes (use decode_qr for that).

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type (EAN13, CODE128, etc.), rect, and polygon
        """
        return decode.decode_barcode(file_path)

    @mcp.tool()
    def decode_all(file_path: str):
        """
        Decodes all supported code types from an image file.
        Detects both QR codes and all barcode formats.

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type (QRCODE, EAN13, CODE128, etc.), rect, and polygon
        """
        return decode.decode_all(file_path)

    @mcp.tool()
    def decode_and_annotate(file_path: str, output_path: str):
        """
        Decodes all codes from an image and saves annotated image with bounding boxes.
        Each detected code is outlined and labeled with its type and data.

        Args:
            file_path: Path to the input image file
            output_path: Path where annotated image will be saved

        Returns:
            Dictionary with found, count, output_path, and codes list
        """
        return decode.decode_and_annotate(file_path, output_path)


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
