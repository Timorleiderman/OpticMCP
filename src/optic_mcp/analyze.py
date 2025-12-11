"""Image analysis module for OpticMCP.

This module provides functions to extract metadata, statistics,
histograms, and dominant colors from images. All operations follow
the token-efficient design - returning only metadata, never raw image data.
"""

import os
from typing import Dict, Any, List, Optional

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

from optic_mcp.validation import validate_file_path, ALLOWED_IMAGE_EXTENSIONS


def _validate_input_file(file_path: str) -> str:
    """
    Validate that an input file exists and is a valid image.

    Args:
        file_path: Path to the image file.

    Returns:
        The validated absolute file path.

    Raises:
        ValueError: If the path is invalid.
        FileNotFoundError: If the file doesn't exist.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    abs_path = os.path.abspath(os.path.expanduser(file_path))

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image file not found: {abs_path}")

    if not os.path.isfile(abs_path):
        raise ValueError(f"Path is not a file: {abs_path}")

    # Check extension
    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Invalid image extension: '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    return abs_path


def get_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from an image file including dimensions, format, and EXIF data.

    Uses PIL/Pillow to read EXIF data and basic image properties.
    EXIF data includes camera settings, GPS coordinates, timestamps, etc.

    Args:
        file_path: Path to the image file.

    Returns:
        Dictionary containing:
        - width: Image width in pixels
        - height: Image height in pixels
        - format: Image format (JPEG, PNG, etc.)
        - mode: Color mode (RGB, RGBA, L, etc.)
        - file_size_bytes: File size in bytes
        - exif: Dictionary of EXIF tags and values (empty if no EXIF)

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If the file is not a valid image.
    """
    abs_path = _validate_input_file(file_path)

    try:
        with Image.open(abs_path) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            mode = img.mode

            # Extract EXIF data
            exif_data: Dict[str, Any] = {}
            try:
                raw_exif = img.getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = TAGS.get(tag_id, str(tag_id))
                        # Convert bytes to string for JSON serialization
                        if isinstance(value, bytes):
                            try:
                                value = value.decode("utf-8", errors="replace")
                            except Exception:
                                value = str(value)
                        # Skip very long values (like MakerNote)
                        if isinstance(value, str) and len(value) > 500:
                            value = f"[{len(value)} chars]"
                        exif_data[tag_name] = value
            except (AttributeError, TypeError):
                # No EXIF data available
                pass

            file_size = os.path.getsize(abs_path)

            return {
                "width": width,
                "height": height,
                "format": img_format,
                "mode": mode,
                "file_size_bytes": file_size,
                "exif": exif_data,
            }

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Failed to read image: {e}")


def get_stats(file_path: str) -> Dict[str, Any]:
    """
    Calculate basic image statistics including brightness, contrast, and sharpness.

    Uses OpenCV to compute statistical measures that describe the image quality.
    All values are normalized to 0-1 range where applicable.

    Args:
        file_path: Path to the image file.

    Returns:
        Dictionary containing:
        - brightness: Average brightness (0-1, where 1 is white)
        - contrast: Standard deviation of pixel values (normalized)
        - sharpness: Laplacian variance (higher = sharper)
        - is_grayscale: Whether the image is grayscale

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If the file is not a valid image.
    """
    abs_path = _validate_input_file(file_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image with OpenCV: {abs_path}")

    try:
        # Check if grayscale
        is_grayscale = len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1)

        if not is_grayscale:
            # Check if all channels are equal (effectively grayscale)
            if len(img.shape) == 3 and img.shape[2] == 3:
                is_grayscale = np.allclose(img[:, :, 0], img[:, :, 1]) and np.allclose(
                    img[:, :, 1], img[:, :, 2]
                )

        # Convert to grayscale for analysis
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Brightness: mean of grayscale values (normalized to 0-1)
        brightness = float(np.mean(gray) / 255.0)

        # Contrast: standard deviation of grayscale values (normalized)
        contrast = float(np.std(gray) / 127.5)  # Max std for uniform distribution is ~127.5

        # Sharpness: Laplacian variance (higher = sharper)
        # Normalized by dividing by a typical max value
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(laplacian.var() / 1000.0)  # Normalize to reasonable range

        return {
            "brightness": round(brightness, 4),
            "contrast": round(min(contrast, 1.0), 4),  # Cap at 1.0
            "sharpness": round(min(sharpness, 10.0), 4),  # Cap at reasonable max
            "is_grayscale": is_grayscale,
        }

    finally:
        del img


