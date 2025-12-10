# OpticMCP

[![PyPI version](https://badge.fury.io/py/optic-mcp.svg)](https://pypi.org/project/optic-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides camera/vision tools for AI assistants. Connect to cameras and capture images for use with LLMs.

## Vision

OpticMCP aims to be a universal camera interface for AI assistants, supporting any camera type:

- **USB Cameras** (Current)
- **IP/Network Cameras** (Current) - RTSP, HLS streams
- **Raspberry Pi Cameras** (Planned) - CSI camera modules
- **Screen Capture** (Planned) - Desktop/window capture
- **Mobile Cameras** (Planned) - Phone camera integration
- **Cloud Cameras** (Planned) - Integration with cloud camera services

## Current Features

### USB Cameras
- **list_cameras** - Scan and list all available USB cameras
- **capture_image** - Capture a frame and return as base64-encoded JPEG
- **save_image** - Capture a frame and save directly to a file

### RTSP Streams (Not tested with real hardware)
- **rtsp_capture_image** - Capture a frame from an RTSP stream
- **rtsp_save_image** - Capture and save a frame from an RTSP stream
- **rtsp_check_stream** - Validate RTSP stream and get properties

### HLS Streams (HTTP Live Streaming)
- **hls_capture_image** - Capture a frame from an HLS stream
- **hls_save_image** - Capture and save a frame from an HLS stream
- **hls_check_stream** - Validate HLS stream and get properties

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

### capture_image

Captures a single frame from the specified camera.

**Parameters:**
- `camera_index` (int, default: 0) - Camera index to capture from

**Returns:** Base64-encoded JPEG string

### save_image

Captures a frame and saves it to disk.

**Parameters:**
- `file_path` (str) - Path where the image will be saved
- `camera_index` (int, default: 0) - Camera index to capture from

**Returns:** Success message with file path

### RTSP Tools

> **Note:** RTSP functionality has not been tested with real RTSP hardware/streams. It is implemented but may require adjustments for specific camera vendors.

#### rtsp_capture_image

Captures a single frame from an RTSP stream.

**Parameters:**
- `rtsp_url` (str) - RTSP stream URL (e.g., `rtsp://ip:554/stream`)
- `timeout_seconds` (int, default: 10) - Connection timeout

**Returns:** Base64-encoded JPEG string

#### rtsp_save_image

Captures a frame from an RTSP stream and saves it to disk.

**Parameters:**
- `rtsp_url` (str) - RTSP stream URL
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

#### hls_capture_image

Captures a single frame from an HLS (HTTP Live Streaming) URL.

**Parameters:**
- `hls_url` (str) - HLS stream URL (typically ending in `.m3u8`)
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Base64-encoded JPEG string

#### hls_save_image

Captures a frame from an HLS stream and saves it to disk.

**Parameters:**
- `hls_url` (str) - HLS stream URL
- `file_path` (str) - Path where the image will be saved
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Success message with file path

#### hls_check_stream

Validates an HLS stream and returns stream information.

**Parameters:**
- `hls_url` (str) - HLS stream URL to validate
- `timeout_seconds` (int, default: 30) - Connection timeout

**Returns:** Dictionary with stream status and properties (width, height, fps, codec)

## Technical Notes

### OpenCV + MCP Compatibility

OpenCV prints debug messages to stderr which corrupts MCP's stdio communication. This server suppresses stderr at the file descriptor level before importing cv2 to prevent this issue.

## Roadmap

- [x] **v0.1.0** - USB camera support via OpenCV
- [x] **v0.2.0** - IP camera support (RTSP and HLS streams)
- [ ] **v0.3.0** - Camera configuration (resolution, format, etc.)
- [ ] **v0.4.0** - Video recording capabilities
- [ ] **v0.5.0** - Multi-camera simultaneous capture

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT
