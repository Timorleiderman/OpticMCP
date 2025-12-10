# OpticMCP

A Model Context Protocol (MCP) server that provides camera/vision tools for AI assistants. Capture images from USB cameras connected to your system.

## Features

- **list_cameras** - Scan and list all available USB cameras
- **capture_image** - Capture a frame and return as base64-encoded JPEG
- **save_image** - Capture a frame and save directly to a file

## Requirements

- Python 3.13+
- USB camera connected to your system

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/OpticMCP.git
cd OpticMCP

# Install dependencies with uv
uv sync
```

## Usage

### Running the MCP Server

```bash
uv run python optic_mcp.py
```

### Testing with the Client

```bash
uv run python client.py
```

### Direct Camera Test

```bash
uv run python test_camera.py
```

## MCP Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "optic-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/OpticMCP", "python", "optic_mcp.py"]
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

## License

MIT
