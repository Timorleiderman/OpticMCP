"""Tests for validation module."""

import os
import pytest
from unittest.mock import patch


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_path_in_tmp(self):
        """Test valid path in /tmp directory."""
        from optic_mcp.validation import validate_file_path

        result = validate_file_path("/tmp/test.jpg", check_parent_exists=False)
        assert result == "/tmp/test.jpg"

    def test_valid_path_with_png_extension(self):
        """Test valid path with PNG extension."""
        from optic_mcp.validation import validate_file_path

        result = validate_file_path("/tmp/test.png", check_parent_exists=False)
        assert result == "/tmp/test.png"

    def test_rejects_path_traversal(self):
        """Test that path traversal is rejected."""
        from optic_mcp.validation import validate_file_path

        with pytest.raises(ValueError, match="Path traversal"):
            validate_file_path("/tmp/../etc/passwd.jpg", check_parent_exists=False)

    def test_rejects_invalid_extension(self):
        """Test that invalid extensions are rejected."""
        from optic_mcp.validation import validate_file_path

        with pytest.raises(ValueError, match="Invalid file extension"):
            validate_file_path("/tmp/test.exe", check_parent_exists=False)

    def test_rejects_empty_path(self):
        """Test that empty path is rejected."""
        from optic_mcp.validation import validate_file_path

        with pytest.raises(ValueError, match="non-empty string"):
            validate_file_path("", check_parent_exists=False)

    def test_rejects_none_path(self):
        """Test that None path is rejected."""
        from optic_mcp.validation import validate_file_path

        with pytest.raises(ValueError, match="non-empty string"):
            validate_file_path(None, check_parent_exists=False)

    def test_allows_custom_extensions(self):
        """Test custom extension whitelist."""
        from optic_mcp.validation import validate_file_path

        result = validate_file_path(
            "/tmp/test.mp4", allowed_extensions={".mp4", ".avi"}, check_parent_exists=False
        )
        assert result == "/tmp/test.mp4"

    def test_rejects_path_outside_allowed_dirs(self):
        """Test that paths outside allowed directories are rejected."""
        from optic_mcp.validation import validate_file_path

        with pytest.raises(ValueError, match="not in allowed directories"):
            validate_file_path("/etc/test.jpg", check_parent_exists=False)


class TestValidateCameraIndex:
    """Tests for validate_camera_index function."""

    def test_valid_index_zero(self):
        """Test valid camera index 0."""
        from optic_mcp.validation import validate_camera_index

        assert validate_camera_index(0) == 0

    def test_valid_index_positive(self):
        """Test valid positive camera index."""
        from optic_mcp.validation import validate_camera_index

        assert validate_camera_index(5) == 5

    def test_rejects_negative_index(self):
        """Test that negative index is rejected."""
        from optic_mcp.validation import validate_camera_index

        with pytest.raises(ValueError, match="non-negative"):
            validate_camera_index(-1)

    def test_rejects_too_large_index(self):
        """Test that index over 100 is rejected."""
        from optic_mcp.validation import validate_camera_index

        with pytest.raises(ValueError, match="<= 100"):
            validate_camera_index(101)

    def test_rejects_non_integer(self):
        """Test that non-integer is rejected."""
        from optic_mcp.validation import validate_camera_index

        with pytest.raises(ValueError, match="must be an integer"):
            validate_camera_index("0")


class TestValidatePort:
    """Tests for validate_port function."""

    def test_valid_port(self):
        """Test valid port number."""
        from optic_mcp.validation import validate_port

        assert validate_port(8080) == 8080

    def test_valid_port_minimum(self):
        """Test minimum valid port (1024)."""
        from optic_mcp.validation import validate_port

        assert validate_port(1024) == 1024

    def test_valid_port_maximum(self):
        """Test maximum valid port (65535)."""
        from optic_mcp.validation import validate_port

        assert validate_port(65535) == 65535

    def test_rejects_privileged_port(self):
        """Test that privileged ports are rejected."""
        from optic_mcp.validation import validate_port

        with pytest.raises(ValueError, match="non-privileged"):
            validate_port(80)

    def test_rejects_port_too_high(self):
        """Test that ports over 65535 are rejected."""
        from optic_mcp.validation import validate_port

        with pytest.raises(ValueError, match="<= 65535"):
            validate_port(99999)

    def test_rejects_non_integer(self):
        """Test that non-integer is rejected."""
        from optic_mcp.validation import validate_port

        with pytest.raises(ValueError, match="must be an integer"):
            validate_port("8080")


