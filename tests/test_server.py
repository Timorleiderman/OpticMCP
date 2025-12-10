"""Tests for OpticMCP server."""

import base64
import sys
import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestModuleStructure:
    """Tests for module structure and imports."""

    def test_import_module(self):
        """Test that the module can be imported."""
        import optic_mcp
        assert hasattr(optic_mcp, "__version__")
        # Just check it's a valid semver format
        assert optic_mcp.__version__.count(".") == 2

    def test_import_server(self):
        """Test that server module can be imported."""
        from optic_mcp import server
        assert hasattr(server, "main")
        assert hasattr(server, "mcp")

    def test_mcp_server_name(self):
        """Test that MCP server has correct name."""
        from optic_mcp.server import mcp
        assert mcp is not None
        assert mcp.name == "optic-mcp"

    def test_tools_exist(self):
        """Test that expected tools exist."""
        from optic_mcp import server
        assert hasattr(server, "list_cameras")
        assert hasattr(server, "capture_image")
        assert hasattr(server, "save_image")


class TestListCameras:
    """Tests for list_cameras function."""

    @patch('optic_mcp.server.cv2')
    def test_list_cameras_no_cameras(self, mock_cv2):
        """Test list_cameras when no cameras are available."""
        # Configure mock to return closed camera
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import list_cameras
        result = list_cameras()
        assert result == []

    @patch('optic_mcp.server.cv2')
    def test_list_cameras_returns_list(self, mock_cv2):
        """Test list_cameras returns a list."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import list_cameras
        result = list_cameras()
        assert isinstance(result, list)

    @patch('optic_mcp.server.cv2')
    def test_list_cameras_with_available_camera(self, mock_cv2):
        """Test list_cameras when a camera is available."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.getBackendName.return_value = "AVFOUNDATION"
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import list_cameras
        result = list_cameras()
        
        # Should find cameras at all 10 indices since mock always returns opened
        assert len(result) == 10
        assert result[0]["index"] == 0
        assert result[0]["status"] == "available"
        assert result[0]["backend"] == "AVFOUNDATION"


class TestCaptureImage:
    """Tests for capture_image function."""

    @patch('optic_mcp.server.cv2')
    def test_capture_image_camera_not_found(self, mock_cv2):
        """Test capture_image when camera is not available."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import capture_image
        with pytest.raises(RuntimeError, match="Could not open camera"):
            capture_image(camera_index=99)

    @patch('optic_mcp.server.cv2')
    def test_capture_image_returns_string(self, mock_cv2):
        """Test capture_image returns base64 string."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cv2.VideoCapture.return_value = mock_cap
        
        # Mock imencode to return valid JPEG-like bytes
        mock_cv2.imencode.return_value = (True, np.array([255, 216, 255, 0], dtype=np.uint8))
        
        from optic_mcp.server import capture_image
        result = capture_image(camera_index=0)
        
        assert isinstance(result, str)
        # Should be valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    @patch('optic_mcp.server.cv2')
    def test_capture_image_read_fails(self, mock_cv2):
        """Test capture_image when frame read fails."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # First 5 reads succeed (warm-up), then fail
        mock_cap.read.side_effect = [(True, np.zeros((1, 1, 3), dtype=np.uint8))] * 5 + [(False, None)]
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import capture_image
        with pytest.raises(RuntimeError, match="Failed to capture frame"):
            capture_image(camera_index=0)

    @patch('optic_mcp.server.cv2')
    def test_capture_image_releases_camera(self, mock_cv2):
        """Test capture_image releases camera even on success."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))
        
        from optic_mcp.server import capture_image
        capture_image(camera_index=0)
        
        mock_cap.release.assert_called_once()


class TestSaveImage:
    """Tests for save_image function."""

    @patch('optic_mcp.server.cv2')
    def test_save_image_camera_not_found(self, mock_cv2):
        """Test save_image when camera is not available."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import save_image
        with pytest.raises(RuntimeError, match="Could not open camera"):
            save_image(file_path="/tmp/test.jpg", camera_index=99)

    @patch('optic_mcp.server.cv2')
    def test_save_image_success(self, mock_cv2):
        """Test successful image save."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.imwrite.return_value = True
        
        from optic_mcp.server import save_image
        result = save_image(file_path="/tmp/test.jpg", camera_index=0)
        
        assert "Image saved to /tmp/test.jpg" in result
        mock_cv2.imwrite.assert_called_once()

    @patch('optic_mcp.server.cv2')
    def test_save_image_read_fails(self, mock_cv2):
        """Test save_image when frame read fails."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # First 5 reads succeed (warm-up), then fail
        mock_cap.read.side_effect = [(True, np.zeros((1, 1, 3), dtype=np.uint8))] * 5 + [(False, None)]
        mock_cv2.VideoCapture.return_value = mock_cap
        
        from optic_mcp.server import save_image
        with pytest.raises(RuntimeError, match="Failed to capture frame"):
            save_image(file_path="/tmp/test.jpg", camera_index=0)

    @patch('optic_mcp.server.cv2')
    def test_save_image_releases_camera(self, mock_cv2):
        """Test save_image releases camera even on success."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.imwrite.return_value = True
        
        from optic_mcp.server import save_image
        save_image(file_path="/tmp/test.jpg", camera_index=0)
        
        mock_cap.release.assert_called_once()
