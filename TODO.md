# OpticMCP - Comprehensive Implementation Plan

## Overview

This document outlines the complete implementation plan for OpticMCP - a comprehensive
MCP server for camera, vision, and image processing tools. All implementations follow
the **token-efficient design** - saving images to files and returning only metadata
(never raw image data).

## Design Principles

1. **File-based output** - All capture/processing functions save to file path, return metadata only
2. **Consistent API** - Each module provides predictable function signatures
3. **Minimal dependencies** - Heavy deps are optional extras
4. **OpenCV stderr suppression** - All modules must be imported after stderr suppression in server.py
5. **JSON-serializable responses** - All returns must be JSON-serializable (lists as arrays, not tuples)

---

# Part A: Camera Protocols & Sources

## Phase A1: Quick Wins (Low Complexity)

### A1.1 MJPEG/HTTP Capture Module

**File:** `src/optic_mcp/mjpeg.py`

**Description:** Capture frames from HTTP MJPEG streams. Common in basic IP cameras,
ESP32-CAM, Arduino cameras, and legacy surveillance systems.

**Dependencies:** `requests>=2.28.0` (add to main dependencies)

**Tools to implement:**

- [ ] `mjpeg_save_image(mjpeg_url: str, file_path: str, timeout_seconds: int = 10) -> dict`
  - Connects to MJPEG stream over HTTP
  - Parses multipart MIME boundary to extract first complete JPEG frame
  - Saves frame to file_path
  - Returns: `{"status": "success", "file_path": str, "size_bytes": int}`

- [ ] `mjpeg_check_stream(mjpeg_url: str, timeout_seconds: int = 10) -> dict`
  - Validates MJPEG stream is accessible
  - Returns: `{"status": "available"|"unavailable", "url": str, "content_type": str, "error"?: str}`

**URL formats to support:**
```
http://camera/video.mjpg
http://192.168.1.100:8080/mjpg/video.mjpg
http://camera:8080/?action=stream
http://user:pass@camera/video.mjpeg
```

**Test file:** `tests/test_mjpeg.py`

- [ ] Test successful frame capture (mocked)
- [ ] Test stream check available (mocked)
- [ ] Test stream check unavailable (mocked)
- [ ] Test timeout handling
- [ ] Test authentication in URL

---

### A1.2 Screen Capture Module

**File:** `src/optic_mcp/screen.py`

**Description:** Capture screenshots of desktop monitors or specific screen regions.
Useful for monitoring applications, dashboards, or remote desktop scenarios.

**Dependencies:** `mss>=9.0.0` (add to main dependencies)

**Tools to implement:**

- [ ] `screen_list_monitors() -> list[dict]`
  - Lists all available monitors/displays
  - Returns: `[{"id": int, "left": int, "top": int, "width": int, "height": int, "primary": bool}]`

- [ ] `screen_save_image(file_path: str, monitor: int = 0) -> dict`
  - Captures full screenshot of specified monitor (0 = all monitors, 1+ = specific monitor)
  - Saves to file_path as PNG or JPEG (based on extension)
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int, "monitor": int}`

- [ ] `screen_save_region(file_path: str, x: int, y: int, width: int, height: int) -> dict`
  - Captures specific region of screen
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int, "region": dict}`

**Test file:** `tests/test_screen.py`

- [ ] Test list monitors (mocked)
- [ ] Test full screen capture (mocked)
- [ ] Test region capture (mocked)
- [ ] Test invalid monitor index handling
- [ ] Test invalid region handling

---

### A1.3 HTTP Image Fetch Module

**File:** `src/optic_mcp/http_image.py`

**Description:** Download and save images from any HTTP/HTTPS URL.
Useful for fetching images from web APIs, static URLs, or snapshot endpoints.

**Dependencies:** `requests>=2.28.0` (shared with MJPEG)

**Tools to implement:**

- [ ] `http_save_image(url: str, file_path: str, timeout_seconds: int = 30) -> dict`
  - Downloads image from URL (supports redirects, basic auth in URL)
  - Auto-detects format from Content-Type or URL extension
  - Returns: `{"status": "success", "file_path": str, "size_bytes": int, "content_type": str}`

- [ ] `http_check_image(url: str, timeout_seconds: int = 10) -> dict`
  - HEAD request to validate image URL
  - Returns: `{"status": "available"|"unavailable", "url": str, "content_type": str, "size_bytes": int}`

**Test file:** `tests/test_http_image.py`

- [ ] Test successful download (mocked)
- [ ] Test various image formats
- [ ] Test redirect handling
- [ ] Test 404 handling
- [ ] Test timeout handling

---

## Phase A2: Medium Complexity

### A2.1 ONVIF Module

**File:** `src/optic_mcp/onvif_cam.py`

**Description:** Discover and interact with ONVIF-compliant IP cameras.
ONVIF is the industry standard for IP surveillance cameras.

**Dependencies:** (optional extra `[onvif]`)
- `onvif-zeep>=0.4.0`
- `WSDiscovery>=2.0.0`

**Tools to implement:**

- [ ] `onvif_discover(timeout_seconds: int = 5) -> list[dict]`
  - Uses WS-Discovery to find ONVIF cameras on local network
  - Returns: `[{"name": str, "host": str, "port": int, "hardware": str, "location": str}]`

- [ ] `onvif_get_device_info(host: str, port: int, username: str, password: str) -> dict`
  - Retrieves device information from ONVIF camera
  - Returns: `{"manufacturer": str, "model": str, "firmware": str, "serial": str, "hardware_id": str}`

- [ ] `onvif_get_stream_uri(host: str, port: int, username: str, password: str, profile: int = 0) -> dict`
  - Gets RTSP stream URI from camera profile
  - Returns: `{"stream_uri": str, "profile_name": str, "encoding": str, "resolution": dict}`

- [ ] `onvif_get_snapshot_uri(host: str, port: int, username: str, password: str, profile: int = 0) -> dict`
  - Gets HTTP snapshot URI from camera profile
  - Returns: `{"snapshot_uri": str, "profile_name": str}`

