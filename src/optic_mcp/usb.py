"""USB camera handling module."""

import base64
from typing import List

import cv2


def list_cameras() -> List[dict]:
    """
    Scans for available USB cameras connected to the system.
    Returns a list of available camera indices and their status.
    It attempts to read a frame to ensure the camera is truly available.
    """
    available_cameras = []
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                backend = cap.getBackendName()
                available_cameras.append(
                    {
                        "index": index,
                        "status": "available",
                        "backend": backend,
                        "description": f"Camera {index} ({backend})",
                    }
                )
            cap.release()

    return available_cameras


def capture_image(camera_index: int = 0) -> str:
    """
    Captures a single frame from the specified camera index.
    Returns the image as a base64 encoded JPEG string.
    """
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}")

    try:
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from camera {camera_index}")

        _, buffer = cv2.imencode(".jpg", frame)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")

        return jpg_as_text

    finally:
        cap.release()


def save_image(file_path: str, camera_index: int = 0) -> str:
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.
    """
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}")

    try:
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from camera {camera_index}")

        cv2.imwrite(file_path, frame)
        return f"Image saved to {file_path}"

    finally:
        cap.release()
