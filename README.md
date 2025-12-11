# OpticMCP

[![PyPI version](https://badge.fury.io/py/optic-mcp.svg)](https://pypi.org/project/optic-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides camera/vision tools for AI assistants. Connect to cameras and capture images for use with LLMs.

## Vision

OpticMCP aims to be a universal camera interface for AI assistants, supporting any camera type:

- **USB Cameras** ✅
- **IP/Network Cameras** ✅ - RTSP, HLS, MJPEG streams
- **Screen Capture** ✅ - Desktop/monitor capture
- **HTTP Images** ✅ - Download images from URLs
- **QR/Barcode Decoding** ✅ - Decode QR codes and barcodes
- **Image Analysis** ✅ - Metadata, stats, histograms, dominant colors
- **Image Comparison** ✅ - SSIM, MSE, perceptual hashing, visual diff
- **Detection** ✅ - Face detection, motion detection, edge detection
- **Raspberry Pi Cameras** (Planned) - CSI camera modules
- **Mobile Cameras** (Planned) - Phone camera integration

## Current Features

### USB Cameras
- **list_cameras** - Scan and list all available USB cameras
- **save_image** - Capture a frame and save directly to a file

### Camera Streaming
- **start_stream** - Start streaming a camera to a localhost HTTP server (MJPEG)
- **stop_stream** - Stop streaming a camera
- **list_streams** - List all active camera streams

### Multi-Camera Dashboard
- **start_dashboard** - Start a dynamic dashboard that displays all active camera streams in a responsive grid
- **stop_dashboard** - Stop the dashboard server

### RTSP Streams
- **rtsp_save_image** - Capture and save a frame from an RTSP stream
- **rtsp_check_stream** - Validate RTSP stream and get properties

### HLS Streams (HTTP Live Streaming)
- **hls_save_image** - Capture and save a frame from an HLS stream
- **hls_check_stream** - Validate HLS stream and get properties

### MJPEG Streams
- **mjpeg_save_image** - Capture a frame from an MJPEG stream (common in IP cameras, ESP32-CAM)
- **mjpeg_check_stream** - Validate MJPEG stream availability

### Screen Capture
- **screen_list_monitors** - List all available monitors/displays
- **screen_save_image** - Capture full screenshot of a monitor
- **screen_save_region** - Capture a specific region of the screen

### HTTP Images
- **http_save_image** - Download and save an image from any URL
- **http_check_image** - Check if a URL points to a valid image

### QR/Barcode Decoding (requires libzbar)
- **decode_qr** - Decode QR codes from an image
- **decode_barcode** - Decode barcodes (EAN, UPC, Code128, etc.)
- **decode_all** - Decode all QR codes and barcodes from an image
- **decode_and_annotate** - Decode and save annotated image with bounding boxes

### Image Analysis
- **image_get_metadata** - Extract image metadata including EXIF data
- **image_get_stats** - Calculate brightness, contrast, sharpness
- **image_get_histogram** - Generate color histogram with optional visualization
- **image_get_dominant_colors** - Extract dominant colors using K-means clustering

### Image Comparison
- **image_compare_ssim** - Compare images using Structural Similarity Index
- **image_compare_mse** - Compare images using Mean Squared Error
- **image_compare_hash** - Compare images using perceptual hashing (phash, dhash, ahash)
- **image_get_hash** - Generate perceptual hash for an image
- **image_diff** - Create visual diff highlighting differences
- **image_compare_histograms** - Compare images by color histograms

### Detection
- **detect_faces** - Detect faces using Haar cascades or DNN
- **detect_faces_save** - Detect faces and save annotated image
- **detect_motion** - Detect motion between two frames
- **detect_edges** - Detect edges using Canny, Sobel, or Laplacian
- **detect_objects** - Detect common objects using MobileNet SSD

## Requirements

- Python 3.10+
- USB camera connected to your system

## Installation

### From PyPI (Recommended)

```bash
pip install optic-mcp
```

Or with `uv`:

```bash
uv pip install optic-mcp
```

### From Source

```bash
# Clone the repository
git clone https://github.com/Timorleiderman/OpticMCP.git
cd OpticMCP

# Install dependencies with uv
uv sync
```

## Usage

### Running the MCP Server

If installed from PyPI:

```bash
optic-mcp
```

Or with uvx (no installation required):

```bash
uvx optic-mcp
```

### Running from Source

```bash
uv run optic-mcp
```

## MCP Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "optic-mcp": {
      "command": "uvx",
      "args": ["optic-mcp"]
    }
  }
}
```

### OpenCode

Add to your `opencode.json` (in `.opencode/` in your project directory or `~/.opencode/` globally):

```json
{
  "mcp": {
    "optic-mcp": {
      "type": "local",
      "command": ["uvx", "optic-mcp"]
    }
  }
}
```

### Other MCP Clients

Using uvx (recommended - no installation required):

```json
{
  "mcpServers": {
    "optic-mcp": {
      "command": "uvx",
      "args": ["optic-mcp"]
    }
  }
}
```

Using pip installation:

```json
{
  "mcpServers": {
    "optic-mcp": {
      "command": "optic-mcp"
    }
  }
}
```

From source:

```json
{
  "mcpServers": {
    "optic-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/OpticMCP", "optic-mcp"]
    }
  }
}
```

## Tools

### list_cameras

Scans for available USB cameras (indices 0-9) and returns their status.

```json
[
  {
    "index": 0,
    "status": "available",
    "backend": "AVFOUNDATION",
    "description": "Camera 0 (AVFOUNDATION)"
  }
]
```

### save_image

Captures a frame and saves it to disk.

**Parameters:**
- `file_path` (str) - Path where the image will be saved
- `camera_index` (int, default: 0) - Camera index to capture from

**Returns:** Success message with file path

### Streaming Tools

Stream cameras to a local HTTP server for real-time viewing in any browser.

#### start_stream

Start streaming a camera to a localhost HTTP server. The stream uses MJPEG format which is widely supported.

**Parameters:**
- `camera_index` (int, default: 0) - Camera index to stream
- `port` (int, default: 8080) - Port to serve the stream on

**Returns:** Dictionary with stream URLs and status

```json
{
  "status": "started",
  "camera_index": 0,
  "port": 8080,
  "url": "http://localhost:8080",
  "stream_url": "http://localhost:8080/stream"
}
```

**Usage:**
- Open `http://localhost:8080` in a browser to view the stream with a simple UI
- Use `http://localhost:8080/stream` for the raw MJPEG stream (can be embedded in other applications)