- [ ] `onvif_save_image(host: str, port: int, username: str, password: str, file_path: str, profile: int = 0) -> dict`
  - Captures image via ONVIF snapshot URI
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int}`

- [ ] `onvif_list_profiles(host: str, port: int, username: str, password: str) -> list[dict]`
  - Lists available media profiles on camera
  - Returns: `[{"index": int, "name": str, "token": str, "encoding": str, "resolution": dict}]`

**Optional PTZ tools (lower priority):**

- [ ] `onvif_ptz_move(host, port, user, pass, pan: float, tilt: float, zoom: float) -> dict`
- [ ] `onvif_ptz_stop(host, port, user, pass) -> dict`
- [ ] `onvif_ptz_goto_preset(host, port, user, pass, preset: int) -> dict`
- [ ] `onvif_ptz_get_presets(host, port, user, pass) -> list[dict]`

**Test file:** `tests/test_onvif_cam.py`

- [ ] Test discovery (mocked WS-Discovery)
- [ ] Test get device info (mocked ONVIF client)
- [ ] Test get stream URI (mocked)
- [ ] Test save image (mocked)
- [ ] Test authentication failure handling
- [ ] Test connection timeout handling

---

### A2.2 NDI Module (Optional)

**File:** `src/optic_mcp/ndi.py`

**Description:** Capture from NDI (Network Device Interface) streams.
Used in professional video production and broadcasting.

**Dependencies:** (optional extra `[ndi]`)
- `ndi-python>=5.0.0`
- Requires NDI SDK installed on system

**Tools to implement:**

- [ ] `ndi_list_sources(timeout_seconds: int = 5) -> list[dict]`
  - Discovers NDI sources on network
  - Returns: `[{"name": str, "url": str, "ip": str}]`

- [ ] `ndi_save_image(source_name: str, file_path: str, timeout_seconds: int = 10) -> dict`
  - Captures frame from NDI source
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int, "source": str}`

- [ ] `ndi_check_source(source_name: str, timeout_seconds: int = 10) -> dict`
  - Validates NDI source availability
  - Returns: `{"status": "available"|"unavailable", "source": str, "frame_rate": float, "resolution": dict}`

**Test file:** `tests/test_ndi.py`

- [ ] Test source discovery (mocked)
- [ ] Test frame capture (mocked)
- [ ] Test source not found handling

---

## Phase A3: High Complexity

### A3.1 WebRTC Module

**File:** `src/optic_mcp/webrtc.py`

**Description:** Capture frames from WebRTC streams. Modern protocol used by
browser-based cameras and surveillance systems.

**Dependencies:** (optional extra `[webrtc]`)
- `aiortc>=1.6.0`
- `aiohttp>=3.8.0`

**Tools to implement:**