def get_histogram(file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate color histogram for an image, optionally saving a visualization.

    Computes histogram for each color channel (R, G, B) with 256 bins each.
    The visualization shows all three channels overlaid on a single plot.

    Args:
        file_path: Path to the image file.
        output_path: Optional path to save histogram visualization.

    Returns:
        Dictionary containing:
        - channels: Dictionary with 'r', 'g', 'b' keys, each containing
                   list of 256 bin values (normalized to 0-1)
        - output_path: Path to saved visualization (if output_path provided)

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If the file is not a valid image or output path invalid.
    """
    abs_path = _validate_input_file(file_path)

    if output_path:
        output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image with OpenCV: {abs_path}")

    try:
        # Calculate histograms for each channel
        hist_b = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
        hist_g = cv2.calcHist([img], [1], None, [256], [0, 256]).flatten()
        hist_r = cv2.calcHist([img], [2], None, [256], [0, 256]).flatten()

        # Normalize to 0-1 range
        total_pixels = img.shape[0] * img.shape[1]
        hist_b_norm = (hist_b / total_pixels).tolist()
        hist_g_norm = (hist_g / total_pixels).tolist()
        hist_r_norm = (hist_r / total_pixels).tolist()

        result: Dict[str, Any] = {
            "channels": {
                "r": [round(v, 6) for v in hist_r_norm],
                "g": [round(v, 6) for v in hist_g_norm],
                "b": [round(v, 6) for v in hist_b_norm],
            }
        }

        # Save visualization if requested
        if output_path:
            # Create histogram visualization using OpenCV
            hist_height = 300
            hist_width = 512
            hist_img = np.zeros((hist_height, hist_width, 3), dtype=np.uint8)

            # Find max value for scaling
            max_val = max(hist_r.max(), hist_g.max(), hist_b.max())
            if max_val == 0:
                max_val = 1

            # Draw histograms
            bin_width = hist_width // 256
            for i in range(256):
                # Blue channel
                h_b = int(hist_b[i] * hist_height / max_val)
                cv2.line(
                    hist_img,
                    (i * bin_width, hist_height),
                    (i * bin_width, hist_height - h_b),
                    (255, 0, 0),
                    1,
                )
                # Green channel
                h_g = int(hist_g[i] * hist_height / max_val)
                cv2.line(
                    hist_img,
                    (i * bin_width, hist_height),
                    (i * bin_width, hist_height - h_g),
                    (0, 255, 0),
                    1,
                )
                # Red channel
                h_r = int(hist_r[i] * hist_height / max_val)
                cv2.line(
                    hist_img,
                    (i * bin_width, hist_height),
                    (i * bin_width, hist_height - h_r),
                    (0, 0, 255),
                    1,
                )

            cv2.imwrite(output_path, hist_img)
            result["output_path"] = output_path

        return result

    finally:
        del img


def get_dominant_colors(file_path: str, num_colors: int = 5) -> Dict[str, Any]:
    """
    Extract dominant colors from an image using K-means clustering.

    Analyzes the image and identifies the most prevalent colors.
    Returns colors sorted by prevalence (most common first).

    Args:
        file_path: Path to the image file.
        num_colors: Number of dominant colors to extract (1-20, default 5).

    Returns:
        Dictionary containing:
        - colors: List of color dictionaries, each with:
            - rgb: [r, g, b] values (0-255)
            - hex: Hex color code (e.g., "#FF5733")
            - percentage: Percentage of image this color represents

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If the file is not a valid image or num_colors invalid.
    """
    abs_path = _validate_input_file(file_path)

    if not isinstance(num_colors, int) or num_colors < 1 or num_colors > 20:
        raise ValueError("num_colors must be an integer between 1 and 20")

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image with OpenCV: {abs_path}")

    try:
        # Convert to RGB (OpenCV loads as BGR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize for faster processing (max 100x100)
        h, w = img_rgb.shape[:2]
        max_dim = 100
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            img_rgb = cv2.resize(img_rgb, new_size, interpolation=cv2.INTER_AREA)

        # Reshape to list of pixels
        pixels = img_rgb.reshape(-1, 3).astype(np.float32)

        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        # Calculate percentage for each color
        label_counts = np.bincount(labels.flatten(), minlength=num_colors)
        total_pixels = len(labels)
        percentages = (label_counts / total_pixels * 100).tolist()

        # Sort by percentage (descending)
        sorted_indices = np.argsort(percentages)[::-1]

        colors: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            r, g, b = [int(c) for c in centers[idx]]
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            colors.append(
                {
                    "rgb": [r, g, b],
                    "hex": hex_color,
                    "percentage": round(percentages[idx], 2),
                }
            )

        return {"colors": colors}

    finally:
        del img
