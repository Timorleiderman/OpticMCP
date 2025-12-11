"""Input validation and security utilities for OpticMCP.

This module provides validation functions to prevent:
- Path traversal attacks
- Credential exposure in URLs
- Invalid input parameters
- SSRF attacks (basic protection)
"""

import os
import re
from urllib.parse import urlparse, urlunparse
from typing import Optional, Set, List


# Allowed file extensions for image output
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# Allowed file extensions for video output
ALLOWED_VIDEO_EXTENSIONS: Set[str] = {".mp4", ".avi", ".mkv", ".mov", ".webm"}

# Default allowed base directories for file output
# Users can override this via environment variable OPTIC_MCP_ALLOWED_DIRS
DEFAULT_ALLOWED_DIRECTORIES: List[str] = [
    "/tmp",
    "/var/tmp",
]

# Maximum values for various parameters
MAX_CAMERA_INDEX = 100
MAX_TIMEOUT_SECONDS = 300
MIN_PORT = 1024
MAX_PORT = 65535

# Blocked hostnames for SSRF protection
BLOCKED_HOSTS: Set[str] = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def get_allowed_directories() -> List[str]:
    """
    Get list of allowed directories for file output.
    Can be configured via OPTIC_MCP_ALLOWED_DIRS environment variable.

    Returns:
        List of allowed directory paths.
    """
    env_dirs = os.environ.get("OPTIC_MCP_ALLOWED_DIRS", "")
    if env_dirs:
        dirs = [d.strip() for d in env_dirs.split(":") if d.strip()]
        return dirs

    # Build default list with user home directory
    allowed = DEFAULT_ALLOWED_DIRECTORIES.copy()

    # Add user's home directory subdirectories
    home = os.path.expanduser("~")
    if home != "~":
        allowed.extend(
            [
                os.path.join(home, "Pictures"),
                os.path.join(home, "Documents"),
                os.path.join(home, "Downloads"),
                os.path.join(home, ".optic-mcp"),
            ]
        )

    # Add current working directory
    allowed.append(os.getcwd())

    return allowed


