"""RTSP stream handling module."""

import cv2

from optic_mcp.validation import (
    validate_file_path,
    validate_timeout,
    validate_rtsp_url,
    sanitize_url_for_display,
)


def save_image(rtsp_url: str, file_path: str, timeout_seconds: int = 10) -> str:
    """
    Captures a frame from an RTSP stream and saves it to the given file path.
    Returns a success message with the file path.

    Args:
        rtsp_url: The RTSP stream URL (e.g., rtsp://username:password@ip:port/path)
        file_path: The path where the image will be saved. Must be in an allowed
                   directory and have a valid image extension.
        timeout_seconds: Connection timeout in seconds (default: 10, max: 300)

    Returns:
        Success message with file path.

    Raises:
        ValueError: If any parameter is invalid.
        RuntimeError: If stream cannot be connected or frame cannot be captured.

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    # Validate inputs
    validated_url = validate_rtsp_url(rtsp_url)
    validated_path = validate_file_path(file_path)
    validated_timeout = validate_timeout(timeout_seconds)

    # Use sanitized URL for error messages to avoid credential exposure
    safe_url = sanitize_url_for_display(validated_url)

    cap = cv2.VideoCapture(validated_url, cv2.CAP_FFMPEG)

    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, validated_timeout * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, validated_timeout * 1000)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"Could not connect to RTSP stream: {safe_url}")

    try:
        for _ in range(5):
            cap.grab()

        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError(f"Failed to capture frame from RTSP stream: {safe_url}")

        cv2.imwrite(validated_path, frame)
        return f"Image saved to {validated_path}"

    finally:
        cap.release()


def check_stream(rtsp_url: str, timeout_seconds: int = 10) -> dict:
    """
    Validates an RTSP stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Args:
        rtsp_url: The RTSP stream URL to validate
        timeout_seconds: Connection timeout in seconds (default: 10, max: 300)

    Returns:
        Dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - url: The sanitized URL (credentials masked)
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code

    Raises:
        ValueError: If any parameter is invalid.
    """
    # Validate inputs
    validated_url = validate_rtsp_url(rtsp_url)
    validated_timeout = validate_timeout(timeout_seconds)

    # Use sanitized URL in responses to avoid credential exposure
    safe_url = sanitize_url_for_display(validated_url)

    cap = cv2.VideoCapture(validated_url, cv2.CAP_FFMPEG)

    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, validated_timeout * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, validated_timeout * 1000)

    if not cap.isOpened():
        return {
            "status": "unavailable",
            "url": safe_url,
            "error": "Could not connect to RTSP stream",
        }

    try:
        ret, _ = cap.read()
        if not ret:
            return {
                "status": "unavailable",
                "url": safe_url,
                "error": "Connected but could not read frame",
            }

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

        return {
            "status": "available",
            "url": safe_url,
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps > 0 else "unknown",
            "codec": codec if codec.strip() else "unknown",
            "backend": cap.getBackendName(),
        }

    finally:
        cap.release()