#### stop_stream

Stop streaming a camera.

**Parameters:**
- `camera_index` (int, default: 0) - Camera index to stop streaming

**Returns:** Dictionary with status

#### list_streams

List all active camera streams.

**Returns:** List of active stream information including URLs and ports

### Dashboard Tools

#### start_dashboard

Start a dynamic multi-camera dashboard server. The dashboard automatically detects all active camera streams and displays them in a responsive grid layout.

**Parameters:**
- `port` (int, default: 9000) - Port to serve the dashboard on

**Returns:** Dictionary with dashboard URL and status

```json
{
  "status": "started",
  "port": 9000,
  "url": "http://localhost:9000"
}
```

**Usage:**
1. Start one or more camera streams with `start_stream`
2. Start the dashboard with `start_dashboard`
3. Open `http://localhost:9000` in a browser
4. The dashboard auto-updates every 3 seconds to detect new/removed streams

#### stop_dashboard

Stop the dashboard server.

**Returns:** Dictionary with status

### RTSP Tools

> **Note:** RTSP functionality has not been tested with real RTSP hardware/streams. It is implemented but may require adjustments for specific camera vendors.

#### rtsp_save_image

Captures a frame from an RTSP stream and saves it to disk.

**Parameters:**
- `rtsp_url` (str) - RTSP stream URL (e.g., `rtsp://ip:554/stream`)
- `file_path` (str) - Path where the image will be saved
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Success message with file path

