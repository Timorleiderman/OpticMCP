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

## Technical Notes

### OpenCV + MCP Compatibility

OpenCV prints debug messages to stderr which corrupts MCP's stdio communication. This server suppresses stderr at the file descriptor level before importing cv2 to prevent this issue.

## Roadmap

- [x] **v0.1.0** - USB camera support via OpenCV
- [x] **v0.2.0** - IP camera support (RTSP and HLS streams)
- [x] **v0.3.0** - Multi-camera dashboard with realtime streaming
- [x] **v0.4.0** - Screen capture, MJPEG streams, HTTP images, QR/barcode decoding
- [ ] **v0.5.0** - Camera configuration (resolution, format, etc.)
- [ ] **v0.6.0** - Video recording capabilities

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT

<a href="https://glama.ai/mcp/servers/@Timorleiderman/OpticMCP">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@Timorleiderman/OpticMCP/badge" />
</a>