- [ ] `webrtc_save_image(whep_url: str, file_path: str, timeout_seconds: int = 30) -> dict`
  - Connects to WHEP endpoint, negotiates WebRTC connection
  - Captures single frame from video track
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int}`

- [ ] `webrtc_check_stream(whep_url: str, timeout_seconds: int = 30) -> dict`
  - Tests WHEP endpoint availability
  - Returns: `{"status": "available"|"unavailable", "url": str, "error"?: str}`

**Test file:** `tests/test_webrtc.py`

- [ ] Test WHEP connection (mocked)
- [ ] Test frame capture (mocked)
- [ ] Test connection failure handling
- [ ] Test timeout handling

---

### A3.2 GStreamer Module (Optional)

**File:** `src/optic_mcp/gstreamer.py`

**Description:** Universal video capture via GStreamer pipelines.
Supports virtually any video source GStreamer can handle.

**Dependencies:** (optional extra `[gstreamer]`)
- `PyGObject>=3.42.0`
- GStreamer runtime installed on system

**Tools to implement:**

- [ ] `gst_save_image(pipeline: str, file_path: str, timeout_seconds: int = 10) -> dict`
  - Executes GStreamer pipeline, captures frame from sink
  - Returns: `{"status": "success", "file_path": str, "width": int, "height": int}`

- [ ] `gst_check_pipeline(pipeline: str, timeout_seconds: int = 10) -> dict`
  - Validates GStreamer pipeline can be constructed and run
  - Returns: `{"status": "valid"|"invalid", "pipeline": str, "error"?: str}`

**Test file:** `tests/test_gstreamer.py`

- [ ] Test valid pipeline (mocked)
- [ ] Test frame capture (mocked)
- [ ] Test invalid pipeline handling

---

# Part B: Image Analysis & Detection

## Phase B1: Basic Analysis (Low Complexity)

### B1.1 Image Metadata Module

**File:** `src/optic_mcp/analyze.py`

**Description:** Extract metadata and basic properties from images without
heavy processing. Uses PIL/Pillow for EXIF and OpenCV for image stats.

**Dependencies:** `Pillow>=10.0.0` (add to main dependencies)

**Tools to implement:**

- [ ] `image_get_metadata(file_path: str) -> dict`
  - Extracts EXIF data, dimensions, format, color mode
  - Returns: `{"width": int, "height": int, "format": str, "mode": str, "exif": dict, "file_size_bytes": int}`

- [ ] `image_get_stats(file_path: str) -> dict`
  - Calculates basic image statistics (brightness, contrast, sharpness estimate)
  - Returns: `{"brightness": float, "contrast": float, "sharpness": float, "is_grayscale": bool}`

- [ ] `image_get_histogram(file_path: str, output_path: str = None) -> dict`
  - Calculates color histogram, optionally saves visualization
  - Returns: `{"channels": {"r": list, "g": list, "b": list}, "output_path"?: str}`

- [ ] `image_get_dominant_colors(file_path: str, num_colors: int = 5) -> dict`
  - K-means clustering to find dominant colors
  - Returns: `{"colors": [{"rgb": [r,g,b], "hex": str, "percentage": float}]}`

**Test file:** `tests/test_analyze.py`

- [ ] Test metadata extraction
- [ ] Test stats calculation
- [ ] Test histogram generation
- [ ] Test dominant colors
- [ ] Test invalid file handling

---

### B1.2 Image Comparison Module

**File:** `src/optic_mcp/compare.py`

**Description:** Compare images for similarity, differences, and changes.
Useful for change detection, duplicate finding, and visual testing.

**Dependencies:** OpenCV (existing), `scikit-image>=0.21.0` (optional, for SSIM)

**Tools to implement:**

- [ ] `image_compare_ssim(file_path_1: str, file_path_2: str) -> dict`
  - Structural Similarity Index (SSIM) comparison
  - Returns: `{"ssim_score": float, "is_similar": bool, "threshold": float}`

- [ ] `image_compare_mse(file_path_1: str, file_path_2: str) -> dict`
  - Mean Squared Error comparison
  - Returns: `{"mse": float, "is_identical": bool}`

- [ ] `image_compare_hash(file_path_1: str, file_path_2: str, hash_type: str = "phash") -> dict`
  - Perceptual hash comparison (phash, dhash, ahash)
  - Returns: `{"hash_1": str, "hash_2": str, "distance": int, "is_similar": bool}`

- [ ] `image_diff(file_path_1: str, file_path_2: str, output_path: str) -> dict`
  - Visual diff - highlights differences between images
  - Returns: `{"status": "success", "output_path": str, "diff_percentage": float, "diff_pixels": int}`

- [ ] `image_get_hash(file_path: str, hash_type: str = "phash") -> dict`
  - Calculate perceptual hash for single image
  - Returns: `{"hash": str, "hash_type": str}`

**Test file:** `tests/test_compare.py`

- [ ] Test SSIM comparison
- [ ] Test MSE comparison
- [ ] Test perceptual hash
- [ ] Test visual diff output
- [ ] Test different size images handling

---

### B1.3 QR/Barcode Decoder Module

**File:** `src/optic_mcp/decode.py`

**Description:** Decode QR codes, barcodes, and other machine-readable codes from images.

**Dependencies:** `pyzbar>=0.1.9` (add to main dependencies), requires libzbar system library

**Tools to implement:**

- [ ] `decode_qr(file_path: str) -> dict`
  - Decodes QR codes from image
  - Returns: `{"found": bool, "codes": [{"data": str, "type": str, "rect": dict}]}`

- [ ] `decode_barcode(file_path: str) -> dict`
  - Decodes barcodes (EAN, UPC, Code128, etc.)
  - Returns: `{"found": bool, "codes": [{"data": str, "type": str, "rect": dict}]}`

- [ ] `decode_all(file_path: str) -> dict`
  - Decodes all supported code types
  - Returns: `{"found": bool, "count": int, "codes": [{"data": str, "type": str, "rect": dict}]}`

**Test file:** `tests/test_decode.py`

- [ ] Test QR code decoding
- [ ] Test barcode decoding
- [ ] Test multiple codes in image
- [ ] Test no code found
- [ ] Test various barcode types

---

## Phase B2: Detection (Medium Complexity)

### B2.1 Face Detection Module

**File:** `src/optic_mcp/detect.py`

**Description:** Detect faces and objects in images using OpenCV's built-in
detectors (Haar cascades, DNN). No external ML frameworks required.

**Dependencies:** OpenCV (existing) - uses bundled Haar cascades and DNN models

**Tools to implement:**

- [ ] `detect_faces(file_path: str, method: str = "haar") -> dict`
  - Detects faces using Haar cascades or DNN
  - Returns: `{"found": bool, "count": int, "faces": [{"x": int, "y": int, "width": int, "height": int, "confidence"?: float}]}`

- [ ] `detect_faces_save(file_path: str, output_path: str, method: str = "haar") -> dict`
  - Detects faces and saves image with bounding boxes drawn
  - Returns: `{"found": bool, "count": int, "output_path": str, "faces": [...]}`

- [ ] `detect_eyes(file_path: str) -> dict`
  - Detects eyes in image (useful for face alignment)
  - Returns: `{"found": bool, "count": int, "eyes": [{"x": int, "y": int, "width": int, "height": int}]}`

- [ ] `detect_motion(file_path_1: str, file_path_2: str, threshold: float = 25.0) -> dict`
  - Compares two frames to detect motion
  - Returns: `{"motion_detected": bool, "motion_percentage": float, "motion_regions": [dict]}`

- [ ] `detect_edges(file_path: str, output_path: str, method: str = "canny") -> dict`
  - Edge detection (Canny, Sobel, Laplacian)
  - Returns: `{"status": "success", "output_path": str, "method": str}`

**Test file:** `tests/test_detect.py`

- [ ] Test face detection (mocked)
- [ ] Test eye detection
- [ ] Test motion detection
- [ ] Test edge detection
- [ ] Test no faces found case

---

# Part C: Camera Geometry & Calibration

## Phase C1: Camera Calibration (Medium-High Complexity)

### C1.1 Camera Calibration Module

**File:** `src/optic_mcp/calibration.py`

**Description:** Camera calibration tools for computing intrinsic and extrinsic
parameters. Essential for robotics, AR/VR, 3D reconstruction, and computer vision.

**Dependencies:** OpenCV (existing), NumPy (existing)

**Tools to implement:**

#### Checkerboard/ChArUco Detection

- [ ] `calibration_find_checkerboard(file_path: str, board_size: tuple = (9, 6)) -> dict`
  - Finds checkerboard corners in image
  - Returns: `{"found": bool, "corners": [[x, y], ...], "board_size": [rows, cols]}`

- [ ] `calibration_find_charuco(file_path: str, board_size: tuple = (5, 7), square_length: float = 0.04, marker_length: float = 0.02) -> dict`
  - Finds ChArUco board corners and IDs
  - Returns: `{"found": bool, "corners": [...], "ids": [...], "board_size": [rows, cols]}`

- [ ] `calibration_draw_corners(file_path: str, output_path: str, board_size: tuple = (9, 6)) -> dict`
  - Draws detected corners on image for verification
  - Returns: `{"status": "success", "output_path": str, "found": bool}`

#### Intrinsic Calibration

- [ ] `calibration_calibrate_camera(image_paths: list[str], board_size: tuple = (9, 6), square_size: float = 0.025) -> dict`
  - Calibrates camera from multiple checkerboard images
  - Returns: `{"status": "success", "camera_matrix": [[...]], "dist_coeffs": [...], "rms_error": float, "num_images_used": int}`

- [ ] `calibration_save_params(camera_matrix: list, dist_coeffs: list, file_path: str) -> dict`
  - Saves calibration parameters to YAML/JSON file
  - Returns: `{"status": "success", "file_path": str}`

- [ ] `calibration_load_params(file_path: str) -> dict`
  - Loads calibration parameters from file
  - Returns: `{"camera_matrix": [[...]], "dist_coeffs": [...], "image_size": [w, h]}`

#### Undistortion

- [ ] `calibration_undistort(file_path: str, output_path: str, camera_matrix: list, dist_coeffs: list) -> dict`
  - Removes lens distortion from image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `calibration_undistort_points(points: list, camera_matrix: list, dist_coeffs: list) -> dict`
  - Undistorts 2D point coordinates
  - Returns: `{"undistorted_points": [[x, y], ...]}`

**Test file:** `tests/test_calibration.py`

- [ ] Test checkerboard detection
- [ ] Test ChArUco detection
- [ ] Test camera calibration (with synthetic data)
- [ ] Test save/load params
- [ ] Test undistortion

---

### C1.2 Pose Estimation Module

**File:** `src/optic_mcp/pose.py`

**Description:** Estimate camera pose (extrinsic parameters) and object poses
relative to the camera. Used for AR, robotics, and 3D reconstruction.

**Dependencies:** OpenCV (existing), NumPy (existing)

**Tools to implement:**

#### Extrinsic Parameters (Camera Pose)

- [ ] `pose_estimate_checkerboard(file_path: str, camera_matrix: list, dist_coeffs: list, board_size: tuple = (9, 6), square_size: float = 0.025) -> dict`
  - Estimates camera pose from checkerboard
  - Returns: `{"found": bool, "rvec": [rx, ry, rz], "tvec": [tx, ty, tz], "rotation_matrix": [[...]], "euler_angles_deg": [roll, pitch, yaw]}`

- [ ] `pose_estimate_charuco(file_path: str, camera_matrix: list, dist_coeffs: list, board_size: tuple, square_length: float, marker_length: float) -> dict`
  - Estimates camera pose from ChArUco board
  - Returns: `{"found": bool, "rvec": [...], "tvec": [...], "rotation_matrix": [[...]], "euler_angles_deg": [...]}`

- [ ] `pose_estimate_markers(file_path: str, camera_matrix: list, dist_coeffs: list, marker_length: float, dict_type: str = "DICT_4X4_50") -> dict`
  - Estimates pose of ArUco markers
  - Returns: `{"found": bool, "markers": [{"id": int, "rvec": [...], "tvec": [...], "corners": [...]}]}`

#### PnP (Perspective-n-Point)

- [ ] `pose_solve_pnp(object_points: list, image_points: list, camera_matrix: list, dist_coeffs: list, method: str = "iterative") -> dict`
  - Solves PnP problem for arbitrary 3D-2D correspondences
  - Methods: "iterative", "p3p", "epnp", "ippe"
  - Returns: `{"success": bool, "rvec": [...], "tvec": [...], "rotation_matrix": [[...]], "reprojection_error": float}`

- [ ] `pose_draw_axes(file_path: str, output_path: str, camera_matrix: list, dist_coeffs: list, rvec: list, tvec: list, axis_length: float = 0.1) -> dict`
  - Draws 3D coordinate axes on image for visualization
  - Returns: `{"status": "success", "output_path": str}`

#### Coordinate Transforms

- [ ] `pose_rodrigues_to_matrix(rvec: list) -> dict`
  - Converts rotation vector to rotation matrix
  - Returns: `{"rotation_matrix": [[...]]}`

- [ ] `pose_matrix_to_rodrigues(rotation_matrix: list) -> dict`
  - Converts rotation matrix to rotation vector
  - Returns: `{"rvec": [rx, ry, rz]}`

- [ ] `pose_matrix_to_euler(rotation_matrix: list, order: str = "xyz") -> dict`
  - Converts rotation matrix to Euler angles
  - Returns: `{"euler_angles_deg": [roll, pitch, yaw], "euler_angles_rad": [...]}`

- [ ] `pose_compose_transforms(rvec1: list, tvec1: list, rvec2: list, tvec2: list) -> dict`
  - Composes two rigid transforms
  - Returns: `{"rvec": [...], "tvec": [...], "transform_matrix": [[4x4 matrix]]}`

- [ ] `pose_invert_transform(rvec: list, tvec: list) -> dict`
  - Inverts a rigid transform (world-to-camera <-> camera-to-world)
  - Returns: `{"rvec": [...], "tvec": [...], "transform_matrix": [[4x4 matrix]]}`

**Test file:** `tests/test_pose.py`

- [ ] Test checkerboard pose estimation
- [ ] Test ArUco marker detection and pose
- [ ] Test PnP solver
- [ ] Test coordinate transforms
- [ ] Test transform composition/inversion

---

### C1.3 Projection Module

**File:** `src/optic_mcp/projection.py`

**Description:** Project points between 2D image coordinates and 3D world coordinates.
Essential for mapping, measurement, and AR applications.

**Dependencies:** OpenCV (existing), NumPy (existing)

**Tools to implement:**

#### Point Projection

- [ ] `project_points_3d_to_2d(object_points: list, rvec: list, tvec: list, camera_matrix: list, dist_coeffs: list) -> dict`
  - Projects 3D world points to 2D image coordinates
  - Returns: `{"image_points": [[x, y], ...], "jacobian"?: [[...]]}`

- [ ] `project_points_2d_to_ray(image_points: list, camera_matrix: list, dist_coeffs: list) -> dict`
  - Converts 2D image points to 3D rays (direction vectors)
  - Returns: `{"rays": [[dx, dy, dz], ...], "normalized": bool}`

- [ ] `project_points_2d_to_3d_plane(image_points: list, camera_matrix: list, dist_coeffs: list, rvec: list, tvec: list, plane_z: float = 0) -> dict`
  - Projects 2D points to 3D assuming known Z plane (e.g., ground plane)
  - Returns: `{"world_points": [[x, y, z], ...]}`

#### Homography

- [ ] `projection_find_homography(src_points: list, dst_points: list, method: str = "ransac") -> dict`
  - Finds homography matrix between two sets of points
  - Returns: `{"homography": [[3x3]], "inliers_mask": [...], "num_inliers": int}`

- [ ] `projection_warp_perspective(file_path: str, output_path: str, homography: list, output_size: tuple) -> dict`
  - Warps image using homography matrix
  - Returns: `{"status": "success", "output_path": str, "output_size": [w, h]}`

- [ ] `projection_get_bird_eye_view(file_path: str, output_path: str, src_points: list, dst_size: tuple) -> dict`
  - Creates bird's eye view transformation
  - Returns: `{"status": "success", "output_path": str, "homography": [[...]]}`

#### Fundamental/Essential Matrix

- [ ] `projection_find_fundamental(points1: list, points2: list, method: str = "ransac") -> dict`
  - Finds fundamental matrix from point correspondences
  - Returns: `{"fundamental_matrix": [[3x3]], "inliers_mask": [...], "num_inliers": int}`

- [ ] `projection_find_essential(points1: list, points2: list, camera_matrix: list, method: str = "ransac") -> dict`
  - Finds essential matrix from point correspondences
  - Returns: `{"essential_matrix": [[3x3]], "inliers_mask": [...], "num_inliers": int}`

- [ ] `projection_decompose_essential(essential_matrix: list, points1: list, points2: list, camera_matrix: list) -> dict`
  - Decomposes essential matrix to recover relative pose
  - Returns: `{"rotation": [[3x3]], "translation": [tx, ty, tz], "valid_points": int}`

**Test file:** `tests/test_projection.py`

- [ ] Test 3D to 2D projection
- [ ] Test 2D to ray conversion
- [ ] Test homography finding
- [ ] Test perspective warp
- [ ] Test fundamental/essential matrix

---

### C1.4 Stereo Vision Module

**File:** `src/optic_mcp/stereo.py`

**Description:** Stereo camera calibration and depth estimation.
Used for 3D reconstruction and depth sensing.

**Dependencies:** OpenCV (existing), NumPy (existing)

**Tools to implement:**

#### Stereo Calibration

- [ ] `stereo_calibrate(left_images: list, right_images: list, board_size: tuple, square_size: float) -> dict`
  - Calibrates stereo camera pair
  - Returns: `{"camera_matrix_left": [[...]], "dist_coeffs_left": [...], "camera_matrix_right": [[...]], "dist_coeffs_right": [...], "R": [[...]], "T": [...], "E": [[...]], "F": [[...]], "rms_error": float}`

- [ ] `stereo_rectify(camera_matrix_left: list, dist_coeffs_left: list, camera_matrix_right: list, dist_coeffs_right: list, image_size: tuple, R: list, T: list) -> dict`
  - Computes rectification transforms for stereo pair
  - Returns: `{"R1": [[...]], "R2": [[...]], "P1": [[...]], "P2": [[...]], "Q": [[...]], "roi_left": [...], "roi_right": [...]}`

- [ ] `stereo_rectify_images(left_path: str, right_path: str, left_output: str, right_output: str, stereo_params: dict) -> dict`
  - Rectifies stereo image pair
  - Returns: `{"status": "success", "left_output": str, "right_output": str}`

#### Depth Estimation

- [ ] `stereo_compute_disparity(left_path: str, right_path: str, output_path: str, method: str = "sgbm", num_disparities: int = 64, block_size: int = 5) -> dict`
  - Computes disparity map from rectified stereo pair
  - Returns: `{"status": "success", "output_path": str, "min_disparity": float, "max_disparity": float}`

- [ ] `stereo_disparity_to_depth(disparity_path: str, Q_matrix: list, output_path: str) -> dict`
  - Converts disparity map to depth map
  - Returns: `{"status": "success", "output_path": str, "min_depth": float, "max_depth": float}`

- [ ] `stereo_reproject_to_3d(disparity_path: str, Q_matrix: list, output_path: str) -> dict`
  - Reprojects disparity to 3D point cloud (saves as PLY)
  - Returns: `{"status": "success", "output_path": str, "num_points": int}`

**Test file:** `tests/test_stereo.py`

- [ ] Test stereo calibration (synthetic)
- [ ] Test rectification
- [ ] Test disparity computation
- [ ] Test depth estimation

---

### C1.5 ArUco Markers Module

**File:** `src/optic_mcp/aruco.py`

**Description:** Generate and detect ArUco fiducial markers.
Widely used in robotics and AR for pose estimation.

**Dependencies:** OpenCV (existing) with aruco contrib module

**Tools to implement:**

#### Marker Generation

- [ ] `aruco_generate_marker(marker_id: int, output_path: str, size: int = 200, dict_type: str = "DICT_4X4_50") -> dict`
  - Generates single ArUco marker image
  - Returns: `{"status": "success", "output_path": str, "marker_id": int, "dict_type": str}`

- [ ] `aruco_generate_board(output_path: str, markers_x: int = 5, markers_y: int = 7, marker_length: float = 0.04, marker_separation: float = 0.01, dict_type: str = "DICT_4X4_50") -> dict`
  - Generates ArUco grid board
  - Returns: `{"status": "success", "output_path": str, "board_size": [x, y]}`

- [ ] `aruco_generate_charuco(output_path: str, squares_x: int = 5, squares_y: int = 7, square_length: float = 0.04, marker_length: float = 0.02, dict_type: str = "DICT_4X4_50") -> dict`
  - Generates ChArUco calibration board
  - Returns: `{"status": "success", "output_path": str, "board_size": [x, y]}`

#### Marker Detection

- [ ] `aruco_detect_markers(file_path: str, dict_type: str = "DICT_4X4_50") -> dict`
  - Detects ArUco markers in image
  - Returns: `{"found": bool, "count": int, "markers": [{"id": int, "corners": [[x,y], ...]}]}`

- [ ] `aruco_detect_and_draw(file_path: str, output_path: str, dict_type: str = "DICT_4X4_50") -> dict`
  - Detects markers and draws them on image
  - Returns: `{"found": bool, "count": int, "output_path": str, "markers": [...]}`

- [ ] `aruco_list_dictionaries() -> dict`
  - Lists available ArUco dictionary types
  - Returns: `{"dictionaries": ["DICT_4X4_50", "DICT_5X5_100", ...]}`

**Test file:** `tests/test_aruco.py`

- [ ] Test marker generation
- [ ] Test board generation
- [ ] Test marker detection
- [ ] Test different dictionary types

---

# Part D: Image Processing & Transformation

## Phase D1: Basic Transformations (Low Complexity)

### D1.1 Image Transform Module

**File:** `src/optic_mcp/transform.py`

**Description:** Basic image transformations - resize, crop, rotate, flip, format conversion.

**Dependencies:** OpenCV (existing), Pillow (shared with analyze)

**Tools to implement:**

- [ ] `transform_resize(file_path: str, output_path: str, width: int = None, height: int = None, scale: float = None, keep_aspect: bool = True) -> dict`
  - Resizes image (specify width/height or scale factor)
  - Returns: `{"status": "success", "output_path": str, "original_size": [w, h], "new_size": [w, h]}`

- [ ] `transform_crop(file_path: str, output_path: str, x: int, y: int, width: int, height: int) -> dict`
  - Crops region from image
  - Returns: `{"status": "success", "output_path": str, "crop_region": dict}`

- [ ] `transform_rotate(file_path: str, output_path: str, angle: float, expand: bool = True) -> dict`
  - Rotates image by angle (degrees)
  - Returns: `{"status": "success", "output_path": str, "angle": float, "new_size": [w, h]}`

- [ ] `transform_flip(file_path: str, output_path: str, direction: str = "horizontal") -> dict`
  - Flips image horizontally or vertically
  - Returns: `{"status": "success", "output_path": str, "direction": str}`

- [ ] `transform_convert_format(file_path: str, output_path: str, quality: int = 95) -> dict`
  - Converts between image formats (based on output extension)
  - Returns: `{"status": "success", "output_path": str, "original_format": str, "new_format": str}`

- [ ] `transform_thumbnail(file_path: str, output_path: str, max_size: int = 256) -> dict`
  - Creates thumbnail preserving aspect ratio
  - Returns: `{"status": "success", "output_path": str, "thumbnail_size": [w, h]}`

**Test file:** `tests/test_transform.py`

- [ ] Test resize operations
- [ ] Test crop
- [ ] Test rotate
- [ ] Test flip
- [ ] Test format conversion

---

### D1.2 Image Annotation Module

**File:** `src/optic_mcp/annotate.py`

**Description:** Draw shapes, text, and annotations on images.
Useful for debugging, visualization, and marking detections.

**Dependencies:** OpenCV (existing), Pillow (for better text rendering)

**Tools to implement:**

- [ ] `annotate_rectangle(file_path: str, output_path: str, x: int, y: int, width: int, height: int, color: list = [0, 255, 0], thickness: int = 2) -> dict`
  - Draws rectangle on image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `annotate_circle(file_path: str, output_path: str, center_x: int, center_y: int, radius: int, color: list = [0, 255, 0], thickness: int = 2) -> dict`
  - Draws circle on image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `annotate_line(file_path: str, output_path: str, x1: int, y1: int, x2: int, y2: int, color: list = [0, 255, 0], thickness: int = 2) -> dict`
  - Draws line on image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `annotate_text(file_path: str, output_path: str, text: str, x: int, y: int, font_scale: float = 1.0, color: list = [0, 255, 0], thickness: int = 2) -> dict`
  - Draws text on image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `annotate_polygon(file_path: str, output_path: str, points: list, color: list = [0, 255, 0], thickness: int = 2, fill: bool = False) -> dict`
  - Draws polygon on image
  - Returns: `{"status": "success", "output_path": str}`

- [ ] `annotate_bounding_boxes(file_path: str, output_path: str, boxes: list, labels: list = None, colors: list = None) -> dict`
  - Draws multiple labeled bounding boxes (for detection results)
  - boxes format: `[{"x": int, "y": int, "width": int, "height": int, "label"?: str}]`
  - Returns: `{"status": "success", "output_path": str, "num_boxes": int}`

**Test file:** `tests/test_annotate.py`

- [ ] Test rectangle drawing
- [ ] Test circle drawing
- [ ] Test text drawing
- [ ] Test bounding boxes

---

# Part E: Video Capabilities

## Phase E1: Video Recording & Timelapse (Medium Complexity)

### E1.1 Video Recording Module

**File:** `src/optic_mcp/record.py`

**Description:** Record video clips from camera sources.

**Dependencies:** OpenCV (existing)

**Tools to implement:**

- [ ] `record_video(camera_index: int, output_path: str, duration_seconds: float, fps: int = 30, codec: str = "mp4v") -> dict`
  - Records video from USB camera
  - Returns: `{"status": "success", "output_path": str, "duration": float, "fps": int, "frame_count": int}`

- [ ] `record_video_rtsp(rtsp_url: str, output_path: str, duration_seconds: float, fps: int = None) -> dict`
  - Records video from RTSP stream
  - Returns: `{"status": "success", "output_path": str, "duration": float, "fps": int, "frame_count": int}`

**Test file:** `tests/test_record.py`

- [ ] Test USB recording (mocked)
- [ ] Test RTSP recording (mocked)
- [ ] Test duration limiting

---

### E1.2 Timelapse Module

**File:** `src/optic_mcp/timelapse.py`

**Description:** Capture timelapse sequences from cameras.

**Dependencies:** OpenCV (existing)

**Tools to implement:**

- [ ] `timelapse_capture(camera_index: int, output_dir: str, num_frames: int, interval_seconds: float, prefix: str = "frame") -> dict`
  - Captures timelapse frames at intervals
  - Returns: `{"status": "success", "output_dir": str, "num_frames": int, "file_paths": [...]}`

- [ ] `timelapse_create_video(input_dir: str, output_path: str, fps: int = 24, pattern: str = "*.jpg") -> dict`
  - Creates video from timelapse frames
  - Returns: `{"status": "success", "output_path": str, "num_frames": int, "duration": float}`

**Test file:** `tests/test_timelapse.py`

- [ ] Test frame capture (mocked)
- [ ] Test video creation

---

### E1.3 Video Analysis Module

**File:** `src/optic_mcp/video_analyze.py`

**Description:** Extract information and frames from video files.

**Dependencies:** OpenCV (existing)

**Tools to implement:**

- [ ] `video_get_info(file_path: str) -> dict`
  - Gets video metadata (duration, fps, resolution, codec)
  - Returns: `{"duration": float, "fps": float, "frame_count": int, "width": int, "height": int, "codec": str}`

- [ ] `video_extract_frame(file_path: str, output_path: str, timestamp_seconds: float = None, frame_number: int = None) -> dict`
  - Extracts single frame from video
  - Returns: `{"status": "success", "output_path": str, "timestamp": float, "frame_number": int}`

- [ ] `video_extract_frames(file_path: str, output_dir: str, interval_seconds: float = 1.0, max_frames: int = None) -> dict`
  - Extracts frames at regular intervals
  - Returns: `{"status": "success", "output_dir": str, "num_frames": int, "file_paths": [...]}`

**Test file:** `tests/test_video_analyze.py`

- [ ] Test video info extraction
- [ ] Test frame extraction
- [ ] Test interval extraction

---

# Part F: Utilities & Monitoring

## Phase F1: Utilities (Low Complexity)

### F1.1 Health Check Module

**File:** `src/optic_mcp/health.py`

**Description:** Camera health checks and system diagnostics.

**Tools to implement:**

- [ ] `health_check_all_cameras() -> dict`
  - Tests all USB cameras and returns status
  - Returns: `{"cameras": [{"index": int, "status": str, "error"?: str}], "total": int, "available": int}`

- [ ] `health_check_stream(url: str, stream_type: str = "auto") -> dict`
  - Tests stream connectivity (auto-detects RTSP/HLS/MJPEG)
  - Returns: `{"status": "available"|"unavailable", "url": str, "stream_type": str, "latency_ms": float}`

- [ ] `health_get_system_info() -> dict`
  - Gets system information relevant to camera operations
  - Returns: `{"opencv_version": str, "platform": str, "python_version": str, "available_backends": [...]}`

**Test file:** `tests/test_health.py`

- [ ] Test camera health check
- [ ] Test stream health check
- [ ] Test system info

---

# Implementation Sprints

## Sprint 1: Foundation (Phase A1 + B1.3)
1. [ ] Add `requests`, `mss`, `Pillow`, `pyzbar` to dependencies in `pyproject.toml`
2. [ ] Implement `mjpeg.py` module
3. [ ] Implement `screen.py` module
4. [ ] Implement `http_image.py` module
5. [ ] Implement `decode.py` module (QR/barcode)
6. [ ] Add all tools to `server.py`
7. [ ] Write tests for all new modules
8. [ ] Run full test suite, lint, verify
9. [ ] Update README.md with new tools

## Sprint 2: Analysis & Comparison (Phase B1.1, B1.2)
1. [ ] Implement `analyze.py` module (metadata, stats, histogram, colors)
2. [ ] Implement `compare.py` module (SSIM, MSE, hash, diff)
3. [ ] Add tools to `server.py`
4. [ ] Write tests
5. [ ] Update README.md

## Sprint 3: Detection (Phase B2)
1. [ ] Implement `detect.py` module (faces, motion, edges)
2. [ ] Add tools to `server.py`
3. [ ] Write tests
4. [ ] Update README.md

## Sprint 4: Camera Geometry - Calibration & Pose (Phase C1.1, C1.2)
1. [ ] Implement `calibration.py` module
2. [ ] Implement `pose.py` module
3. [ ] Add tools to `server.py`
4. [ ] Write tests
5. [ ] Update README.md

## Sprint 5: Camera Geometry - Projection & Stereo (Phase C1.3, C1.4, C1.5)
1. [ ] Implement `projection.py` module
2. [ ] Implement `stereo.py` module
3. [ ] Implement `aruco.py` module
4. [ ] Add tools to `server.py`
5. [ ] Write tests
6. [ ] Update README.md

## Sprint 6: Transformations & Annotations (Phase D1)
1. [ ] Implement `transform.py` module
2. [ ] Implement `annotate.py` module
3. [ ] Add tools to `server.py`
4. [ ] Write tests
5. [ ] Update README.md

## Sprint 7: Video & Utilities (Phase E1, F1)
1. [ ] Implement `record.py` module
2. [ ] Implement `timelapse.py` module
3. [ ] Implement `video_analyze.py` module
4. [ ] Implement `health.py` module
5. [ ] Add tools to `server.py`
6. [ ] Write tests
7. [ ] Update README.md

## Sprint 8: Advanced Protocols (Phase A2, A3)
1. [ ] Add optional dependencies to `pyproject.toml`
2. [ ] Implement `onvif_cam.py` module
3. [ ] Implement `webrtc.py` module
4. [ ] (Optional) Implement `ndi.py` module
5. [ ] (Optional) Implement `gstreamer.py` module
6. [ ] Add tools to `server.py`
7. [ ] Write tests
8. [ ] Update README.md

## Sprint 9: Polish & Release
1. [ ] Integration testing with real devices
2. [ ] Performance optimization
3. [ ] Documentation improvements
4. [ ] API consistency review
5. [ ] Version bump and release

---

# File Structure After Implementation

```
src/optic_mcp/
├── __init__.py
├── server.py              # Main MCP server - register all tools
│
├── # === SOURCES (Part A) ===
├── usb.py                 # ✅ Existing - USB cameras
├── rtsp.py                # ✅ Existing - RTSP streams
├── hls.py                 # ✅ Existing - HLS streams
├── stream.py              # ✅ Existing - MJPEG streaming server
├── mjpeg.py               # 🆕 MJPEG/HTTP input capture
├── screen.py              # 🆕 Screen/monitor capture
├── http_image.py          # 🆕 HTTP image download
├── onvif_cam.py           # 🆕 ONVIF cameras (optional)
├── webrtc.py              # 🆕 WebRTC/WHEP (optional)
├── ndi.py                 # 🆕 NDI streams (optional)
├── gstreamer.py           # 🆕 GStreamer (optional)
│
├── # === ANALYSIS (Part B) ===
├── analyze.py             # 🆕 Metadata, stats, histogram, colors
├── compare.py             # 🆕 SSIM, MSE, hash, visual diff
├── decode.py              # 🆕 QR codes, barcodes
├── detect.py              # 🆕 Face, motion, edge detection
│
├── # === GEOMETRY (Part C) ===
├── calibration.py         # 🆕 Camera calibration
├── pose.py                # 🆕 Pose estimation, PnP
├── projection.py          # 🆕 Homography, projection
├── stereo.py              # 🆕 Stereo vision, depth
├── aruco.py               # 🆕 ArUco marker generation/detection
│
├── # === PROCESSING (Part D) ===
├── transform.py           # 🆕 Resize, crop, rotate, convert
├── annotate.py            # 🆕 Draw shapes, text, boxes
│
├── # === VIDEO (Part E) ===
├── record.py              # 🆕 Video recording
├── timelapse.py           # 🆕 Timelapse capture
├── video_analyze.py       # 🆕 Video info, frame extraction
│
└── # === UTILITIES (Part F) ===
    └── health.py          # 🆕 Health checks, diagnostics

