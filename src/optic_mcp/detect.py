"""Detection module for OpticMCP.

This module provides functions to detect faces, motion, and edges in images.
Uses OpenCV's built-in detectors (Haar cascades, DNN). No external ML frameworks required.
"""

import os
from typing import Dict, Any, List

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

    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Invalid image extension: '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    return abs_path


def detect_faces(file_path: str, method: str = "haar") -> Dict[str, Any]:
    """
    Detect faces in an image using Haar cascades or DNN.

    Uses OpenCV's pre-trained face detection models. Haar cascades are fast
    but less accurate. DNN method uses a deep learning model for better accuracy.

    Args:
        file_path: Path to the image file.
        method: Detection method - 'haar' (fast) or 'dnn' (accurate).

    Returns:
        Dictionary containing:
        - found: True if faces detected
        - count: Number of faces found
        - faces: List of face dictionaries with x, y, width, height, confidence

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If method is invalid or file is not a valid image.
    """
    valid_methods = {"haar", "dnn"}
    if method not in valid_methods:
        raise ValueError(f"Invalid method: '{method}'. Must be one of {valid_methods}")

    abs_path = _validate_input_file(file_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces: List[Dict[str, Any]] = []

        if method == "haar":
            # Use Haar cascade classifier - alt2 is more accurate for real faces
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)

            # Calculate minimum face size based on image dimensions
            # Minimum 60px, or 5% of smallest dimension
            img_height, img_width = gray.shape[:2]
            min_face_size = max(60, int(min(img_height, img_width) * 0.05))

            detections = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,  # Smaller = more thorough but slower
                minNeighbors=5,  # Balance between false positives and detection
                minSize=(min_face_size, min_face_size),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

            # Convert to list and filter overlapping detections
            detection_list = list(detections) if len(detections) > 0 else []

            # Remove smaller boxes that overlap significantly with larger ones
            filtered = []
            detection_list = sorted(detection_list, key=lambda d: d[2] * d[3], reverse=True)

            for det in detection_list:
                x, y, w, h = det
                is_overlapping = False
                for fx, fy, fw, fh in filtered:
                    # Check if this detection overlaps with an already accepted one
                    overlap_x = max(0, min(x + w, fx + fw) - max(x, fx))
                    overlap_y = max(0, min(y + h, fy + fh) - max(y, fy))
                    overlap_area = overlap_x * overlap_y
                    det_area = w * h
                    if overlap_area > det_area * 0.3:  # 30% overlap threshold
                        is_overlapping = True
                        break
                if not is_overlapping:
                    filtered.append((x, y, w, h))

            for x, y, w, h in filtered:
                faces.append(
                    {
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                    }
                )

        else:  # dnn
            # Use DNN face detector (more accurate but requires model files)
            # Fall back to Haar if DNN models not available
            try:
                model_path = cv2.data.haarcascades + "../dnn/deploy.prototxt"
                weights_path = (
                    cv2.data.haarcascades + "../dnn/res10_300x300_ssd_iter_140000.caffemodel"
                )

                if os.path.exists(model_path) and os.path.exists(weights_path):
                    net = cv2.dnn.readNetFromCaffe(model_path, weights_path)
                    h, w = img.shape[:2]
                    blob = cv2.dnn.blobFromImage(
                        cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
                    )
                    net.setInput(blob)
                    detections = net.forward()

                    for i in range(detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        if confidence > 0.5:
                            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                            (x1, y1, x2, y2) = box.astype("int")
                            faces.append(
                                {
                                    "x": int(x1),
                                    "y": int(y1),
                                    "width": int(x2 - x1),
                                    "height": int(y2 - y1),
                                    "confidence": float(confidence),
                                }
                            )
                else:
                    # Fall back to Haar cascade
                    return detect_faces(file_path, method="haar")
            except Exception:
                # Fall back to Haar cascade on any DNN error
                return detect_faces(file_path, method="haar")

        return {
            "found": len(faces) > 0,
            "count": len(faces),
            "faces": faces,
        }

    finally:
        del img


def detect_faces_save(file_path: str, output_path: str, method: str = "haar") -> Dict[str, Any]:
    """
    Detect faces and save image with bounding boxes drawn.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the annotated output image.
        method: Detection method - 'haar' or 'dnn'.

    Returns:
        Dictionary containing:
        - found: True if faces detected
        - count: Number of faces found
        - output_path: Path to the saved annotated image
        - faces: List of face dictionaries

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If paths are invalid.
    """
    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    # Detect faces first
    result = detect_faces(abs_path, method)

    # Load image and draw boxes
    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        for face in result["faces"]:
            x, y, w, h = face["x"], face["y"], face["width"], face["height"]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add confidence label if available
            if "confidence" in face:
                label = f"{face['confidence']:.2f}"
                cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imwrite(output_path, img)

        return {
            "found": result["found"],
            "count": result["count"],
            "output_path": output_path,
            "faces": result["faces"],
        }

    finally:
        del img


def detect_motion(file_path_1: str, file_path_2: str, threshold: float = 25.0) -> Dict[str, Any]:
    """
    Compare two frames to detect motion between them.

    Uses frame differencing to find areas that changed between two images.
    Useful for motion detection in surveillance or timelapse analysis.

    Args:
        file_path_1: Path to the first (earlier) image.
        file_path_2: Path to the second (later) image.
        threshold: Pixel difference threshold (0-255, default 25).

    Returns:
        Dictionary containing:
        - motion_detected: True if significant motion detected
        - motion_percentage: Percentage of image with motion
        - motion_regions: List of bounding boxes around motion areas
        - changed_pixels: Number of pixels that changed

    Raises:
        FileNotFoundError: If either image file doesn't exist.
        ValueError: If files are invalid or threshold out of range.
    """
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 255:
        raise ValueError("Threshold must be a number between 0 and 255")

    path1 = _validate_input_file(file_path_1)
    path2 = _validate_input_file(file_path_2)

    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)

    if img1 is None:
        raise ValueError(f"Failed to load image: {path1}")
    if img2 is None:
        raise ValueError(f"Failed to load image: {path2}")

    try:
        # Resize second image to match first if needed
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

        # Compute absolute difference
        diff = cv2.absdiff(gray1, gray2)

        # Apply threshold
        _, thresh = cv2.threshold(diff, int(threshold), 255, cv2.THRESH_BINARY)

        # Dilate to fill gaps
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Calculate motion statistics
        total_pixels = gray1.shape[0] * gray1.shape[1]
        changed_pixels = int(np.count_nonzero(thresh))
        motion_percentage = (changed_pixels / total_pixels) * 100

        # Get bounding boxes for motion regions
        motion_regions: List[Dict[str, int]] = []
        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Filter tiny changes
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append(
                    {
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                    }
                )

        return {
            "motion_detected": motion_percentage > 1.0,  # >1% change = motion
            "motion_percentage": round(motion_percentage, 4),
            "motion_regions": motion_regions,
            "changed_pixels": changed_pixels,
        }

    finally:
        del img1, img2


