"""Tests for RTSP stream functions."""

from unittest.mock import MagicMock, patch
import numpy as np


@patch("optic_mcp.rtsp.cv2")
def test_save_image_success(mock_cv2):
    """Test RTSP save_image saves file successfully."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900

    from optic_mcp.rtsp import save_image

    result = save_image(rtsp_url="rtsp://192.168.1.100:554/stream", file_path="/tmp/test.jpg")
    assert "Image saved to /tmp/test.jpg" in result


@patch("optic_mcp.rtsp.cv2")
def test_check_stream_available(mock_cv2):
    """Test check_stream returns info for available stream."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))
    mock_cap.get.side_effect = lambda prop: {3: 1920, 4: 1080, 5: 30.0, 6: 0}.get(prop, 0)
    mock_cap.getBackendName.return_value = "FFMPEG"
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_FFMPEG = 1900
    mock_cv2.CAP_PROP_FRAME_WIDTH = 3
    mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
    mock_cv2.CAP_PROP_FPS = 5
    mock_cv2.CAP_PROP_FOURCC = 6

    from optic_mcp.rtsp import check_stream

    result = check_stream(rtsp_url="rtsp://192.168.1.100:554/stream")
    assert result["status"] == "available"
    assert result["width"] == 1920