tests/
├── # Existing
├── test_usb.py
├── test_rtsp.py
├── test_hls.py
├── test_stream.py
├── test_server.py
│
├── # Sources
├── test_mjpeg.py
├── test_screen.py
├── test_http_image.py
├── test_onvif_cam.py
├── test_webrtc.py
│
├── # Analysis
├── test_analyze.py
├── test_compare.py
├── test_decode.py
├── test_detect.py
│
├── # Geometry
├── test_calibration.py
├── test_pose.py
├── test_projection.py
├── test_stereo.py
├── test_aruco.py
│
├── # Processing
├── test_transform.py
├── test_annotate.py
│
├── # Video
├── test_record.py
├── test_timelapse.py
├── test_video_analyze.py
│
└── # Utilities
    └── test_health.py
```

---

# Updated pyproject.toml Dependencies

```toml
[project]
dependencies = [
    "mcp[cli]>=1.0.0",
    "opencv-python>=4.8.0",
    "opencv-contrib-python>=4.8.0",  # For ArUco
    "numpy>=1.24.0",
    "requests>=2.28.0",              # For MJPEG, HTTP
    "mss>=9.0.0",                    # For screen capture
    "Pillow>=10.0.0",                # For metadata, transforms
    "pyzbar>=0.1.9",                 # For QR/barcode
]