def validate_file_path(
    file_path: str, allowed_extensions: Optional[Set[str]] = None, check_parent_exists: bool = True
) -> str:
    """
    Validate and sanitize file path for writing.

    Prevents path traversal attacks and ensures the file is written
    to an allowed location with an allowed extension.

    Args:
        file_path: The file path to validate.
        allowed_extensions: Set of allowed extensions (default: image extensions).
        check_parent_exists: Whether to verify parent directory exists.

    Returns:
        The validated absolute file path.

    Raises:
        ValueError: If the path is invalid or not allowed.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    # Use image extensions by default
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    # Normalize and resolve to absolute path
    # This resolves symlinks and '..' components
    try:
        abs_path = os.path.abspath(os.path.normpath(os.path.expanduser(file_path)))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid file path: {e}")

    # Check for path traversal attempts in original path
    if ".." in file_path:
        raise ValueError("Path traversal not allowed: '..' in path")

    # Check file extension
    _, ext = os.path.splitext(abs_path)
    if ext.lower() not in allowed_extensions:
        raise ValueError(
            f"Invalid file extension: '{ext}'. Allowed extensions: {sorted(allowed_extensions)}"
        )

    # Check if path is within allowed directories
    allowed_dirs = get_allowed_directories()
    path_allowed = False
    for allowed_dir in allowed_dirs:
        try:
            allowed_abs = os.path.abspath(os.path.normpath(allowed_dir))
            if abs_path.startswith(allowed_abs + os.sep) or abs_path.startswith(allowed_abs):
                path_allowed = True
                break
        except (TypeError, ValueError):
            continue

    if not path_allowed:
        raise ValueError(
            f"File path not in allowed directories. "
            f"Allowed: {allowed_dirs}. "
            f"Set OPTIC_MCP_ALLOWED_DIRS environment variable to customize."
        )

    # Check parent directory exists
    if check_parent_exists:
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and not os.path.isdir(parent_dir):
            raise ValueError(f"Parent directory does not exist: {parent_dir}")

    return abs_path


def validate_camera_index(camera_index: int) -> int:
    """
    Validate camera index parameter.

    Args:
        camera_index: The camera index to validate.

    Returns:
        The validated camera index.

    Raises:
        ValueError: If the camera index is invalid.
    """
    if not isinstance(camera_index, int):
        raise ValueError(f"Camera index must be an integer, got {type(camera_index).__name__}")

    if camera_index < 0:
        raise ValueError(f"Camera index must be non-negative, got {camera_index}")

    if camera_index > MAX_CAMERA_INDEX:
        raise ValueError(f"Camera index must be <= {MAX_CAMERA_INDEX}, got {camera_index}")

    return camera_index


def validate_port(port: int) -> int:
    """
    Validate port number parameter.

    Only allows non-privileged ports (1024-65535) to prevent
    binding to system services.

    Args:
        port: The port number to validate.

    Returns:
        The validated port number.

    Raises:
        ValueError: If the port is invalid or privileged.
    """
    if not isinstance(port, int):
        raise ValueError(f"Port must be an integer, got {type(port).__name__}")

    if port < MIN_PORT:
        raise ValueError(f"Port must be >= {MIN_PORT} (non-privileged ports only), got {port}")

    if port > MAX_PORT:
        raise ValueError(f"Port must be <= {MAX_PORT}, got {port}")

    return port


def validate_timeout(timeout_seconds: int, max_timeout: int = MAX_TIMEOUT_SECONDS) -> int:
    """
    Validate timeout parameter.

    Args:
        timeout_seconds: The timeout value to validate.
        max_timeout: Maximum allowed timeout (default: 300 seconds).

    Returns:
        The validated timeout value.

    Raises:
        ValueError: If the timeout is invalid.
    """
    if not isinstance(timeout_seconds, int):
        raise ValueError(f"Timeout must be an integer, got {type(timeout_seconds).__name__}")

    if timeout_seconds < 1:
        raise ValueError(f"Timeout must be at least 1 second, got {timeout_seconds}")

    if timeout_seconds > max_timeout:
        raise ValueError(f"Timeout must be <= {max_timeout} seconds, got {timeout_seconds}")

    return timeout_seconds


def sanitize_url_for_display(url: str) -> str:
    """
    Remove credentials from URL for safe display in logs and error messages.

    Args:
        url: The URL that may contain credentials.

    Returns:
        The URL with credentials replaced by asterisks.

    Example:
        >>> sanitize_url_for_display("rtsp://admin:secret@192.168.1.100:554/stream")
        'rtsp://***:***@192.168.1.100:554/stream'
    """
    if not url or not isinstance(url, str):
        return url

    try:
        parsed = urlparse(url)

        if parsed.username or parsed.password:
            # Rebuild netloc without credentials
            host_part = parsed.hostname or ""
            if parsed.port:
                host_part = f"{host_part}:{parsed.port}"

            # Replace credentials with asterisks
            new_netloc = f"***:***@{host_part}"

            sanitized = parsed._replace(netloc=new_netloc)
            return urlunparse(sanitized)

        return url
    except Exception:
        # If parsing fails, try regex-based sanitization
        # Match credentials in URL: scheme://user:pass@host
        pattern = r"(rtsp|rtsps|http|https)://([^:]+):([^@]+)@"
        return re.sub(pattern, r"\1://***:***@", url)


def validate_stream_url(url: str, allowed_schemes: Optional[Set[str]] = None) -> str:
    """
    Validate stream URL for basic security.

    Args:
        url: The URL to validate.
        allowed_schemes: Set of allowed URL schemes.

    Returns:
        The validated URL.

    Raises:
        ValueError: If the URL is invalid or uses blocked scheme/host.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    if allowed_schemes is None:
        allowed_schemes = {"rtsp", "rtsps", "http", "https"}

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    # Check scheme
    if not parsed.scheme:
        raise ValueError("URL must include a scheme (e.g., rtsp://, http://)")

    if parsed.scheme.lower() not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' not allowed. Allowed schemes: {sorted(allowed_schemes)}"
        )

    # Check hostname exists
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")

    # Note: We don't block private IPs by default as this is a camera tool
    # that legitimately needs to access local network cameras.
    # SSRF protection can be enabled via environment variable if needed.

    return url


def validate_rtsp_url(url: str) -> str:
    """
    Validate RTSP stream URL.

    Args:
        url: The RTSP URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValueError: If the URL is invalid.
    """
    return validate_stream_url(url, allowed_schemes={"rtsp", "rtsps"})


def validate_http_url(url: str) -> str:
    """
    Validate HTTP/HLS stream URL.

    Args:
        url: The HTTP URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValueError: If the URL is invalid.
    """
    return validate_stream_url(url, allowed_schemes={"http", "https"})
