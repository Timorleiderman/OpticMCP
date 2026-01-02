"""Image segmentation module providing traditional OpenCV-based segmentation methods.

This module implements both semantic and instance segmentation algorithms
using only OpenCV dependencies, following the project's computer vision
infrastructure patterns.
"""

import os
from typing import Dict, Any, List, Tuple, Optional

import cv2
import numpy as np

from optic_mcp.validation import ALLOWED_IMAGE_EXTENSIONS


def _validate_input_file(file_path: str) -> str:
    """Validate that an input file exists and is a valid image."""
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    abs_path = os.path.abspath(os.path.expanduser(file_path))

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image file not found: {abs_path}")

    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Invalid image extension: '{ext}'")

    return abs_path


def _generate_segment_info(
    mask: np.ndarray, segment_id: int, image_shape: Tuple[int, ...]
) -> Dict[str, Any]:
    """Generate segment information including area, bounding box, centroid, and mean color."""
    # Find coordinates of segment pixels
    coords = np.where(mask == segment_id)
    if len(coords[0]) == 0:
        return None

    # Calculate area
    area = len(coords[0])

    # Calculate bounding box
    min_y, max_y = coords[0].min(), coords[0].max()
    min_x, max_x = coords[1].min(), coords[1].max()
    bounding_box = [int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)]

    # Calculate centroid
    centroid = [int(coords[1].mean()), int(coords[0].mean())]

    return {"id": int(segment_id), "area": area, "bounding_box": bounding_box, "centroid": centroid}


def segment_image(file_path: str, method: str = "threshold", **kwargs) -> Dict[str, Any]:
    """
    Segment an image using various traditional OpenCV algorithms.

    Args:
        file_path: Path to the image file
        method: Segmentation method ('threshold', 'kmeans', 'watershed', 'grabcut')
        **kwargs: Method-specific parameters

    Returns:
        Dictionary with segments list containing segment information
    """
    abs_path = _validate_input_file(file_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Could not read image: {abs_path}")

    try:
        if method == "threshold":
            return _segment_threshold(img, **kwargs)
        elif method == "kmeans":
            return _segment_kmeans(img, **kwargs)
        elif method == "watershed":
            return _segment_watershed(img, **kwargs)
        elif method == "grabcut":
            return _segment_grabcut(img, **kwargs)
        else:
            raise ValueError(f"Unsupported segmentation method: {method}")
    finally:
        del img


def _segment_threshold(image: np.ndarray, threshold_value: int = 127, **kwargs) -> Dict[str, Any]:
    """Perform threshold-based segmentation."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Otsu's thresholding if threshold_value is None
    if threshold_value == 127:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

    # Find connected components
    num_labels, labels = cv2.connectedComponents(binary)

    segments = []
    for i in range(1, num_labels):  # Skip background (label 0)
        segment_info = _generate_segment_info(labels, i, image.shape)
        if segment_info and segment_info["area"] > 50:  # Filter small segments
            segments.append(segment_info)

    return {"method": "threshold", "num_segments": len(segments), "segments": segments}


def _segment_kmeans(image: np.ndarray, k: int = 4, **kwargs) -> Dict[str, Any]:
    """Perform K-means clustering-based segmentation."""
    # Reshape image to be a list of pixels
    pixel_values = image.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)

    # Define criteria and apply K-means
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Convert back to uint8 and reshape to original image shape
    centers = np.uint8(centers)
    segmented_image = centers[labels.flatten()]
    segmented_image = segmented_image.reshape(image.shape)

    # Convert to grayscale labels for segment analysis
    labels_2d = labels.reshape(image.shape[:2])

    segments = []
    for i in range(k):
        segment_info = _generate_segment_info(labels_2d, i, image.shape)
        if segment_info and segment_info["area"] > 50:
            # Calculate mean color for this segment
            mask = labels_2d == i
            mean_color = image[mask].mean(axis=0).tolist()
            segment_info["mean_color"] = [int(c) for c in mean_color]
            segments.append(segment_info)

    return {
        "method": "kmeans",
        "num_segments": len(segments),
        "segments": segments,
        "k_clusters": k,
    }


def _segment_watershed(image: np.ndarray, **kwargs) -> Dict[str, Any]:
    """Perform watershed-based segmentation."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Noise removal
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

    # Sure background area
    sure_bg = cv2.dilate(opening, kernel, iterations=3)

    # Finding sure foreground area
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)

    # Finding unknown region
    unknown = cv2.subtract(sure_bg, sure_fg)

    # Marker labelling
    _, markers = cv2.connectedComponents(sure_fg)

    # Add one to all labels so that sure background is not 0, but 1
    markers = markers + 1

    # Mark the unknown region with zero
    markers[unknown == 255] = 0

    # Apply watershed
    markers = cv2.watershed(image, markers)

    # Create segments from watershed markers
    segments = []
    unique_markers = np.unique(markers)
    for marker_id in unique_markers:
        if marker_id <= 1:  # Skip boundary and background
            continue

        segment_info = _generate_segment_info(markers, marker_id, image.shape)
        if segment_info and segment_info["area"] > 50:
            segments.append(segment_info)

    return {"method": "watershed", "num_segments": len(segments), "segments": segments}


