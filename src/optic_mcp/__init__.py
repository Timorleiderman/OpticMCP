"""OpticMCP - MCP server for USB camera capture with OpenCV."""

__version__ = "0.6.0"

# Core modules are imported here for backwards compatibility
from optic_mcp import usb
from optic_mcp import rtsp
from optic_mcp import hls

# New modules are NOT auto-imported to avoid requiring dependencies
# at import time. Users can import them directly:
#   from optic_mcp import mjpeg
#   from optic_mcp import screen
#   from optic_mcp import http_image
#   from optic_mcp import decode (requires libzbar)

__all__ = ["usb", "rtsp", "hls"]
