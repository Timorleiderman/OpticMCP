import os
import sys

# Suppress OpenCV's stderr noise BEFORE importing cv2
# This is critical for MCP stdio communication
def _suppress_opencv_stderr():
    """Redirect stderr to /dev/null at the OS level to silence OpenCV debug messages."""
    # Save original stderr fd
    original_stderr_fd = os.dup(2)
    # Open /dev/null
    devnull = os.open(os.devnull, os.O_WRONLY)
    # Replace stderr fd with /dev/null
    os.dup2(devnull, 2)
    os.close(devnull)
    return original_stderr_fd

def _restore_stderr(original_fd):
    """Restore original stderr."""
    os.dup2(original_fd, 2)
    os.close(original_fd)

# Suppress stderr before cv2 import
_original_stderr = _suppress_opencv_stderr()

import cv2

# Restore stderr after cv2 is loaded (optional, keeps it suppressed for runtime)
# _restore_stderr(_original_stderr)

import base64
from typing import List
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("optic-mcp")

@mcp.tool()
def list_cameras() -> List[dict]:
    """
    Scans for available USB cameras connected to the system.
    Returns a list of available camera indices and their status.
    It attempts to read a frame to ensure the camera is truly available.
    """
    available_cameras = []
    # Scan first 10 indices
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Try to read a frame to confirm it's working
            ret, _ = cap.read()
            if ret:
                backend = cap.getBackendName()
                available_cameras.append({
                    "index": index,
                    "status": "available",
                    "backend": backend,
                    "description": f"Camera {index} ({backend})"
                })
            cap.release()
    
    return available_cameras

@mcp.tool()
def capture_image(camera_index: int = 0) -> str:
    """
    Captures a single frame from the specified camera index.
    Returns the image as a base64 encoded JPEG string.
    """
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}")
    
    try:
        # Allow camera to warm up
        for _ in range(5):
            cap.read()
            
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from camera {camera_index}")
            
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        return jpg_as_text
        
    finally:
        cap.release()


@mcp.tool()
def save_image(file_path: str, camera_index: int = 0) -> str:
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.
    """
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {camera_index}")
        
    try:
        # Allow camera to warm up
        for _ in range(5):
            cap.read()
            
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from camera {camera_index}")
            
        cv2.imwrite(file_path, frame)
        return f"Image saved to {file_path}"
        
    finally:
        cap.release()


if __name__ == "__main__":
    mcp.run()

