"""USB camera handling module."""

from typing import List

import cv2

from optic_mcp.validation import validate_file_path, validate_camera_index


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


def save_image(file_path: str, camera_index: int = 0) -> str:
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.

    Args:
        file_path: Path where the image will be saved. Must be in an allowed directory
                   and have a valid image extension (.jpg, .png, etc.)
        camera_index: The camera index to capture from (0-100).

    Returns:
        Success message with file path.

    Raises:
        ValueError: If file_path or camera_index is invalid.
        RuntimeError: If camera cannot be opened or frame cannot be captured.
    """
    # Validate inputs
    validated_path = validate_file_path(file_path)
    validated_index = validate_camera_index(camera_index)

    cap = cv2.VideoCapture(validated_index)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {validated_index}")

    try:
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from camera {validated_index}")

        cv2.imwrite(validated_path, frame)
        return f"Image saved to {validated_path}"

    finally:
        cap.release()