#### rtsp_check_stream

Validates an RTSP stream and returns stream information.

**Parameters:**
- `rtsp_url` (str) - RTSP stream URL to validate
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Dictionary with stream status and properties (width, height, fps, codec)

### HLS Tools

#### hls_save_image

Captures a frame from an HLS stream and saves it to disk.

**Parameters:**
- `hls_url` (str) - HLS stream URL (typically ending in `.m3u8`)
- `file_path` (str) - Path where the image will be saved
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Success message with file path

#### hls_check_stream

Validates an HLS stream and returns stream information.

**Parameters:**
- `hls_url` (str) - HLS stream URL to validate
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Dictionary with stream status and properties (width, height, fps, codec)

### MJPEG Tools

#### mjpeg_save_image

Captures a frame from an MJPEG stream (common in IP cameras, ESP32-CAM, Arduino cameras).

**Parameters:**
- `mjpeg_url` (str) - MJPEG stream URL (e.g., `http://camera/video.mjpg`)
- `file_path` (str) - Path where the image will be saved
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Dictionary with status, file_path, and size_bytes

#### mjpeg_check_stream

Validates an MJPEG stream URL.

**Parameters:**
- `mjpeg_url` (str) - MJPEG stream URL to validate
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Dictionary with status, url, and content_type

### Screen Capture Tools

#### screen_list_monitors

Lists all available monitors/displays.

**Returns:** List of monitors with id, dimensions, and position

#### screen_save_image

Captures a full screenshot of a monitor.

**Parameters:**
- `file_path` (str) - Path where the image will be saved
- `monitor` (int, default: 0) - Monitor index (0 = all monitors combined)

**Returns:** Dictionary with status, file_path, and dimensions

#### screen_save_region

Captures a specific region of the screen.

**Parameters:**
- `file_path` (str) - Path where the image will be saved
- `x` (int) - X coordinate of top-left corner
- `y` (int) - Y coordinate of top-left corner
- `width` (int) - Width in pixels
- `height` (int) - Height in pixels

**Returns:** Dictionary with status, file_path, and region details

### HTTP Image Tools

#### http_save_image

Downloads an image from a URL and saves it to disk.

