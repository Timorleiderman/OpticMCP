"""Tests for the compare module."""

import os
import tempfile

import cv2
import numpy as np
import pytest

from optic_mcp import compare


def create_test_image(width: int = 100, height: int = 100, color: tuple = (128, 128, 128)) -> str:
    """Create a test image and return its path."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


class TestCompare:
    """Core tests for compare module functions."""

    def test_compare_ssim_identical(self):
        """Test SSIM returns 1.0 for identical images."""
        path = create_test_image()
        try:
            result = compare.compare_ssim(path, path)
            assert result["ssim_score"] > 0.99
            assert result["is_similar"] is True
        finally:
            os.unlink(path)

    def test_compare_mse_identical(self):
        """Test MSE returns 0 for identical images."""
        path = create_test_image()
        try:
            result = compare.compare_mse(path, path)
            assert result["mse"] == 0
            assert result["is_identical"] is True
        finally:
            os.unlink(path)

    def test_compare_hash_identical(self):
        """Test hash comparison returns distance 0 for identical images."""
        path = create_test_image()
        try:
            result = compare.compare_hash(path, path)
            assert result["distance"] == 0
            assert result["hash_1"] == result["hash_2"]
        finally:
            os.unlink(path)

    def test_get_hash(self):
        """Test hash generation returns valid hex string."""
        path = create_test_image()
        try:
            result = compare.get_hash(path, "phash")
            assert isinstance(result["hash"], str)
            int(result["hash"], 16)  # Should be valid hex
        finally:
            os.unlink(path)

    def test_image_diff(self):
        """Test image diff creates output file."""
        path = create_test_image()
        output_path = "/tmp/test_diff.png"
        try:
            result = compare.image_diff(path, path, output_path)
            assert result["status"] == "success"
            assert result["diff_percentage"] == 0
            assert os.path.exists(output_path)
        finally:
            os.unlink(path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_compare_histograms(self):
        """Test histogram comparison returns score."""
        path = create_test_image()
        try:
            result = compare.compare_histograms(path, path)
            assert result["is_similar"] is True
            assert "score" in result
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Test FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            compare.compare_ssim("/nonexistent/a.jpg", "/nonexistent/b.jpg")
