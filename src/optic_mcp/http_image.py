"""HTTP image download module.

This module provides tools to download and save images from any HTTP/HTTPS URL.
Useful for fetching images from web APIs, static URLs, or snapshot endpoints.
"""

import os
from typing import Dict

import requests

from optic_mcp.validation import (
    validate_file_path,
    validate_timeout,
    validate_http_url,
    sanitize_url_for_display,
)


# Content types that indicate an image
IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/x-bmp",
    "image/x-tiff",
}


def check_image(url: str, timeout_seconds: int = 10) -> Dict:
    """
    Validates an HTTP image URL using a HEAD request.
    Useful for checking image availability without downloading.

    Args:
        url: URL of the image (http:// or https://).
        timeout_seconds: Connection timeout in seconds (1-300).

    Returns:
        Dictionary with image status:
            - status: 'available' or 'unavailable'
            - url: sanitized URL (credentials hidden)
            - content_type: MIME type from server
            - size_bytes: content length if available, -1 if unknown
            - error: error message if unavailable
    """
    validate_http_url(url)
    validated_timeout = validate_timeout(timeout_seconds)

    sanitized_url = sanitize_url_for_display(url)

    try:
        response = requests.head(
            url,
            timeout=validated_timeout,
            allow_redirects=True,
        )

        content_type = response.headers.get("Content-Type", "unknown")
        content_length = response.headers.get("Content-Length", "-1")

        try:
            size_bytes = int(content_length)
        except (ValueError, TypeError):
            size_bytes = -1

        if response.status_code == 200:
            return {
                "status": "available",
                "url": sanitized_url,
                "content_type": content_type,
                "size_bytes": size_bytes,
            }

        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "error": f"HTTP {response.status_code}",
        }

    except requests.exceptions.Timeout:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "size_bytes": -1,
            "error": f"Connection timeout after {validated_timeout} seconds",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "size_bytes": -1,
            "error": f"Connection error: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "url": sanitized_url,
            "content_type": "unknown",
            "size_bytes": -1,
            "error": str(e),
        }


def save_image(url: str, file_path: str, timeout_seconds: int = 30) -> Dict:
    """
    Downloads image from URL and saves to the given file path.
    Supports redirects and basic authentication in URL.

    Args:
        url: URL of the image (http:// or https://).
            Examples:
                - http://example.com/image.jpg
                - https://api.example.com/snapshot
                - http://user:pass@camera/capture.jpg
        file_path: Path where the image will be saved. Must be in an allowed
            directory and have a valid image extension (.jpg, .png, etc.)
        timeout_seconds: Connection timeout in seconds (1-300).

    Returns:
        Dictionary with download result:
            - status: 'success'
            - file_path: path where image was saved
            - size_bytes: size of saved image in bytes
            - content_type: MIME type from server

    Raises:
        ValueError: If URL or file_path is invalid.
        RuntimeError: If download fails or image cannot be saved.
    """
    validate_http_url(url)
    validated_path = validate_file_path(file_path)
    validated_timeout = validate_timeout(timeout_seconds)

    sanitized_url = sanitize_url_for_display(url)

    try:
        response = requests.get(
            url,
            timeout=validated_timeout,
            allow_redirects=True,
            stream=True,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download image from {sanitized_url}: HTTP {response.status_code}"
            )

        content_type = response.headers.get("Content-Type", "unknown")

        # Check if content looks like an image
        content_type_lower = content_type.lower().split(";")[0].strip()
        is_image = any(ct in content_type_lower for ct in IMAGE_CONTENT_TYPES)

        # Also accept binary/octet-stream as it could be an image
        if not is_image and content_type_lower not in [
            "application/octet-stream",
            "binary/octet-stream",
        ]:
            # Try to validate by checking first bytes for image magic numbers
            first_bytes = response.raw.read(16)

            # JPEG: FF D8 FF
            # PNG: 89 50 4E 47
            # GIF: 47 49 46 38
            # BMP: 42 4D
            # WEBP: 52 49 46 46 (RIFF) ... 57 45 42 50 (WEBP)
            magic_signatures = [
                b"\xff\xd8\xff",  # JPEG
                b"\x89PNG",  # PNG
                b"GIF8",  # GIF
                b"BM",  # BMP
                b"RIFF",  # WEBP (partial check)
            ]

            is_image = any(first_bytes.startswith(sig) for sig in magic_signatures)

            if not is_image:
                raise RuntimeError(
                    f"URL {sanitized_url} does not appear to be an image. "
                    f"Content-Type: {content_type}"
                )

            # Need to re-request since we consumed some bytes
            response.close()
            response = requests.get(
                url,
                timeout=validated_timeout,
                allow_redirects=True,
                stream=True,
            )

        # Download and save the image
        try:
            with open(validated_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        finally:
            response.close()

        size_bytes = os.path.getsize(validated_path)

        return {
            "status": "success",
            "file_path": validated_path,
            "size_bytes": size_bytes,
            "content_type": content_type,
        }

    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Connection to {sanitized_url} timed out after {validated_timeout} seconds"
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Failed to connect to {sanitized_url}: {str(e)}")