def detect_edges(file_path: str, output_path: str, method: str = "canny") -> Dict[str, Any]:
    """
    Detect edges in an image using various methods.

    Supports Canny, Sobel, and Laplacian edge detection algorithms.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the edge detection output.
        method: Detection method - 'canny', 'sobel', or 'laplacian'.

    Returns:
        Dictionary containing:
        - status: "success" if completed
        - output_path: Path to the saved edge image
        - method: The method used

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If method is invalid or paths are invalid.
    """
    valid_methods = {"canny", "sobel", "laplacian"}
    if method not in valid_methods:
        raise ValueError(f"Invalid method: '{method}'. Must be one of {valid_methods}")

    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if method == "canny":
            edges = cv2.Canny(gray, 50, 150)

        elif method == "sobel":
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = cv2.magnitude(sobelx, sobely)
            edges = np.uint8(np.clip(edges, 0, 255))

        else:  # laplacian
            edges = cv2.Laplacian(gray, cv2.CV_64F)
            edges = np.uint8(np.absolute(edges))

        cv2.imwrite(output_path, edges)

        return {
            "status": "success",
            "output_path": output_path,
            "method": method,
        }

    finally:
        del img


def detect_objects(file_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Detect common objects in an image using OpenCV's DNN module.

    Uses MobileNet SSD for object detection. Can detect 20 common object
    classes including person, car, dog, cat, etc.

    Note: Requires pre-trained model files. Falls back to empty result
    if models are not available.

    Args:
        file_path: Path to the image file.
        confidence_threshold: Minimum confidence for detection (0-1).

    Returns:
        Dictionary containing:
        - found: True if objects detected
        - count: Number of objects found
        - objects: List of object dictionaries with class, confidence, bbox

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If file is invalid or threshold out of range.
    """
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")

    abs_path = _validate_input_file(file_path)

    # COCO class labels
    classes = [
        "background",
        "aeroplane",
        "bicycle",
        "bird",
        "boat",
        "bottle",
        "bus",
        "car",
        "cat",
        "chair",
        "cow",
        "diningtable",
        "dog",
        "horse",
        "motorbike",
        "person",
        "pottedplant",
        "sheep",
        "sofa",
        "train",
        "tvmonitor",
    ]

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        # Try to load MobileNet SSD model
        # These paths are common locations for OpenCV DNN models
        model_paths = [
            (
                cv2.data.haarcascades + "../dnn/MobileNetSSD_deploy.prototxt",
                cv2.data.haarcascades + "../dnn/MobileNetSSD_deploy.caffemodel",
            ),
        ]

        net = None
        for prototxt, caffemodel in model_paths:
            if os.path.exists(prototxt) and os.path.exists(caffemodel):
                net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
                break

        if net is None:
            # Model not available, return empty result
            return {
                "found": False,
                "count": 0,
                "objects": [],
                "note": "Object detection model not installed",
            }

        h, w = img.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
        net.setInput(blob)
        detections = net.forward()

        objects: List[Dict[str, Any]] = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > confidence_threshold:
                class_id = int(detections[0, 0, i, 1])
                if class_id < len(classes):
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x1, y1, x2, y2) = box.astype("int")
                    objects.append(
                        {
                            "class": classes[class_id],
                            "confidence": float(confidence),
                            "x": int(x1),
                            "y": int(y1),
                            "width": int(x2 - x1),
                            "height": int(y2 - y1),
                        }
                    )

        return {
            "found": len(objects) > 0,
            "count": len(objects),
            "objects": objects,
        }

    finally:
        del img


def segment_watershed(file_path: str, output_path: str) -> Dict[str, Any]:
    """
    Perform semantic segmentation using watershed algorithm.

    Watershed segmentation treats grayscale image as a topographic surface
    and floods basins from markers to segment the image.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the segmentation mask.

    Returns:
        Dictionary containing:
        - success: True if segmentation completed
        - output_path: Path to the saved mask
        - method: "watershed"
        - segments_info: Basic statistics about the segmentation

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If paths are invalid.
    """
    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        # Convert to grayscale and apply threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Noise removal
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        # Sure background area
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        # Finding unknown region
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labeling
        _, markers = cv2.connectedComponents(sure_fg)

        # Add one to all labels so that sure background is not 0, but 1
        markers = markers + 1

        # Mark unknown region with zero
        markers[unknown == 255] = 0

        # Apply watershed
        markers = cv2.watershed(img, markers)

        # Create segmentation mask
        mask = np.zeros_like(gray)
        mask[markers > 1] = 255

        # Save mask
        cv2.imwrite(output_path, mask)

        # Calculate statistics
        num_segments = len(np.unique(markers)) - 1  # Subtract background

        return {
            "success": True,
            "output_path": output_path,
            "method": "watershed",
            "segments_info": {"num_segments": num_segments, "mask_shape": list(mask.shape)},
        }

    finally:
        del img


def segment_grabcut(
    file_path: str, output_path: str, rect: List[int] | None = None
) -> Dict[str, Any]:
    """
    Perform semantic segmentation using GrabCut algorithm.

    GrabCut is an interactive image segmentation method that can extract
    foreground objects from the background.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the segmentation mask.
        rect: Bounding box [x, y, width, height] for foreground initialization.
              If None, uses the center region of the image.

    Returns:
        Dictionary containing:
        - success: True if segmentation completed
        - output_path: Path to the saved mask
        - method: "grabcut"
        - segments_info: Basic statistics about the segmentation

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If paths are invalid or rect is malformed.
    """
    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        height, width = img.shape[:2]

        # Default rectangle: center 60% of the image
        if rect is None:
            rect = [
                int(width * 0.2),  # x
                int(height * 0.2),  # y
                int(width * 0.6),  # width
                int(height * 0.6),  # height
            ]
        elif len(rect) != 4:
            raise ValueError("rect must contain exactly 4 integers: [x, y, width, height]")

        # Initialize mask
        mask = np.zeros(img.shape[:2], np.uint8)

        # Background and foreground models
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Apply GrabCut
        cv2.grabCut(img, mask, tuple(rect), bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # Create binary mask where foreground is white
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")

        # Save mask
        cv2.imwrite(output_path, mask2)

        # Calculate statistics
        foreground_pixels = np.count_nonzero(mask2)
        total_pixels = height * width
        foreground_percentage = (foreground_pixels / total_pixels) * 100

        return {
            "success": True,
            "output_path": output_path,
            "method": "grabcut",
            "segments_info": {
                "rect": rect,
                "foreground_pixels": foreground_pixels,
                "foreground_percentage": round(foreground_percentage, 2),
                "mask_shape": list(mask2.shape),
            },
        }

    finally:
        del img


def segment_threshold(file_path: str, output_path: str, method: str = "otsu") -> Dict[str, Any]:
    """
    Perform semantic segmentation using adaptive thresholding techniques.

    Uses thresholding methods to separate foreground from the background based on
    pixel intensity values.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the segmentation mask.
        method: Thresholding method - 'otsu', 'adaptive', or 'binary'.

    Returns:
        Dictionary containing:
        - success: True if segmentation completed
        - output_path: Path to the saved mask
        - method: Thresholding method used
        - segments_info: Basic statistics about the segmentation

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If paths are invalid or method is unsupported.
    """
    valid_methods = {"otsu", "adaptive", "binary"}
    if method not in valid_methods:
        raise ValueError(f"Invalid method: '{method}'. Must be one of {valid_methods}")

    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply thresholding
        if method == "otsu":
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "adaptive":
            mask = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
        else:  # binary
            _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # Save mask
        cv2.imwrite(output_path, mask)

        # Calculate statistics
        foreground_pixels = np.count_nonzero(mask)
        total_pixels = gray.shape[0] * gray.shape[1]
        foreground_percentage = (foreground_pixels / total_pixels) * 100

        return {
            "success": True,
            "output_path": output_path,
            "method": method,
            "segments_info": {
                "foreground_pixels": foreground_pixels,
                "foreground_percentage": round(foreground_percentage, 2),
                "mask_shape": list(mask.shape),
            },
        }

    finally:
        del img


def segment_kmeans(file_path: str, output_path: str, k: int = 4) -> Dict[str, Any]:
    """
    Perform semantic segmentation using K-means clustering.

    Groups similar pixels together based on color similarity to create
    a segmented image.

    Args:
        file_path: Path to the input image file.
        output_path: Path to save the segmentation mask.
        k: Number of clusters (segments) to create.

    Returns:
        Dictionary containing:
        - success: True if segmentation completed
        - output_path: Path to the saved mask
        - method: "kmeans"
        - segments_info: Basic statistics about the segmentation

    Raises:
        FileNotFoundError: If the image file doesn't exist.
        ValueError: If paths are invalid or k is out of range.
    """
    if not isinstance(k, int) or k < 2 or k > 20:
        raise ValueError("k must be an integer between 2 and 20")

    abs_path = _validate_input_file(file_path)
    output_path = validate_file_path(output_path)

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"Failed to load image: {abs_path}")

    try:
        # Reshape image to be a list of pixels
        pixel_values = img.reshape((-1, 3))
        pixel_values = np.float32(pixel_values)

        # Define criteria and apply K-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        # Convert back to 8-bit values
        centers = np.uint8(centers)

        # Create mask based on the largest cluster
        unique_labels, counts = np.unique(labels, return_counts=True)
        largest_cluster = unique_labels[np.argmax(counts)]
        mask = np.where(labels.flatten() == largest_cluster, 255, 0).astype("uint8")
        mask = mask.reshape(img.shape[:2])

        # Save mask
        cv2.imwrite(output_path, mask)

        # Calculate statistics
        segment_sizes = [int(np.sum(labels == i)) for i in range(k)]

        return {
            "success": True,
            "output_path": output_path,
            "method": "kmeans",
            "segments_info": {
                "k": k,
                "cluster_sizes": segment_sizes,
                "dominant_cluster": int(largest_cluster),
                "mask_shape": list(mask.shape),
            },
        }

    finally:
        del img
