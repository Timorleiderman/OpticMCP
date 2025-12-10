"""RTSP stream handling module."""

import base64

import cv2


def capture_image(rtsp_url: str, timeout_seconds: int = 10) -> str:
    """
    Captures a single frame from an RTSP stream URL.
    Returns the image as a base64 encoded JPEG string.

    Args:
        rtsp_url: The RTSP stream URL (e.g., rtsp://username:password@ip:port/path)
        timeout_seconds: Connection timeout in seconds (default: 10)

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_seconds * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_seconds * 1000)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"Could not connect to RTSP stream: {rtsp_url}")

    try:
        for _ in range(5):
            cap.grab()

        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError(f"Failed to capture frame from RTSP stream: {rtsp_url}")

        _, buffer = cv2.imencode(".jpg", frame)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")

        return jpg_as_text

    finally:
        cap.release()


def save_image(rtsp_url: str, file_path: str, timeout_seconds: int = 10) -> str:
    """
    Captures a frame from an RTSP stream and saves it to the given file path.
    Returns a success message with the file path.

    Args:
        rtsp_url: The RTSP stream URL (e.g., rtsp://username:password@ip:port/path)
        file_path: The path where the image will be saved
        timeout_seconds: Connection timeout in seconds (default: 10)

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_seconds * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_seconds * 1000)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        raise RuntimeError(f"Could not connect to RTSP stream: {rtsp_url}")

    try:
        for _ in range(5):
            cap.grab()

        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError(f"Failed to capture frame from RTSP stream: {rtsp_url}")

        cv2.imwrite(file_path, frame)
        return f"Image saved to {file_path}"

    finally:
        cap.release()


def check_stream(rtsp_url: str, timeout_seconds: int = 10) -> dict:
    """
    Validates an RTSP stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Args:
        rtsp_url: The RTSP stream URL to validate
        timeout_seconds: Connection timeout in seconds (default: 10)

    Returns a dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code
    """
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_seconds * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_seconds * 1000)

    if not cap.isOpened():
        return {
            "status": "unavailable",
            "url": rtsp_url,
            "error": "Could not connect to RTSP stream",
        }

    try:
        ret, _ = cap.read()
        if not ret:
            return {
                "status": "unavailable",
                "url": rtsp_url,
                "error": "Connected but could not read frame",
            }

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

        return {
            "status": "available",
            "url": rtsp_url,
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps > 0 else "unknown",
            "codec": codec if codec.strip() else "unknown",
            "backend": cap.getBackendName(),
        }

    finally:
        cap.release()