def _segment_grabcut(
    image: np.ndarray, rect: Optional[List[int]] = None, **kwargs
) -> Dict[str, Any]:
    """Perform GrabCut-based instance segmentation."""
    height, width = image.shape[:2]

    # If no rectangle provided, use the entire image
    if rect is None:
        rect = [10, 10, width - 20, height - 20]  # [x, y, w, h]

    # Create mask
    mask = np.zeros(image.shape[:2], np.uint8)

    # Create models
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Apply GrabCut
    cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    # Modify mask to create binary mask
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

    # Find contours to identify separate instances
    contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    segments = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 50:  # Filter small contours
            continue

        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate centroid
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w // 2, y + h // 2

        # Calculate mean color
        segment_mask = np.zeros(mask2.shape, dtype=np.uint8)
        cv2.drawContours(segment_mask, [contour], -1, 1, -1)

        mean_color = cv2.mean(image, mask=segment_mask)[:3]  # BGR values

        segments.append(
            {
                "id": i + 1,
                "area": int(area),
                "bounding_box": [x, y, w, h],
                "centroid": [cx, cy],
                "mean_color": [int(c) for c in mean_color],
            }
        )

    return {
        "method": "grabcut",
        "num_segments": len(segments),
        "segments": segments,
        "initial_rect": rect,
    }


def segment_image_save(
    file_path: str, output_path: str, method: str = "threshold", **kwargs
) -> Dict[str, Any]:
    """
    Segment an image and save the visualized result with colored segments.

    Args:
        file_path: Path to the input image file
        output_path: Path to save the segmented visualization
        method: Segmentation method ('threshold', 'kmeans', 'watershed', 'grabcut')
        **kwargs: Method-specific parameters

    Returns:
        Dictionary with save status and segment information
    """
    abs_path = _validate_input_file(file_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Could not read image: {abs_path}")

    try:
        # Perform segmentation
        result = segment_image(file_path, method, **kwargs)

        # Create visualization
        if method == "threshold":
            vis_img = _visualize_threshold(img, **kwargs)
        elif method == "kmeans":
            vis_img = _visualize_kmeans(img, **kwargs)
        elif method == "watershed":
            vis_img = _visualize_watershed(img, **kwargs)
        elif method == "grabcut":
            vis_img = _visualize_grabcut(img, **kwargs)
        else:
            vis_img = img.copy()

        # Save visualization
        output_abs_path = os.path.abspath(os.path.expanduser(output_path))
        success = cv2.imwrite(output_abs_path, vis_img)

        if not success:
            raise RuntimeError(f"Failed to save segmented image to: {output_abs_path}")

        return {
            "saved": True,
            "output_path": output_abs_path,
            "method": method,
            "num_segments": result.get("num_segments", 0),
            "segments": result.get("segments", []),
        }

    finally:
        del img


def _visualize_threshold(image: np.ndarray, **kwargs) -> np.ndarray:
    """Create visualization for threshold segmentation."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    num_labels, labels = cv2.connectedComponents(binary)

    # Create colored visualization
    vis_img = np.zeros_like(image)
    colors = [np.random.randint(0, 255, 3) for _ in range(num_labels)]

    for i in range(1, num_labels):
        mask = labels == i
        if mask.sum() > 50:
            vis_img[mask] = colors[i]

    return cv2.addWeighted(image, 0.5, vis_img, 0.5, 0)


def _visualize_kmeans(image: np.ndarray, k: int = 4, **kwargs) -> np.ndarray:
    """Create visualization for K-means segmentation."""
    pixel_values = image.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    centers = np.uint8(centers)
    segmented_image = centers[labels.flatten()]
    segmented_image = segmented_image.reshape(image.shape)

    return segmented_image


def _visualize_watershed(image: np.ndarray, **kwargs) -> np.ndarray:
    """Create visualization for watershed segmentation."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

    sure_bg = cv2.dilate(opening, kernel, iterations=3)
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)

    unknown = cv2.subtract(sure_bg, sure_fg)
    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0

    markers = cv2.watershed(image, markers)

    vis_img = image.copy()
    vis_img[markers == -1] = [255, 0, 0]  # Mark boundaries in red

    return vis_img


def _visualize_grabcut(image: np.ndarray, rect: Optional[List[int]] = None, **kwargs) -> np.ndarray:
    """Create visualization for GrabCut segmentation."""
    height, width = image.shape[:2]

    if rect is None:
        rect = [10, 10, width - 20, height - 20]

    mask = np.zeros(image.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

    vis_img = image.copy()
    vis_img[mask2 == 1] = [0, 255, 0]  # Mark foreground in green

    # Draw rectangle
    x, y, w, h = rect
    cv2.rectangle(vis_img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return vis_img
