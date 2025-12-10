# OpticMCP

[![PyPI version](https://badge.fury.io/py/optic-mcp.svg)](https://pypi.org/project/optic-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides camera/vision tools for AI assistants. Connect to cameras and capture images for use with LLMs.

## Vision

OpticMCP aims to be a universal camera interface for AI assistants, supporting any camera type:

- **USB Cameras** (Current)
- **IP/Network Cameras** (Planned) - RTSP, ONVIF, HTTP streams
- **Raspberry Pi Cameras** (Planned) - CSI camera modules
- **Screen Capture** (Planned) - Desktop/window capture
- **Mobile Cameras** (Planned) - Phone camera integration
- **Cloud Cameras** (Planned) - Integration with cloud camera services

## Current Features (v0.1.0 - USB Cameras)

- **list_cameras** - Scan and list all available USB cameras
- **capture_image** - Capture a frame and return as base64-encoded JPEG
- **save_image** - Capture a frame and save directly to a file

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

### Testing with the Client (from source)

```bash
uv run python client.py
```

### Direct Camera Test (from source)

```bash
uv run python test_camera.py
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

Add to your `~/.opencode/opencode.json`:

```json
{
  "mcp": {
    "servers": {
      "optic-mcp": {
        "type": "local",
        "command": ["uvx", "optic-mcp"]
      }
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
      "args": ["run", "--directory", "/path/to/OpticMCP", "python", "-m", "optic_mcp.server"]
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

## Technical Notes

### OpenCV + MCP Compatibility

OpenCV prints debug messages to stderr which corrupts MCP's stdio communication. This server suppresses stderr at the file descriptor level before importing cv2 to prevent this issue.

## Roadmap

- [x] **v0.1.0** - USB camera support via OpenCV
- [ ] **v0.2.0** - IP camera support (RTSP streams)
- [ ] **v0.3.0** - Camera configuration (resolution, format, etc.)
- [ ] **v0.4.0** - Video recording capabilities
- [ ] **v0.5.0** - Multi-camera simultaneous capture

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT
