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
def capture_image(camera_index: int = 0):
    """
    Captures a single frame from the specified camera index.
    Returns the image as a base64 encoded JPEG string.
    """
    return usb.capture_image(camera_index)


@mcp.tool()
def save_image(file_path: str, camera_index: int = 0):
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.
    """
    return usb.save_image(file_path, camera_index)


# RTSP Stream Tools
@mcp.tool()
def rtsp_capture_image(rtsp_url: str, timeout_seconds: int = 10):
    """
    Captures a single frame from an RTSP stream URL.
    Returns the image as a base64 encoded JPEG string.

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    return rtsp.capture_image(rtsp_url, timeout_seconds)


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
def hls_capture_image(hls_url: str, timeout_seconds: int = 30):
    """
    Captures a single frame from an HLS (HTTP Live Streaming) URL.
    Returns the image as a base64 encoded JPEG string.

    HLS streams are commonly used by webcams, surveillance systems,
    and streaming services. They typically use .m3u8 playlist files.

    Common HLS URL formats:
        - http://server/stream.m3u8
        - https://server/live/stream.m3u8
        - http://server/streams/{stream_id}/stream.m3u8
    """
    return hls.capture_image(hls_url, timeout_seconds)


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


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
