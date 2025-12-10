"""Tests for USB camera functions."""

import base64
import pytest
from unittest.mock import MagicMock, patch
import numpy as np


@patch("optic_mcp.usb.cv2")
def test_list_cameras_returns_list(mock_cv2):
    """Test list_cameras returns a list."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap

    from optic_mcp.usb import list_cameras

    result = list_cameras()
    assert isinstance(result, list)


@patch("optic_mcp.usb.cv2")
def test_list_cameras_finds_camera(mock_cv2):
    """Test list_cameras detects available cameras."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cap.getBackendName.return_value = "AVFOUNDATION"
    mock_cv2.VideoCapture.return_value = mock_cap

    from optic_mcp.usb import list_cameras

    result = list_cameras()
    assert len(result) == 10
    assert result[0]["status"] == "available"


@patch("optic_mcp.usb.cv2")
def test_capture_image_returns_base64(mock_cv2):
    """Test capture_image returns base64 string."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))

    from optic_mcp.usb import capture_image

    result = capture_image(camera_index=0)
    assert isinstance(result, str)
    base64.b64decode(result)  # Should not raise


@patch("optic_mcp.usb.cv2")
def test_capture_image_camera_not_found(mock_cv2):
    """Test capture_image raises error when camera not found."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap

    from optic_mcp.usb import capture_image

    with pytest.raises(RuntimeError, match="Could not open camera"):
        capture_image(camera_index=99)


@patch("optic_mcp.usb.cv2")
def test_save_image_success(mock_cv2):
    """Test save_image saves file successfully."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cv2.VideoCapture.return_value = mock_cap

    from optic_mcp.usb import save_image

    result = save_image(file_path="/tmp/test.jpg", camera_index=0)
    assert "Image saved to /tmp/test.jpg" in result
    mock_cv2.imwrite.assert_called_once()
