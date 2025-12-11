"""MJPEG stream capture module.

This module provides tools to capture frames from HTTP MJPEG streams.
Common in basic IP cameras, ESP32-CAM, Arduino cameras, and legacy
surveillance systems.
"""

import os
from typing import Dict

import requests

from optic_mcp.validation import (
    validate_file_path,
    validate_timeout,
    validate_http_url,
    sanitize_url_for_display,
)


# MJPEG boundary markers
MJPEG_BOUNDARY_MARKERS = [
    b"--mjpegboundary",
    b"--boundarydonotcross",
    b"--frame",
    b"--myboundary",
    b"--boundary",
    b"--video boundary--",
]

# JPEG markers
JPEG_START = b"\xff\xd8"
JPEG_END = b"\xff\xd9"


def _find_jpeg_frame(data: bytes) -> bytes:
    """
    Extract first complete JPEG frame from data buffer.

    Args:
        data: Raw bytes from MJPEG stream.

    Returns:
        JPEG image bytes.

    Raises:
        ValueError: If no complete JPEG frame found.
    """
    start_idx = data.find(JPEG_START)
    if start_idx == -1:
        raise ValueError("No JPEG start marker found in stream data")

    end_idx = data.find(JPEG_END, start_idx)
    if end_idx == -1:
        raise ValueError("No JPEG end marker found in stream data")

    # Include the end marker (2 bytes)
    return data[start_idx : end_idx + 2]


def check_stream(mjpeg_url: str, timeout_seconds: int = 10) -> Dict:
    """
    Validates MJPEG stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://).
        timeout_seconds: Connection timeout in seconds (1-300).

    Returns:
        Dictionary with stream status and properties:
            - status: 'available' or 'unavailable'
            - url: sanitized URL (credentials hidden)
            - content_type: MIME type from server
            - error: error message if unavailable
    """
    # Validate inputs
    validate_http_url(mjpeg_url)
    validated_timeout = validate_timeout(timeout_seconds)

    sanitized_url = sanitize_url_for_display(mjpeg_url)

    try:
        # Use HEAD request first to check availability
        response = requests.head(
            mjpeg_url,
            timeout=validated_timeout,
            allow_redirects=True,
        )

        content_type = response.headers.get("Content-Type", "unknown")

        if response.status_code == 200:
            # Check if it looks like an MJPEG stream
            is_mjpeg = (
                "multipart" in content_type.lower()
                or "mjpeg" in content_type.lower()
                or "jpeg" in content_type.lower()
            )

            if is_mjpeg:
                return {
                    "status": "available",
                    "url": sanitized_url,
                    "content_type": content_type,
                }
            else:
                # Try GET to verify - some servers don't return correct content-type on HEAD
                response = requests.get(
                    mjpeg_url,
                    timeout=validated_timeout,
                    stream=True,
                )
                content_type = response.headers.get("Content-Type", "unknown")
                response.close()

                return {
                    "status": "available",
                    "url": sanitized_url,
                    "content_type": content_type,
                }

        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": content_type,
            "error": f"HTTP {response.status_code}",
        }

    except requests.exceptions.Timeout:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "error": f"Connection timeout after {validated_timeout} seconds",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "error": f"Connection error: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "error": str(e),
        }


def save_image(mjpeg_url: str, file_path: str, timeout_seconds: int = 10) -> Dict:
    """
    Captures a frame from MJPEG stream and saves it to the given file path.
    Connects to MJPEG stream over HTTP and parses multipart MIME boundary
    to extract the first complete JPEG frame.

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://).
            Supported formats:
                - http://camera/video.mjpg
                - http://192.168.1.100:8080/mjpg/video.mjpg
                - http://camera:8080/?action=stream
                - http://user:pass@camera/video.mjpeg
        file_path: Path where the image will be saved. Must be in an allowed
            directory and have a valid image extension (.jpg, .png, etc.)
        timeout_seconds: Connection timeout in seconds (1-300).

    Returns:
        Dictionary with capture result:
            - status: 'success'
            - file_path: path where image was saved
            - size_bytes: size of saved image in bytes

    Raises:
        ValueError: If URL or file_path is invalid.
        RuntimeError: If stream cannot be connected or frame cannot be captured.
    """
    # Validate inputs
    validate_http_url(mjpeg_url)
    validated_path = validate_file_path(file_path)
    validated_timeout = validate_timeout(timeout_seconds)

    sanitized_url = sanitize_url_for_display(mjpeg_url)

    try:
        # Stream the response to avoid loading entire stream into memory
        response = requests.get(
            mjpeg_url,
            timeout=validated_timeout,
            stream=True,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to connect to MJPEG stream at {sanitized_url}: HTTP {response.status_code}"
            )

        # Read enough data to get first frame
        # Most JPEG frames are under 500KB, read up to 2MB to be safe
        max_bytes = 2 * 1024 * 1024
        chunk_size = 4096
        data = b""
        jpeg_data = None

        try:
            for chunk in response.iter_content(chunk_size=chunk_size):
                data += chunk

                # Try to find a complete JPEG frame
                if JPEG_START in data and JPEG_END in data:
                    try:
                        jpeg_data = _find_jpeg_frame(data)
                        break
                    except ValueError:
                        pass

                if len(data) > max_bytes:
                    raise RuntimeError(
                        f"Could not find complete JPEG frame in first {max_bytes} bytes "
                        f"of MJPEG stream at {sanitized_url}"
                    )
        finally:
            response.close()

        if jpeg_data is None:
            raise RuntimeError(f"Could not extract JPEG frame from MJPEG stream at {sanitized_url}")

        # Save the frame
        with open(validated_path, "wb") as f:
            f.write(jpeg_data)

        size_bytes = os.path.getsize(validated_path)

        return {
            "status": "success",
            "file_path": validated_path,
            "size_bytes": size_bytes,
        }

    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Connection to MJPEG stream at {sanitized_url} timed out "
            f"after {validated_timeout} seconds"
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Failed to connect to MJPEG stream at {sanitized_url}: {str(e)}")
