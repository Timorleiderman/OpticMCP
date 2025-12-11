"""Tests for the detect module."""

import os
import tempfile

import cv2
import numpy as np
import pytest

from optic_mcp import detect


def create_test_image(width: int = 100, height: int = 100, color: tuple = (128, 128, 128)) -> str:
    """Create a test image and return its path."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


def create_diff_image(width: int = 100, height: int = 100) -> str:
    """Create a different test image for motion detection."""
    img = np.full((height, width, 3), (200, 200, 200), dtype=np.uint8)
    # Add a distinct shape
    cv2.rectangle(img, (20, 20), (80, 80), (50, 50, 50), -1)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


class TestDetect:
    """Core tests for detect module functions."""

    def test_detect_faces_returns_structure(self):
        """Test detect_faces returns correct structure."""
        path = create_test_image()
        try:
            result = detect.detect_faces(path)
            assert "found" in result
            assert "count" in result
            assert "faces" in result
            assert isinstance(result["faces"], list)
        finally:
            os.unlink(path)

    def test_detect_faces_invalid_method(self):
        """Test detect_faces raises on invalid method."""
        path = create_test_image()
        try:
            with pytest.raises(ValueError, match="Invalid method"):
                detect.detect_faces(path, method="invalid")
        finally:
            os.unlink(path)

    def test_detect_faces_save(self):
        """Test detect_faces_save creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_faces.png"
        try:
            result = detect.detect_faces_save(path, output_path)
            assert "found" in result
            assert "output_path" in result
            assert os.path.exists(output_path)
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_detect_motion(self):
        """Test detect_motion detects changes between images."""
        path1 = create_test_image()
        path2 = create_diff_image()
        try:
            result = detect.detect_motion(path1, path2)
            assert "motion_detected" in result
            assert "motion_percentage" in result
            assert "changed_pixels" in result
            assert isinstance(result["motion_regions"], list)
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_detect_edges(self):
        """Test detect_edges creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_edges.png"
        try:
            result = detect.detect_edges(path, output_path, method="canny")
            assert result["status"] == "success"
            assert result["method"] == "canny"
            assert os.path.exists(output_path)
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_detect_edges_invalid_method(self):
        """Test detect_edges raises on invalid method."""
        path = create_test_image()
        try:
            with pytest.raises(ValueError, match="Invalid method"):
                detect.detect_edges(path, "/tmp/out.png", method="invalid")
        finally:
            os.unlink(path)

    def test_detect_objects_returns_structure(self):
        """Test detect_objects returns correct structure."""
        path = create_test_image()
        try:
            result = detect.detect_objects(path)
            assert "found" in result
            assert "count" in result
            assert "objects" in result
            assert isinstance(result["objects"], list)
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Test FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            detect.detect_faces("/nonexistent/image.jpg")
