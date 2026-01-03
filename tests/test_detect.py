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

    def test_segment_watershed(self):
        """Test segment_watershed creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_watershed.png"
        try:
            result = detect.segment_watershed(path, output_path)
            assert result["success"] is True
            assert result["method"] == "watershed"
            assert os.path.exists(output_path)
            assert "segments_info" in result
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_grabcut(self):
        """Test segment_grabcut creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_grabcut.png"
        try:
            result = detect.segment_grabcut(path, output_path)
            assert result["success"] is True
            assert result["method"] == "grabcut"
            assert os.path.exists(output_path)
            assert "segments_info" in result
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_grabcut_with_rect(self):
        """Test segment_grabcut with custom rectangle."""
        path = create_test_image()
        output_path = "/tmp/test_grabcut_rect.png"
        try:
            rect = [10, 10, 50, 50]
            result = detect.segment_grabcut(path, output_path, rect)
            assert result["success"] is True
            assert result["segments_info"]["rect"] == rect
            assert os.path.exists(output_path)
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_threshold(self):
        """Test segment_threshold creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_threshold.png"
        try:
            result = detect.segment_threshold(path, output_path, method="otsu")
            assert result["success"] is True
            assert result["method"] == "otsu"
            assert os.path.exists(output_path)
            assert "segments_info" in result
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_threshold_invalid_method(self):
        """Test segment_threshold raises on invalid method."""
        path = create_test_image()
        try:
            with pytest.raises(ValueError, match="Invalid method"):
                detect.segment_threshold(path, "/tmp/out.png", method="invalid")
        finally:
            os.unlink(path)

    def test_segment_kmeans(self):
        """Test segment_kmeans creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_kmeans.png"
        try:
            result = detect.segment_kmeans(path, output_path, k=3)
            assert result["success"] is True
            assert result["method"] == "kmeans"
            assert result["segments_info"]["k"] == 3
            assert os.path.exists(output_path)
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_kmeans_invalid_k(self):
        """Test segment_kmeans raises on invalid k value."""
        path = create_test_image()
        try:
            with pytest.raises(ValueError, match="k must be an integer"):
                detect.segment_kmeans(path, "/tmp/out.png", k=1)
        finally:
            os.unlink(path)
