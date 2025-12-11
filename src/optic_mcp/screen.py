"""Screen capture module.

This module provides tools to capture screenshots of desktop monitors
or specific screen regions. Useful for monitoring applications,
dashboards, or remote desktop scenarios.
"""

import os
from typing import Dict, List

import mss
import mss.tools

from optic_mcp.validation import validate_file_path


def list_monitors() -> List[Dict]:
    """
    Lists all available monitors/displays connected to the system.
    Monitor 0 represents all monitors combined, monitor 1+ are individual displays.

    Returns:
        List of monitor dictionaries with:
            - id: monitor index (0 = all monitors, 1+ = specific monitor)
            - left: X coordinate of monitor's left edge
            - top: Y coordinate of monitor's top edge
            - width: monitor width in pixels
            - height: monitor height in pixels
            - primary: True if this is the primary monitor (always False for id=0)
    """
    with mss.mss() as sct:
        monitors = []
        for i, monitor in enumerate(sct.monitors):
            monitors.append(
                {
                    "id": i,
                    "left": monitor["left"],
                    "top": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"],
                    "primary": i == 1,  # Monitor 1 is typically the primary
                }
            )
        return monitors


def save_image(file_path: str, monitor: int = 0) -> Dict:
    """
    Captures full screenshot of specified monitor and saves to file.
    Monitor 0 captures all monitors combined into one image.
    Monitor 1+ captures specific individual monitors.

    Args:
        file_path: Path where the image will be saved. Must be in an allowed
            directory and have a valid image extension (.jpg, .png, etc.)
        monitor: Monitor index to capture (0 = all monitors, 1+ = specific monitor).

    Returns:
        Dictionary with capture result:
            - status: 'success'
            - file_path: path where image was saved
            - width: captured image width in pixels
            - height: captured image height in pixels
            - monitor: monitor index that was captured

    Raises:
        ValueError: If file_path is invalid or monitor index out of range.
        RuntimeError: If screenshot capture fails.
    """
    validated_path = validate_file_path(file_path)

    if not isinstance(monitor, int) or monitor < 0:
        raise ValueError(f"Monitor must be a non-negative integer, got {monitor}")

    with mss.mss() as sct:
        # Check monitor index is valid
        if monitor >= len(sct.monitors):
            raise ValueError(
                f"Invalid monitor index {monitor}. Available monitors: 0-{len(sct.monitors) - 1}"
            )

        try:
            # Capture the monitor
            screenshot = sct.grab(sct.monitors[monitor])

            # Determine output format from file extension
            _, ext = os.path.splitext(validated_path)
            ext = ext.lower()

            # mss.tools.to_png can save to file
            if ext == ".png":
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=validated_path)
            else:
                # For other formats, use PIL
                from PIL import Image

                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img.save(validated_path)

            return {
                "status": "success",
                "file_path": validated_path,
                "width": screenshot.width,
                "height": screenshot.height,
                "monitor": monitor,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to capture screenshot: {str(e)}")


def save_region(file_path: str, x: int, y: int, width: int, height: int) -> Dict:
    """
    Captures a specific region of the screen and saves to file.
    Coordinates are absolute screen coordinates (0,0 is top-left of primary monitor).

    Args:
        file_path: Path where the image will be saved. Must be in an allowed
            directory and have a valid image extension (.jpg, .png, etc.)
        x: X coordinate of region's top-left corner.
        y: Y coordinate of region's top-left corner.
        width: Width of region in pixels.
        height: Height of region in pixels.

    Returns:
        Dictionary with capture result:
            - status: 'success'
            - file_path: path where image was saved
            - width: captured region width in pixels
            - height: captured region height in pixels
            - region: dict with x, y, width, height

    Raises:
        ValueError: If file_path is invalid or region parameters are invalid.
        RuntimeError: If screenshot capture fails.
    """
    validated_path = validate_file_path(file_path)

    # Validate region parameters
    if not isinstance(x, int) or x < 0:
        raise ValueError(f"x must be a non-negative integer, got {x}")
    if not isinstance(y, int) or y < 0:
        raise ValueError(f"y must be a non-negative integer, got {y}")
    if not isinstance(width, int) or width <= 0:
        raise ValueError(f"width must be a positive integer, got {width}")
    if not isinstance(height, int) or height <= 0:
        raise ValueError(f"height must be a positive integer, got {height}")

    with mss.mss() as sct:
        try:
            # Define the region to capture
            region = {"left": x, "top": y, "width": width, "height": height}

            # Capture the region
            screenshot = sct.grab(region)

            # Determine output format from file extension
            _, ext = os.path.splitext(validated_path)
            ext = ext.lower()

            # Save the image
            if ext == ".png":
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=validated_path)
            else:
                from PIL import Image

                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img.save(validated_path)

            return {
                "status": "success",
                "file_path": validated_path,
                "width": screenshot.width,
                "height": screenshot.height,
                "region": {"x": x, "y": y, "width": width, "height": height},
            }

        except Exception as e:
            raise RuntimeError(f"Failed to capture screen region: {str(e)}")