class TestValidateTimeout:
    """Tests for validate_timeout function."""

    def test_valid_timeout(self):
        """Test valid timeout value."""
        from optic_mcp.validation import validate_timeout

        assert validate_timeout(30) == 30

    def test_valid_timeout_minimum(self):
        """Test minimum valid timeout (1 second)."""
        from optic_mcp.validation import validate_timeout

        assert validate_timeout(1) == 1

    def test_rejects_zero_timeout(self):
        """Test that zero timeout is rejected."""
        from optic_mcp.validation import validate_timeout

        with pytest.raises(ValueError, match="at least 1 second"):
            validate_timeout(0)

    def test_rejects_negative_timeout(self):
        """Test that negative timeout is rejected."""
        from optic_mcp.validation import validate_timeout

        with pytest.raises(ValueError, match="at least 1 second"):
            validate_timeout(-5)

    def test_rejects_too_large_timeout(self):
        """Test that timeout over max is rejected."""
        from optic_mcp.validation import validate_timeout

        with pytest.raises(ValueError, match="<= 300"):
            validate_timeout(500)

    def test_custom_max_timeout(self):
        """Test custom max timeout."""
        from optic_mcp.validation import validate_timeout

        assert validate_timeout(50, max_timeout=100) == 50

        with pytest.raises(ValueError, match="<= 60"):
            validate_timeout(100, max_timeout=60)


class TestSanitizeUrlForDisplay:
    """Tests for sanitize_url_for_display function."""

    def test_url_without_credentials(self):
        """Test URL without credentials is unchanged."""
        from optic_mcp.validation import sanitize_url_for_display

        url = "rtsp://192.168.1.100:554/stream"
        assert sanitize_url_for_display(url) == url

    def test_url_with_credentials(self):
        """Test URL with credentials is sanitized."""
        from optic_mcp.validation import sanitize_url_for_display

        url = "rtsp://admin:password123@192.168.1.100:554/stream"
        result = sanitize_url_for_display(url)
        assert "admin" not in result
        assert "password123" not in result
        assert "***:***@" in result
        assert "192.168.1.100:554/stream" in result

    def test_http_url_with_credentials(self):
        """Test HTTP URL with credentials is sanitized."""
        from optic_mcp.validation import sanitize_url_for_display

        url = "http://user:secret@example.com/video.mjpg"
        result = sanitize_url_for_display(url)
        assert "user" not in result
        assert "secret" not in result
        assert "***:***@" in result

    def test_none_url(self):
        """Test None URL returns None."""
        from optic_mcp.validation import sanitize_url_for_display

        assert sanitize_url_for_display(None) is None

    def test_empty_url(self):
        """Test empty URL returns empty."""
        from optic_mcp.validation import sanitize_url_for_display

        assert sanitize_url_for_display("") == ""


class TestValidateStreamUrl:
    """Tests for validate_stream_url and related functions."""

    def test_valid_rtsp_url(self):
        """Test valid RTSP URL."""
        from optic_mcp.validation import validate_rtsp_url

        url = "rtsp://192.168.1.100:554/stream"
        assert validate_rtsp_url(url) == url

    def test_valid_rtsps_url(self):
        """Test valid RTSPS URL."""
        from optic_mcp.validation import validate_rtsp_url

        url = "rtsps://192.168.1.100:554/stream"
        assert validate_rtsp_url(url) == url

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        from optic_mcp.validation import validate_http_url

        url = "http://example.com/stream.m3u8"
        assert validate_http_url(url) == url

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        from optic_mcp.validation import validate_http_url

        url = "https://example.com/stream.m3u8"
        assert validate_http_url(url) == url

    def test_rejects_invalid_scheme(self):
        """Test that invalid scheme is rejected."""
        from optic_mcp.validation import validate_rtsp_url

        with pytest.raises(ValueError, match="not allowed"):
            validate_rtsp_url("http://example.com/stream")

    def test_rejects_missing_scheme(self):
        """Test that missing scheme is rejected."""
        from optic_mcp.validation import validate_stream_url

        # URL without scheme should be rejected (error message may vary by Python version)
        with pytest.raises(ValueError):
            validate_stream_url("192.168.1.100:554/stream")

    def test_rejects_missing_hostname(self):
        """Test that missing hostname is rejected."""
        from optic_mcp.validation import validate_stream_url

        with pytest.raises(ValueError, match="must include a hostname"):
            validate_stream_url("rtsp:///stream")

    def test_rejects_empty_url(self):
        """Test that empty URL is rejected."""
        from optic_mcp.validation import validate_stream_url

        with pytest.raises(ValueError, match="non-empty string"):
            validate_stream_url("")
