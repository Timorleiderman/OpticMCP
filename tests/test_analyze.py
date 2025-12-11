"""Tests for the analyze module."""

import os
import tempfile

import cv2
import numpy as np
import pytest

from optic_mcp import analyze


def create_test_image(width: int = 100, height: int = 100, color: tuple = (128, 128, 128)) -> str:
    """Create a test image and return its path."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


class TestAnalyze:
    """Core tests for analyze module functions."""

    def test_get_metadata(self):
        """Test metadata extraction returns expected fields."""
        path = create_test_image(200, 150)
        try:
            result = analyze.get_metadata(path)
            assert result["width"] == 200
            assert result["height"] == 150
            assert result["format"] in ("JPEG", "JPG")
            assert "exif" in result
        finally:
            os.unlink(path)

    def test_get_stats(self):
        """Test stats returns brightness, contrast, sharpness."""
        path = create_test_image(50, 50, (255, 255, 255))  # White image
        try:
            result = analyze.get_stats(path)
            assert result["brightness"] > 0.9  # White = high brightness
            assert "contrast" in result
            assert "sharpness" in result
            assert "is_grayscale" in result
        finally:
            os.unlink(path)

    def test_get_histogram(self):
        """Test histogram returns RGB channels with 256 bins each."""
        path = create_test_image()
        try:
            result = analyze.get_histogram(path)
            assert len(result["channels"]["r"]) == 256
            assert len(result["channels"]["g"]) == 256
            assert len(result["channels"]["b"]) == 256
        finally:
            os.unlink(path)

    def test_get_dominant_colors(self):
        """Test dominant colors extraction."""
        path = create_test_image(50, 50, (255, 0, 0))  # Single color
        try:
            result = analyze.get_dominant_colors(path, num_colors=3)
            assert len(result["colors"]) == 3
            # First color should dominate
            assert result["colors"][0]["percentage"] > 90
            assert "hex" in result["colors"][0]
            assert "rgb" in result["colors"][0]
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Test FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            analyze.get_metadata("/nonexistent/image.jpg")
