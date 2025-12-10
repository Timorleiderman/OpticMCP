"""Tests for camera streaming functions."""

from unittest.mock import MagicMock, patch
import numpy as np


@patch("optic_mcp.stream.cv2")
def test_stream_lifecycle(mock_cv2):
    """Test start, list, and stop stream operations."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.grab.return_value = True
    mock_cap.retrieve.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))
    mock_cv2.IMWRITE_JPEG_QUALITY = 1
    mock_cv2.CAP_PROP_BUFFERSIZE = 38

    from optic_mcp.stream import start_stream, stop_stream, list_streams, _manager

    _manager._streams.clear()

    # Start stream
    result = start_stream(camera_index=0, port=18080)
    assert result["status"] == "started"
    assert result["port"] == 18080

    # List streams
    streams = list_streams()
    assert len(streams) == 1
    assert streams[0]["camera_index"] == 0

    # Start again returns already_running
    result = start_stream(camera_index=0, port=18081)
    assert result["status"] == "already_running"

    # Stop stream
    result = stop_stream(camera_index=0)
    assert result["status"] == "stopped"

    # Stop non-existent returns not_running
    result = stop_stream(camera_index=99)
    assert result["status"] == "not_running"
