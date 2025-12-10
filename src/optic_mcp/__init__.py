"""OpticMCP - MCP server for USB camera capture with OpenCV."""

__version__ = "0.2.0"

from optic_mcp import usb
from optic_mcp import rtsp

__all__ = ["usb", "rtsp"]
