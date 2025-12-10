"""Tests for USB camera functions."""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


@patch("optic_mcp.usb.cv2")
def test_list_cameras(mock_cv2):
    """Test list_cameras detects available cameras."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cap.getBackendName.return_value = "AVFOUNDATION"
    mock_cv2.VideoCapture.return_value = mock_cap

    from optic_mcp.usb import list_cameras

    result = list_cameras()
    assert isinstance(result, list)
    assert len(result) == 10
    assert result[0]["status"] == "available"


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
