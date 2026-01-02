"""Tests for image segmentation functionality."""

import os
import tempfile

import cv2
import numpy as np
import pytest

from optic_mcp import segmentation as segmentation


def create_test_image(width: int = 100, height: int = 100, color: tuple = (128, 128, 128)) -> str:
    """Create a test image and return its path."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


def create_gradient_image(width: int = 200, height: int = 200) -> str:
    """Create a gradient test image for better segmentation testing."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(width):
        img[:, i] = [i * 255 // width, 128, 255 - i * 255 // width]
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


class TestSegmentation:
    """Test suite for segmentation functions."""

    def test_validate_input_file_success(self):
        """Test successful file validation."""
        path = create_test_image()
        try:
            result = segmentation._validate_input_file(path)
            assert os.path.isabs(result)
            assert result == os.path.abspath(os.path.expanduser(path))
        finally:
            os.unlink(path)

    def test_validate_input_file_not_found(self):
        """Test file validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            segmentation._validate_input_file("non_existent_file.jpg")

    def test_validate_input_file_invalid_extension(self):
        """Test file validation with invalid file extension."""
        path = create_test_image()
        invalid_path = path.replace(".jpg", ".txt")
        try:
            with pytest.raises(ValueError, match="Invalid image extension"):
                segmentation._validate_input_file(invalid_path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_validate_input_file_empty_string(self):
        """Test file validation with empty string."""
        with pytest.raises(ValueError, match="File path must be a non-empty string"):
            segmentation._validate_input_file("")

    def test_generate_segment_info_valid_segment(self):
        """Test segment info generation for valid segment."""
        mask = np.array([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 0]], dtype=np.uint8)

        result = segmentation._generate_segment_info(mask, 1, mask.shape)

        assert result is not None
        assert result["id"] == 1
        assert result["area"] == 4
        assert result["bounding_box"] == [3, 0, 2, 2]
        assert result["centroid"] == [3, 0]

    def test_generate_segment_info_empty_segment(self):
        """Test segment info generation for empty segment."""
        mask = np.zeros((10, 10), dtype=np.uint8)

        result = segmentation._generate_segment_info(mask, 1, mask.shape)

        assert result is None

    def test_segment_image_threshold_method(self):
        """Test threshold-based segmentation."""
        path = create_gradient_image()
        try:
            result = segmentation.segment_image(path, method="threshold")

            assert result["method"] == "threshold"
            assert isinstance(result["num_segments"], int)
            assert isinstance(result["segments"], list)
            assert result["num_segments"] >= 0

            if result["segments"]:
                segment = result["segments"][0]
                assert "id" in segment
                assert "area" in segment
                assert "bounding_box" in segment
                assert "centroid" in segment
                assert segment["area"] > 0
        finally:
            os.unlink(path)

    def test_segment_image_kmeans_method(self):
        """Test K-means clustering segmentation."""
        path = create_gradient_image()
        try:
            result = segmentation.segment_image(path, method="kmeans", k=3)

            assert result["method"] == "kmeans"
            assert result["k_clusters"] == 3
            assert isinstance(result["num_segments"], int)
            assert isinstance(result["segments"], list)

            if result["segments"]:
                segment = result["segments"][0]
                assert "mean_color" in segment
                assert len(segment["mean_color"]) == 3
        finally:
            os.unlink(path)

    def test_segment_image_watershed_method(self):
        """Test watershed segmentation."""
        path = create_gradient_image()
        try:
            result = segmentation.segment_image(path, method="watershed")

            assert result["method"] == "watershed"
            assert isinstance(result["num_segments"], int)
            assert isinstance(result["segments"], list)
        finally:
            os.unlink(path)

    def test_segment_image_grabcut_method(self):
        """Test GrabCut segmentation."""
        path = create_test_image()
        try:
            result = segmentation.segment_image(path, method="grabcut")

            assert result["method"] == "grabcut"
            assert "initial_rect" in result
            assert isinstance(result["num_segments"], int)
            assert isinstance(result["segments"], list)

            if result["segments"]:
                segment = result["segments"][0]
                assert "mean_color" in segment
        finally:
            os.unlink(path)

    def test_segment_image_invalid_method(self):
        """Test segmentation with invalid method."""
        path = create_test_image()
        try:
            with pytest.raises(ValueError, match="Unsupported segmentation method"):
                segmentation.segment_image(path, method="invalid_method")
        finally:
            os.unlink(path)

    def test_segment_image_corrupted_file(self):
        """Test segmentation with corrupted image file."""
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.write(fd, b"not a valid image")
        os.close(fd)

        try:
            with pytest.raises(ValueError, match="Could not read image"):
                segmentation.segment_image(path)
        finally:
            os.unlink(path)

    def test_segment_image_save(self):
        """Test saving segmented image visualization."""
        input_path = create_gradient_image()
        fd, output_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            result = segmentation.segment_image_save(input_path, output_path, method="threshold")

            assert result["saved"] is True
            assert result["output_path"] == os.path.abspath(output_path)
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
            assert result["method"] == "threshold"
            assert isinstance(result["num_segments"], int)
            assert isinstance(result["segments"], list)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_image_save_kmeans(self):
        """Test saving K-means segmented image."""
        input_path = create_gradient_image()
        fd, output_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            result = segmentation.segment_image_save(input_path, output_path, method="kmeans", k=4)

            assert result["saved"] is True
            assert result["method"] == "kmeans"
            assert os.path.exists(output_path)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_image_save_watershed(self):
        """Test saving watershed segmented image."""
        input_path = create_gradient_image()
        fd, output_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            result = segmentation.segment_image_save(input_path, output_path, method="watershed")

            assert result["saved"] is True
            assert result["method"] == "watershed"
            assert os.path.exists(output_path)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_image_save_grabcut(self):
        """Test saving GrabCut segmented image."""
        input_path = create_test_image()
        fd, output_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            result = segmentation.segment_image_save(input_path, output_path, method="grabcut")

            assert result["saved"] is True
            assert result["method"] == "grabcut"
            assert os.path.exists(output_path)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_segment_image_save_invalid_output_path(self):
        """Test saving to invalid output path."""
        input_path = create_test_image()
        invalid_output_path = "/non/existent/path/output.jpg"

        try:
            with pytest.raises(RuntimeError, match="Failed to save segmented image"):
                segmentation.segment_image_save(input_path, invalid_output_path)
        finally:
            os.unlink(input_path)

    def test_segment_threshold_with_custom_threshold(self):
        """Test threshold segmentation with custom threshold value."""
        path = create_test_image(color=(200, 200, 200))
        try:
            result = segmentation._segment_threshold(cv2.imread(path), threshold_value=150)

            assert result["method"] == "threshold"
            assert isinstance(result["num_segments"], int)
        finally:
            os.unlink(path)

    def test_segment_grabcut_with_custom_rect(self):
        """Test GrabCut segmentation with custom rectangle."""
        path = create_test_image()
        try:
            img = cv2.imread(path)
            height, width = img.shape[:2]
            custom_rect = [50, 50, width - 100, height - 100]

            result = segmentation._segment_grabcut(img, rect=custom_rect)

            assert result["method"] == "grabcut"
            assert result["initial_rect"] == custom_rect
        finally:
            os.unlink(path)

    def test_visualization_functions(self):
        """Test visualization helper functions."""
        path = create_gradient_image()
        try:
            img = cv2.imread(path)

            # Test all visualization methods
            vis_threshold = segmentation._visualize_threshold(img)
            vis_kmeans = segmentation._visualize_kmeans(img, k=3)
            vis_watershed = segmentation._visualize_watershed(img)
            vis_grabcut = segmentation._visualize_grabcut(img)

            # All should return valid images with same dimensions
            for vis_img in [vis_threshold, vis_kmeans, vis_watershed, vis_grabcut]:
                assert vis_img.shape[:2] == img.shape[:2]
                assert vis_img.shape[2] == 3  # Should be BGR
        finally:
            os.unlink(path)


class TestSegmentationEdgeCases:
    """Test edge cases and error handling."""

    def test_small_image_segmentation(self):
        """Test segmentation with very small images."""
        path = create_test_image(width=10, height=10)
        try:
            # Should not crash even with small images
            result = segmentation.segment_image(path, method="threshold")
            assert isinstance(result, dict)
        finally:
            os.unlink(path)

    def test_uniform_image_segmentation(self):
        """Test segmentation with uniform color image."""
        path = create_test_image(width=100, height=100, color=(128, 128, 128))
        try:
            result = segmentation.segment_image(path, method="threshold")
            # Should handle uniform images gracefully
            assert isinstance(result["num_segments"], int)
        finally:
            os.unlink(path)

    def test_grabcut_no_foreground(self):
        """Test GrabCut when no foreground is detected."""
        path = create_test_image(width=50, height=50, color=(255, 255, 255))
        try:
            # Very small uniform white image should result in no segments
            result = segmentation.segment_image(path, method="grabcut")
            assert result["method"] == "grabcut"
            # May have 0 segments if no foreground is found
            assert result["num_segments"] >= 0
        finally:
            os.unlink(path)

    def test_kmeans_with_very_large_k(self):
        """Test K-means with more clusters than image pixels."""
        path = create_test_image(width=10, height=10)  # 100 pixels total
        try:
            result = segmentation.segment_image(path, method="kmeans", k=200)
            # Should not crash, though some clusters may be empty
            assert result["method"] == "kmeans"
            assert result["k_clusters"] == 200
        finally:
            os.unlink(path)