[project.optional-dependencies]
compare = [
    "scikit-image>=0.21.0",          # For SSIM
    "imagehash>=4.3.0",              # For perceptual hashing
]
onvif = [
    "onvif-zeep>=0.4.0",
    "WSDiscovery>=2.0.0",
]
webrtc = [
    "aiortc>=1.6.0",
    "aiohttp>=3.8.0",
]
ndi = [
    "ndi-python>=5.0.0",
]
gstreamer = [
    "PyGObject>=3.42.0",
]
all = [
    "optic-mcp[compare,onvif,webrtc,ndi,gstreamer]",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "numpy>=1.24.0",
    "ruff>=0.8.0",
    "twine>=5.0.0",
    "bump2version>=1.0.0",
]
```

---

# Response Format Standards

All tools MUST return JSON-serializable dictionaries. Never return raw image data.

### Capture/Save Response
```python
{"status": "success", "file_path": "/path/to/image.jpg", "width": 1920, "height": 1080}
```

### Check/Validate Response
```python
{"status": "available"|"unavailable", "url": "...", "error"?: "..."}
```

### Detection Response
```python
{"found": bool, "count": int, "detections": [{"x": int, "y": int, ...}]}
```

### Calibration/Geometry Response
```python
{"status": "success", "camera_matrix": [[...]], "dist_coeffs": [...], "rms_error": float}
```

### Discovery Response
```python
[{"name": "Camera 1", "host": "192.168.1.50", ...}]
```

---

# Notes

- All modules must handle OpenCV stderr suppression (import cv2 after server.py suppression)
- Optional dependencies should use try/except imports with graceful degradation
- Tools requiring unavailable deps should raise clear `RuntimeError` messages
- Follow existing code style: type hints, docstrings, try/finally for cleanup
- All matrix/array returns must be lists (not numpy arrays) for JSON serialization
- Camera geometry functions should document coordinate system conventions