**Parameters:**
- `url` (str) - Image URL (http:// or https://)
- `file_path` (str) - Path where the image will be saved
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Dictionary with status, file_path, size_bytes, and content_type

#### http_check_image

Validates an image URL using a HEAD request.

**Parameters:**
- `url` (str) - Image URL to validate
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Dictionary with status, content_type, and size_bytes

### QR/Barcode Tools

> **Note:** These tools require the `libzbar` system library. Install with: `brew install zbar` (macOS) or `apt install libzbar0` (Linux)

#### decode_qr

Decodes QR codes from an image file.

**Parameters:**
- `file_path` (str) - Path to the image file

**Returns:** Dictionary with found, count, and codes list

#### decode_barcode

Decodes barcodes (EAN, UPC, Code128, etc.) from an image file.

**Parameters:**
- `file_path` (str) - Path to the image file

**Returns:** Dictionary with found, count, and codes list

#### decode_all

Decodes all QR codes and barcodes from an image file.

**Parameters:**
- `file_path` (str) - Path to the image file

**Returns:** Dictionary with found, count, and codes list

#### decode_and_annotate

Decodes codes and saves an annotated image with bounding boxes.

**Parameters:**
- `file_path` (str) - Path to the input image
- `output_path` (str) - Path for the annotated output image

**Returns:** Dictionary with found, count, output_path, and codes list

### Image Analysis Tools

#### image_get_metadata

Extracts metadata from an image file including dimensions, format, and EXIF data.

**Parameters:**
- `file_path` (str) - Path to the image file

**Returns:** Dictionary with width, height, format, mode, file_size_bytes, and exif dict

```json
{
  "width": 1920,
  "height": 1080,
  "format": "JPEG",
  "mode": "RGB",
  "file_size_bytes": 245678,
  "exif": {"Make": "Canon", "Model": "EOS R5", ...}
}
```

#### image_get_stats

Calculates basic image statistics including brightness, contrast, and sharpness.

**Parameters:**
- `file_path` (str) - Path to the image file

**Returns:** Dictionary with brightness (0-1), contrast (0-1), sharpness, and is_grayscale

```json
{
  "brightness": 0.65,
  "contrast": 0.42,
  "sharpness": 2.35,
  "is_grayscale": false
}
```

#### image_get_histogram

Calculates color histogram for each channel (R, G, B) with optional visualization.

**Parameters:**
- `file_path` (str) - Path to the image file
- `output_path` (str, optional) - Path to save histogram visualization

**Returns:** Dictionary with channels (r, g, b arrays of 256 values) and output_path if provided

#### image_get_dominant_colors

Extracts dominant colors using K-means clustering.

**Parameters:**
- `file_path` (str) - Path to the image file
- `num_colors` (int, default: 5) - Number of colors to extract (1-20)

**Returns:** List of colors with RGB values, hex codes, and percentages

```json
{
  "colors": [
    {"rgb": [64, 128, 192], "hex": "#4080C0", "percentage": 35.2},
    {"rgb": [255, 255, 255], "hex": "#FFFFFF", "percentage": 28.1}
  ]
}
```

### Image Comparison Tools

#### image_compare_ssim

Compares two images using Structural Similarity Index (SSIM).

**Parameters:**
- `file_path_1` (str) - Path to first image
- `file_path_2` (str) - Path to second image
- `threshold` (float, default: 0.95) - Similarity threshold

**Returns:** Dictionary with ssim_score (-1 to 1), is_similar, and threshold

```json
{
  "ssim_score": 0.9823,
  "is_similar": true,
  "threshold": 0.95
}
```

#### image_compare_mse

Compares two images using Mean Squared Error.

**Parameters:**
- `file_path_1` (str) - Path to first image
- `file_path_2` (str) - Path to second image

**Returns:** Dictionary with mse, is_identical, and normalized_mse (0-1)

#### image_compare_hash

Compares two images using perceptual hashing.

**Parameters:**
- `file_path_1` (str) - Path to first image
- `file_path_2` (str) - Path to second image
- `hash_type` (str, default: "phash") - Hash type: "phash", "dhash", or "ahash"

**Returns:** Dictionary with hash_1, hash_2, distance, is_similar, and hash_type

```json
{
  "hash_1": "8f0f0f0f0f0f0f0f",
  "hash_2": "8f0f0f0f0f0f0f0f",
  "distance": 0,
  "is_similar": true,
  "hash_type": "phash"
}
```

#### image_get_hash

Generates a perceptual hash for a single image.

**Parameters:**
- `file_path` (str) - Path to the image file
- `hash_type` (str, default: "phash") - Hash type: "phash", "dhash", or "ahash"

**Returns:** Dictionary with hash (hex string) and hash_type

#### image_diff

Creates a visual diff highlighting differences between two images.

**Parameters:**
- `file_path_1` (str) - Path to reference image
- `file_path_2` (str) - Path to comparison image
- `output_path` (str) - Path to save diff visualization
- `threshold` (int, default: 30) - Pixel difference threshold (0-255)

**Returns:** Dictionary with status, output_path, diff_percentage, and diff_pixels

```json
{
  "status": "success",
  "output_path": "/path/to/diff.png",
  "diff_percentage": 12.5,
  "diff_pixels": 25600
}
```

#### image_compare_histograms

Compares two images by their color histograms.

**Parameters:**
- `file_path_1` (str) - Path to first image
- `file_path_2` (str) - Path to second image
- `method` (str, default: "correlation") - Method: "correlation", "chi_square", "intersection", "bhattacharyya"

**Returns:** Dictionary with score, method, and is_similar

### Detection Tools

#### detect_faces

Detects faces in an image using Haar cascades or DNN.

**Parameters:**
- `file_path` (str) - Path to the image file
- `method` (str, default: "haar") - Detection method: "haar" (fast) or "dnn" (accurate)

**Returns:** Dictionary with found, count, and faces list containing x, y, width, height, and confidence (DNN only)

```json
{
  "found": true,
  "count": 2,
  "faces": [
    {"x": 120, "y": 80, "width": 150, "height": 150},
    {"x": 400, "y": 100, "width": 140, "height": 140, "confidence": 0.95}
  ]
}
```

#### detect_faces_save

Detects faces and saves an annotated image with bounding boxes.

**Parameters:**
- `file_path` (str) - Path to the input image
- `output_path` (str) - Path to save annotated image
- `method` (str, default: "haar") - Detection method: "haar" or "dnn"

**Returns:** Dictionary with found, count, output_path, and faces list

#### detect_motion

Compares two frames to detect motion between them.

**Parameters:**
- `file_path_1` (str) - Path to the first (earlier) image
- `file_path_2` (str) - Path to the second (later) image
- `threshold` (float, default: 25.0) - Pixel difference threshold (0-255)

**Returns:** Dictionary with motion_detected, motion_percentage, motion_regions list, and changed_pixels

```json
{
  "motion_detected": true,
  "motion_percentage": 15.3,
  "motion_regions": [
    {"x": 200, "y": 150, "width": 80, "height": 120}
  ],
  "changed_pixels": 31250
}
```

#### detect_edges

Detects edges in an image using various methods.

**Parameters:**
- `file_path` (str) - Path to the input image
- `output_path` (str) - Path to save edge detection output
- `method` (str, default: "canny") - Method: "canny", "sobel", or "laplacian"

**Returns:** Dictionary with status, output_path, and method

```json
{
  "status": "success",
  "output_path": "/path/to/edges.png",
  "method": "canny"
}
```

#### detect_objects

Detects common objects using MobileNet SSD.

**Parameters:**
- `file_path` (str) - Path to the image file
- `confidence_threshold` (float, default: 0.5) - Minimum confidence (0-1)

**Returns:** Dictionary with found, count, and objects list

> **Note:** Requires pre-trained MobileNet SSD model files. Returns empty result if models are not available.

```json
{
  "found": true,
  "count": 3,
  "objects": [
    {"class": "person", "confidence": 0.92, "x": 50, "y": 100, "width": 200, "height": 400},
    {"class": "car", "confidence": 0.87, "x": 300, "y": 250, "width": 180, "height": 120}
  ]
}
```

## Technical Notes

### OpenCV + MCP Compatibility

OpenCV prints debug messages to stderr which corrupts MCP's stdio communication. This server suppresses stderr at the file descriptor level before importing cv2 to prevent this issue.

## Roadmap

- [x] **v0.1.0** - USB camera support via OpenCV
- [x] **v0.2.0** - IP camera support (RTSP and HLS streams)
- [x] **v0.3.0** - Multi-camera dashboard with realtime streaming
- [x] **v0.4.0** - Screen capture, MJPEG streams, HTTP images, QR/barcode decoding
- [x] **v0.5.0** - Image analysis and comparison tools (metadata, stats, SSIM, hashing, diff)
- [x] **v0.6.0** - Detection tools (face detection, motion detection, edge detection)
- [ ] **v0.7.0** - Camera configuration (resolution, format, etc.)
- [ ] **v0.8.0** - Video recording capabilities

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT

<a href="https://glama.ai/mcp/servers/@Timorleiderman/OpticMCP">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@Timorleiderman/OpticMCP/badge" />
</a>
