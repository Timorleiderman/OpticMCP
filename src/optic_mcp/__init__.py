"""OpticMCP - MCP server for USB camera capture with OpenCV."""

__version__ = "0.3.0"

from optic_mcp import usb
from optic_mcp import rtsp
from optic_mcp import hls

__all__ = ["usb", "rtsp", "hls"]
