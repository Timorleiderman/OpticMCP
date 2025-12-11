"""Image comparison module for OpticMCP.

This module provides functions to compare images for similarity,
differences, and changes. Useful for change detection, duplicate finding,
and visual testing. All operations follow the token-efficient design.
"""

import os
from typing import Dict, Any

import cv2
import numpy as np

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


def _load_and_prepare_images(
    file_path_1: str, file_path_2: str, resize_to_match: bool = True
) -> tuple:
    """
    Load two images and optionally resize to match dimensions.

    Args:
        file_path_1: Path to first image.
        file_path_2: Path to second image.
        resize_to_match: If True, resize second image to match first.

    Returns:
        Tuple of (img1, img2, gray1, gray2) numpy arrays.

    Raises:
        ValueError: If images cannot be loaded.
    """
    path1 = _validate_input_file(file_path_1)
    path2 = _validate_input_file(file_path_2)

    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)

    if img1 is None:
        raise ValueError(f"Failed to load image: {path1}")
    if img2 is None:
        raise ValueError(f"Failed to load image: {path2}")

    # Resize second image to match first if dimensions differ
    if resize_to_match and img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Convert to grayscale for comparison
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    return img1, img2, gray1, gray2


def compare_ssim(file_path_1: str, file_path_2: str, threshold: float = 0.95) -> Dict[str, Any]:
    """
    Compare two images using Structural Similarity Index (SSIM).

    SSIM measures the perceptual similarity between images, considering
    luminance, contrast, and structure. Score ranges from -1 to 1,
    where 1 means identical images.

    This implementation uses a pure OpenCV approach without scikit-image.

    Args:
        file_path_1: Path to the first image.
        file_path_2: Path to the second image.
        threshold: SSIM score above which images are considered similar (default 0.95).

    Returns:
        Dictionary containing:
        - ssim_score: SSIM value between -1 and 1
        - is_similar: True if score >= threshold
        - threshold: The threshold used for comparison

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If the files are not valid images.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")

    _, _, gray1, gray2 = _load_and_prepare_images(file_path_1, file_path_2)

    try:
        # Compute SSIM using OpenCV
        # Constants for SSIM calculation
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        # Convert to float
        img1 = gray1.astype(np.float64)
        img2 = gray2.astype(np.float64)

        # Compute means
        mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)

        mu1_sq = mu1**2
        mu2_sq = mu2**2
        mu1_mu2 = mu1 * mu2

        # Compute variances and covariance
        sigma1_sq = cv2.GaussianBlur(img1**2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2**2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2

        # SSIM formula
        numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)

        ssim_map = numerator / denominator
        ssim_score = float(ssim_map.mean())

        return {
            "ssim_score": round(ssim_score, 6),
            "is_similar": ssim_score >= threshold,
            "threshold": threshold,
        }

    finally:
        del gray1, gray2


def compare_mse(file_path_1: str, file_path_2: str) -> Dict[str, Any]:
    """
    Compare two images using Mean Squared Error (MSE).

    MSE measures the average squared difference between pixel values.
    Lower values indicate more similar images. A value of 0 means
    the images are identical.

    Args:
        file_path_1: Path to the first image.
        file_path_2: Path to the second image.

    Returns:
        Dictionary containing:
        - mse: Mean squared error value (0 = identical)
        - is_identical: True if MSE is 0 (exactly identical images)
        - normalized_mse: MSE normalized to 0-1 range (divided by max possible)

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If the files are not valid images.
    """
    _, _, gray1, gray2 = _load_and_prepare_images(file_path_1, file_path_2)

    try:
        # Calculate MSE
        diff = gray1.astype(np.float64) - gray2.astype(np.float64)
        mse = float((diff**2).mean())

        # Normalize MSE (max possible is 255^2 = 65025)
        normalized_mse = mse / 65025.0

        return {
            "mse": round(mse, 4),
            "is_identical": mse == 0,
            "normalized_mse": round(normalized_mse, 6),
        }

    finally:
        del gray1, gray2


def compare_hash(file_path_1: str, file_path_2: str, hash_type: str = "phash") -> Dict[str, Any]:
    """
    Compare two images using perceptual hashing.

    Perceptual hashing creates a fingerprint of the image that is
    robust to minor changes like resizing, compression, and small edits.
    Lower Hamming distance indicates more similar images.

    Supports three hash types:
    - phash: Perceptual hash using DCT (best for general use)
    - dhash: Difference hash (fast, good for detecting tampering)
    - ahash: Average hash (simple, fast)

    Args:
        file_path_1: Path to the first image.
        file_path_2: Path to the second image.
        hash_type: Type of hash to use ('phash', 'dhash', 'ahash').

    Returns:
        Dictionary containing:
        - hash_1: Hash string of first image
        - hash_2: Hash string of second image
        - distance: Hamming distance between hashes (0 = identical)
        - is_similar: True if distance <= 10 (typical threshold)
        - hash_type: The hash type used

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If the files are not valid images or hash_type invalid.
    """
    valid_hash_types = {"phash", "dhash", "ahash"}
    if hash_type not in valid_hash_types:
        raise ValueError(f"Invalid hash_type: '{hash_type}'. Must be one of {valid_hash_types}")

    path1 = _validate_input_file(file_path_1)
    path2 = _validate_input_file(file_path_2)

    hash1 = get_hash(path1, hash_type)["hash"]
    hash2 = get_hash(path2, hash_type)["hash"]

    # Calculate Hamming distance
    distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    return {
        "hash_1": hash1,
        "hash_2": hash2,
        "distance": distance,
        "is_similar": distance <= 10,
        "hash_type": hash_type,
    }


def get_hash(file_path: str, hash_type: str = "phash") -> Dict[str, Any]:
    """
    Calculate perceptual hash for a single image.

    Generates a compact hash string that represents the image content.
    Images with similar content will have similar hash values.

    Args:
        file_path: Path to the image file.
        hash_type: Type of hash to use ('phash', 'dhash', 'ahash').

    Returns:
        Dictionary containing:
        - hash: The hash string (hexadecimal)
        - hash_type: The hash type used

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If the file is not a valid image or hash_type invalid.
    """
    valid_hash_types = {"phash", "dhash", "ahash"}
    if hash_type not in valid_hash_types:
        raise ValueError(f"Invalid hash_type: '{hash_type}'. Must be one of {valid_hash_types}")

    abs_path = _validate_input_file(file_path)

    img = cv2.imread(abs_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        if hash_type == "ahash":
            # Average hash: resize to 8x8, compare to mean
            resized = cv2.resize(img, (8, 8), interpolation=cv2.INTER_AREA)
            mean_val = resized.mean()
            hash_bits = (resized > mean_val).flatten()

        elif hash_type == "dhash":
            # Difference hash: compare adjacent pixels
            resized = cv2.resize(img, (9, 8), interpolation=cv2.INTER_AREA)
            hash_bits = (resized[:, 1:] > resized[:, :-1]).flatten()

        else:  # phash
            # Perceptual hash using DCT
            resized = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
            resized_float = resized.astype(np.float32)
            dct = cv2.dct(resized_float)
            # Use top-left 8x8 of DCT (low frequencies)
            dct_low = dct[:8, :8]
            # Exclude first coefficient (DC component)
            median = np.median(dct_low.flatten()[1:])
            hash_bits = (dct_low > median).flatten()

        # Convert bits to hex string
        hash_int = 0
        for bit in hash_bits:
            hash_int = (hash_int << 1) | int(bit)

        # Format as hex with leading zeros
        hex_len = len(hash_bits) // 4
        hash_str = format(hash_int, f"0{hex_len}x")

        return {
            "hash": hash_str,
            "hash_type": hash_type,
        }

    finally:
        del img


def image_diff(
    file_path_1: str, file_path_2: str, output_path: str, threshold: int = 30
) -> Dict[str, Any]:
    """
    Create a visual diff highlighting differences between two images.

    Generates an output image where different regions are highlighted.
    Useful for spotting changes between versions of an image.

    Args:
        file_path_1: Path to the first (reference) image.
        file_path_2: Path to the second (comparison) image.
        output_path: Path to save the diff visualization.
        threshold: Pixel difference threshold (0-255, default 30).

    Returns:
        Dictionary containing:
        - status: "success" or error message
        - output_path: Path to the saved diff image
        - diff_percentage: Percentage of pixels that differ
        - diff_pixels: Number of pixels that differ

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If the files are not valid images or output path invalid.
    """
    if not isinstance(threshold, int) or threshold < 0 or threshold > 255:
        raise ValueError("Threshold must be an integer between 0 and 255")

    output_path = validate_file_path(output_path)
    img1, img2, gray1, gray2 = _load_and_prepare_images(file_path_1, file_path_2)

    try:
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)

        # Apply threshold to find significant differences
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # Count differing pixels
        diff_pixels = int(np.count_nonzero(thresh))
        total_pixels = gray1.shape[0] * gray1.shape[1]
        diff_percentage = (diff_pixels / total_pixels) * 100

        # Create visualization
        # Start with the second image
        output = img2.copy()

        # Find contours of different regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw rectangles around different regions
        for contour in contours:
            if cv2.contourArea(contour) > 10:  # Ignore tiny differences
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(output, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Add semi-transparent red overlay on different areas
        mask = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        red_overlay = np.zeros_like(output)
        red_overlay[:, :] = (0, 0, 255)
        red_mask = cv2.bitwise_and(red_overlay, mask)
        output = cv2.addWeighted(output, 1.0, red_mask, 0.3, 0)

        # Save output
        cv2.imwrite(output_path, output)

        return {
            "status": "success",
            "output_path": output_path,
            "diff_percentage": round(diff_percentage, 4),
            "diff_pixels": diff_pixels,
        }

    finally:
        del img1, img2, gray1, gray2


def compare_histograms(
    file_path_1: str, file_path_2: str, method: str = "correlation"
) -> Dict[str, Any]:
    """
    Compare two images by their color histograms.

    Histogram comparison is useful for comparing overall color
    distribution without pixel-by-pixel comparison. Good for
    finding images with similar color schemes.

    Args:
        file_path_1: Path to the first image.
        file_path_2: Path to the second image.
        method: Comparison method ('correlation', 'chi_square', 'intersection', 'bhattacharyya').

    Returns:
        Dictionary containing:
        - score: Comparison score (interpretation depends on method)
        - method: The method used
        - is_similar: True if images have similar histograms

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If the files are not valid images or method invalid.
    """
    valid_methods = {"correlation", "chi_square", "intersection", "bhattacharyya"}
    if method not in valid_methods:
        raise ValueError(f"Invalid method: '{method}'. Must be one of {valid_methods}")

    method_map = {
        "correlation": cv2.HISTCMP_CORREL,
        "chi_square": cv2.HISTCMP_CHISQR,
        "intersection": cv2.HISTCMP_INTERSECT,
        "bhattacharyya": cv2.HISTCMP_BHATTACHARYYA,
    }

    path1 = _validate_input_file(file_path_1)
    path2 = _validate_input_file(file_path_2)

    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)

    if img1 is None:
        raise ValueError(f"Failed to load image: {path1}")
    if img2 is None:
        raise ValueError(f"Failed to load image: {path2}")

    try:
        # Convert to HSV for better histogram comparison
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        # Calculate histograms
        h_bins, s_bins = 50, 60
        hist_size = [h_bins, s_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges
        channels = [0, 1]

        hist1 = cv2.calcHist([hsv1], channels, None, hist_size, ranges)
        hist2 = cv2.calcHist([hsv2], channels, None, hist_size, ranges)

        # Normalize histograms
        cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        # Compare histograms
        score = float(cv2.compareHist(hist1, hist2, method_map[method]))

        # Determine similarity based on method
        if method == "correlation":
            is_similar = score > 0.9  # Higher is more similar, max 1
        elif method == "chi_square":
            is_similar = score < 10  # Lower is more similar
        elif method == "intersection":
            is_similar = score > 0.9  # Higher is more similar
        else:  # bhattacharyya
            is_similar = score < 0.1  # Lower is more similar, 0 = identical

        return {
            "score": round(score, 6),
            "method": method,
            "is_similar": is_similar,
        }

    finally:
        del img1, img2
