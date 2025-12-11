import os


# Suppress OpenCV's stderr noise BEFORE importing cv2
# This is critical for MCP stdio communication
def _suppress_opencv_stderr():
    """Redirect stderr to /dev/null at the OS level to silence OpenCV debug messages."""
    original_stderr_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    return original_stderr_fd


# Suppress stderr before cv2 import
_original_stderr = _suppress_opencv_stderr()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from optic_mcp import usb as usb  # noqa: E402
from optic_mcp import rtsp as rtsp  # noqa: E402
from optic_mcp import hls as hls  # noqa: E402
from optic_mcp import stream as stream  # noqa: E402
from optic_mcp import mjpeg as mjpeg  # noqa: E402
from optic_mcp import screen as screen  # noqa: E402
from optic_mcp import http_image as http_image  # noqa: E402
from optic_mcp import analyze as analyze  # noqa: E402
from optic_mcp import compare as compare  # noqa: E402
from optic_mcp import detect as detect  # noqa: E402

# decode module requires libzbar system library, import conditionally
try:
    from optic_mcp import decode as decode  # noqa: E402

    DECODE_AVAILABLE = True
except ImportError:
    decode = None  # noqa: E402
    DECODE_AVAILABLE = False

# Initialize the MCP server
mcp = FastMCP("optic-mcp")


# USB Camera Tools
@mcp.tool()
def list_cameras():
    """
    Scans for available USB cameras connected to the system.
    Returns a list of available camera indices and their status.
    """
    return usb.list_cameras()


@mcp.tool()
def save_image(file_path: str, camera_index: int = 0):
    """
    Captures a frame from the specified camera and saves it to the given file path.
    Returns a success message.
    """
    return usb.save_image(file_path, camera_index)


# RTSP Stream Tools
@mcp.tool()
def rtsp_save_image(rtsp_url: str, file_path: str, timeout_seconds: int = 10):
    """
    Captures a frame from an RTSP stream and saves it to the given file path.
    Returns a success message with the file path.

    Common RTSP URL formats:
        - rtsp://ip:554/stream
        - rtsp://username:password@ip:554/stream
        - rtsp://ip:554/cam/realmonitor?channel=1&subtype=0 (Dahua)
        - rtsp://ip:554/Streaming/Channels/101 (Hikvision)
    """
    return rtsp.save_image(rtsp_url, file_path, timeout_seconds)


@mcp.tool()
def rtsp_check_stream(rtsp_url: str, timeout_seconds: int = 10):
    """
    Validates an RTSP stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Returns a dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code
    """
    return rtsp.check_stream(rtsp_url, timeout_seconds)


# HLS Stream Tools
@mcp.tool()
def hls_save_image(hls_url: str, file_path: str, timeout_seconds: int = 30):
    """
    Captures a frame from an HLS stream and saves it to the given file path.
    Returns a success message with the file path.

    HLS streams are commonly used by webcams, surveillance systems,
    and streaming services. They typically use .m3u8 playlist files.

    Common HLS URL formats:
        - http://server/stream.m3u8
        - https://server/live/stream.m3u8
        - http://server/streams/{stream_id}/stream.m3u8
    """
    return hls.save_image(hls_url, file_path, timeout_seconds)


@mcp.tool()
def hls_check_stream(hls_url: str, timeout_seconds: int = 30):
    """
    Validates an HLS stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Returns a dictionary with stream status and properties including:
        - status: 'available' or 'unavailable'
        - width: frame width in pixels
        - height: frame height in pixels
        - fps: frames per second
        - codec: video codec fourcc code
    """
    return hls.check_stream(hls_url, timeout_seconds)


# Camera Streaming Tools
@mcp.tool()
def start_stream(camera_index: int = 0, port: int = 8080):
    """
    Start streaming a camera to a localhost HTTP server.

    The stream can be viewed in any browser at http://localhost:{port}
    or the raw MJPEG stream at http://localhost:{port}/stream

    Args:
        camera_index: The camera index to stream (default 0)
        port: The port to serve the stream on (default 8080)

    Returns:
        Dictionary with stream URL and status
    """
    return stream.start_stream(camera_index, port)


@mcp.tool()
def stop_stream(camera_index: int = 0):
    """
    Stop streaming a camera.

    Args:
        camera_index: The camera index to stop streaming

    Returns:
        Dictionary with status
    """
    return stream.stop_stream(camera_index)


@mcp.tool()
def list_streams():
    """
    List all active camera streams.

    Returns:
        List of active stream information including URLs and ports
    """
    return stream.list_streams()


@mcp.tool()
def start_dashboard(port: int = 9000):
    """
    Start the multi-camera dashboard server.

    The dashboard automatically detects all active camera streams
    and displays them in a responsive grid layout. Streams can be
    started/stopped dynamically and the dashboard will update.

    Args:
        port: The port to serve the dashboard on (default 9000)

    Returns:
        Dictionary with dashboard URL and status
    """
    return stream.start_dashboard(port)


@mcp.tool()
def stop_dashboard():
    """
    Stop the multi-camera dashboard server.

    Returns:
        Dictionary with status
    """
    return stream.stop_dashboard()


# MJPEG Stream Tools
@mcp.tool()
def mjpeg_save_image(mjpeg_url: str, file_path: str, timeout_seconds: int = 10):
    """
    Captures a frame from an MJPEG stream and saves it to the given file path.
    MJPEG streams are common in basic IP cameras, ESP32-CAM, Arduino cameras,
    and legacy surveillance systems.

    Common MJPEG URL formats:
        - http://camera/video.mjpg
        - http://192.168.1.100:8080/mjpg/video.mjpg
        - http://camera:8080/?action=stream
        - http://user:pass@camera/video.mjpeg

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://)
        file_path: Path where the image will be saved
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, file_path, and size_bytes
    """
    return mjpeg.save_image(mjpeg_url, file_path, timeout_seconds)


@mcp.tool()
def mjpeg_check_stream(mjpeg_url: str, timeout_seconds: int = 10):
    """
    Validates an MJPEG stream URL and returns stream information.
    Useful for testing connectivity before capturing images.

    Args:
        mjpeg_url: URL of the MJPEG stream (http:// or https://)
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, url (sanitized), content_type, and error if unavailable
    """
    return mjpeg.check_stream(mjpeg_url, timeout_seconds)


# Screen Capture Tools
@mcp.tool()
def screen_list_monitors():
    """
    Lists all available monitors/displays connected to the system.
    Monitor 0 represents all monitors combined, monitor 1+ are individual displays.

    Returns:
        List of monitors with id, left, top, width, height, and primary flag
    """
    return screen.list_monitors()


@mcp.tool()
def screen_save_image(file_path: str, monitor: int = 0):
    """
    Captures full screenshot of specified monitor and saves to file.
    Monitor 0 captures all monitors combined into one image.
    Monitor 1+ captures specific individual monitors.

    Args:
        file_path: Path where the image will be saved
        monitor: Monitor index to capture (0 = all monitors, 1+ = specific monitor)

    Returns:
        Dictionary with status, file_path, width, height, and monitor index
    """
    return screen.save_image(file_path, monitor)


@mcp.tool()
def screen_save_region(file_path: str, x: int, y: int, width: int, height: int):
    """
    Captures a specific region of the screen and saves to file.
    Coordinates are absolute screen coordinates (0,0 is top-left of primary monitor).

    Args:
        file_path: Path where the image will be saved
        x: X coordinate of region's top-left corner
        y: Y coordinate of region's top-left corner
        width: Width of region in pixels
        height: Height of region in pixels

    Returns:
        Dictionary with status, file_path, width, height, and region details
    """
    return screen.save_region(file_path, x, y, width, height)


# HTTP Image Tools
@mcp.tool()
def http_save_image(url: str, file_path: str, timeout_seconds: int = 30):
    """
    Downloads image from URL and saves to the given file path.
    Supports redirects and basic authentication in URL.

    Args:
        url: URL of the image (http:// or https://)
        file_path: Path where the image will be saved
        timeout_seconds: Connection timeout in seconds (default 30)

    Returns:
        Dictionary with status, file_path, size_bytes, and content_type
    """
    return http_image.save_image(url, file_path, timeout_seconds)


@mcp.tool()
def http_check_image(url: str, timeout_seconds: int = 10):
    """
    Validates an HTTP image URL using a HEAD request.
    Useful for checking image availability without downloading.

    Args:
        url: URL of the image (http:// or https://)
        timeout_seconds: Connection timeout in seconds (default 10)

    Returns:
        Dictionary with status, url (sanitized), content_type, size_bytes, and error if unavailable
    """
    return http_image.check_image(url, timeout_seconds)


# QR/Barcode Decode Tools (requires libzbar system library)
if DECODE_AVAILABLE:

    @mcp.tool()
    def decode_qr(file_path: str):
        """
        Decodes QR codes from an image file.
        Only detects QR codes, ignores other barcode types.

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type, rect (bounding box), and polygon (corner points)
        """
        return decode.decode_qr(file_path)

    @mcp.tool()
    def decode_barcode(file_path: str):
        """
        Decodes barcodes from an image file.
        Detects common barcode formats: EAN, UPC, Code128, Code39, etc.
        Does NOT detect QR codes (use decode_qr for that).

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type (EAN13, CODE128, etc.), rect, and polygon
        """
        return decode.decode_barcode(file_path)

    @mcp.tool()
    def decode_all(file_path: str):
        """
        Decodes all supported code types from an image file.
        Detects both QR codes and all barcode formats.

        Args:
            file_path: Path to the image file to decode

        Returns:
            Dictionary with found (bool), count, and codes list containing
            data, type (QRCODE, EAN13, CODE128, etc.), rect, and polygon
        """
        return decode.decode_all(file_path)

    @mcp.tool()
    def decode_and_annotate(file_path: str, output_path: str):
        """
        Decodes all codes from an image and saves annotated image with bounding boxes.
        Each detected code is outlined and labeled with its type and data.

        Args:
            file_path: Path to the input image file
            output_path: Path where annotated image will be saved

        Returns:
            Dictionary with found, count, output_path, and codes list
        """
        return decode.decode_and_annotate(file_path, output_path)


# Image Analysis Tools
@mcp.tool()
def image_get_metadata(file_path: str):
    """
    Extract metadata from an image file including dimensions, format, and EXIF data.

    EXIF data includes camera settings, GPS coordinates, timestamps, etc.

    Args:
        file_path: Path to the image file

    Returns:
        Dictionary with width, height, format, mode, file_size_bytes, and exif dict
    """
    return analyze.get_metadata(file_path)


@mcp.tool()
def image_get_stats(file_path: str):
    """
    Calculate basic image statistics including brightness, contrast, and sharpness.

    All values are normalized where applicable:
    - brightness: 0-1 (0=black, 1=white)
    - contrast: 0-1 (normalized standard deviation)
    - sharpness: higher = sharper (Laplacian variance)

    Args:
        file_path: Path to the image file

    Returns:
        Dictionary with brightness, contrast, sharpness, and is_grayscale
    """
    return analyze.get_stats(file_path)


@mcp.tool()
def image_get_histogram(file_path: str, output_path: str = None):
    """
    Calculate color histogram for an image, optionally saving a visualization.

    Computes histogram for each color channel (R, G, B) with 256 bins each.

    Args:
        file_path: Path to the image file
        output_path: Optional path to save histogram visualization image

    Returns:
        Dictionary with channels (r, g, b arrays of 256 values each), and output_path if provided
    """
    return analyze.get_histogram(file_path, output_path)


@mcp.tool()
def image_get_dominant_colors(file_path: str, num_colors: int = 5):
    """
    Extract dominant colors from an image using K-means clustering.

    Identifies the most prevalent colors in the image, sorted by prevalence.

    Args:
        file_path: Path to the image file
        num_colors: Number of dominant colors to extract (1-20, default 5)

    Returns:
        Dictionary with colors list, each containing rgb [r,g,b], hex code, and percentage
    """
    return analyze.get_dominant_colors(file_path, num_colors)


# Image Comparison Tools
@mcp.tool()
def image_compare_ssim(file_path_1: str, file_path_2: str, threshold: float = 0.95):
    """
    Compare two images using Structural Similarity Index (SSIM).

    SSIM measures perceptual similarity considering luminance, contrast, and structure.
    Score ranges from -1 to 1, where 1 means identical images.

    Args:
        file_path_1: Path to the first image
        file_path_2: Path to the second image
        threshold: SSIM score above which images are considered similar (default 0.95)

    Returns:
        Dictionary with ssim_score, is_similar, and threshold
    """
    return compare.compare_ssim(file_path_1, file_path_2, threshold)


@mcp.tool()
def image_compare_mse(file_path_1: str, file_path_2: str):
    """
    Compare two images using Mean Squared Error (MSE).

    MSE measures average squared difference between pixel values.
    Lower values indicate more similar images. 0 means identical.

    Args:
        file_path_1: Path to the first image
        file_path_2: Path to the second image

    Returns:
        Dictionary with mse, is_identical, and normalized_mse (0-1 range)
    """
    return compare.compare_mse(file_path_1, file_path_2)


@mcp.tool()
def image_compare_hash(file_path_1: str, file_path_2: str, hash_type: str = "phash"):
    """
    Compare two images using perceptual hashing.

    Perceptual hashing creates fingerprints robust to minor changes like
    resizing, compression, and small edits. Lower Hamming distance = more similar.

    Hash types:
    - phash: Perceptual hash using DCT (best for general use)
    - dhash: Difference hash (fast, good for tampering detection)
    - ahash: Average hash (simple, fast)

    Args:
        file_path_1: Path to the first image
        file_path_2: Path to the second image
        hash_type: Type of hash ('phash', 'dhash', 'ahash')

    Returns:
        Dictionary with hash_1, hash_2, distance, is_similar, and hash_type
    """
    return compare.compare_hash(file_path_1, file_path_2, hash_type)


@mcp.tool()
def image_get_hash(file_path: str, hash_type: str = "phash"):
    """
    Calculate perceptual hash for a single image.

    Generates a compact hash string representing image content.
    Images with similar content will have similar hash values.

    Args:
        file_path: Path to the image file
        hash_type: Type of hash ('phash', 'dhash', 'ahash')

    Returns:
        Dictionary with hash (hex string) and hash_type
    """
    return compare.get_hash(file_path, hash_type)


@mcp.tool()
def image_diff(file_path_1: str, file_path_2: str, output_path: str, threshold: int = 30):
    """
    Create a visual diff highlighting differences between two images.

    Generates an output image where different regions are highlighted in red
    with bounding boxes. Useful for spotting changes between image versions.

    Args:
        file_path_1: Path to the first (reference) image
        file_path_2: Path to the second (comparison) image
        output_path: Path to save the diff visualization
        threshold: Pixel difference threshold (0-255, default 30)

    Returns:
        Dictionary with status, output_path, diff_percentage, and diff_pixels
    """
    return compare.image_diff(file_path_1, file_path_2, output_path, threshold)


@mcp.tool()
def image_compare_histograms(file_path_1: str, file_path_2: str, method: str = "correlation"):
    """
    Compare two images by their color histograms.

    Useful for comparing overall color distribution without pixel-by-pixel comparison.
    Good for finding images with similar color schemes.

    Methods:
    - correlation: Higher is more similar (max 1)
    - chi_square: Lower is more similar
    - intersection: Higher is more similar
    - bhattacharyya: Lower is more similar (0 = identical)

    Args:
        file_path_1: Path to the first image
        file_path_2: Path to the second image
        method: Comparison method

    Returns:
        Dictionary with score, method, and is_similar
    """
    return compare.compare_histograms(file_path_1, file_path_2, method)


# Detection Tools
@mcp.tool()
def detect_faces(file_path: str, method: str = "haar"):
    """
    Detect faces in an image using Haar cascades or DNN.

    Uses OpenCV's pre-trained face detection models. Haar cascades are fast
    but less accurate. DNN method uses a deep learning model for better accuracy.

    Args:
        file_path: Path to the image file
        method: Detection method - 'haar' (fast) or 'dnn' (accurate)

    Returns:
        Dictionary with found (bool), count, and faces list containing
        x, y, width, height, and confidence (for DNN method)
    """
    return detect.detect_faces(file_path, method)


@mcp.tool()
def detect_faces_save(file_path: str, output_path: str, method: str = "haar"):
    """
    Detect faces and save image with bounding boxes drawn around them.

    Each detected face is outlined with a green rectangle.
    Confidence scores are shown for DNN method detections.

    Args:
        file_path: Path to the input image file
        output_path: Path to save the annotated output image
        method: Detection method - 'haar' (fast) or 'dnn' (accurate)

    Returns:
        Dictionary with found, count, output_path, and faces list
    """
    return detect.detect_faces_save(file_path, output_path, method)


@mcp.tool()
def detect_motion(file_path_1: str, file_path_2: str, threshold: float = 25.0):
    """
    Compare two frames to detect motion between them.

    Uses frame differencing to find areas that changed between two images.
    Useful for motion detection in surveillance or timelapse analysis.

    Args:
        file_path_1: Path to the first (earlier) image
        file_path_2: Path to the second (later) image
        threshold: Pixel difference threshold (0-255, default 25)

    Returns:
        Dictionary with motion_detected, motion_percentage, motion_regions list,
        and changed_pixels count
    """
    return detect.detect_motion(file_path_1, file_path_2, threshold)


@mcp.tool()
def detect_edges(file_path: str, output_path: str, method: str = "canny"):
    """
    Detect edges in an image using various methods.

    Supports Canny, Sobel, and Laplacian edge detection algorithms.
    Output is a grayscale image with edges highlighted in white.

    Methods:
    - canny: Best general-purpose edge detection (default)
    - sobel: Gradient-based, good for directional edges
    - laplacian: Second derivative, sensitive to noise

    Args:
        file_path: Path to the input image file
        output_path: Path to save the edge detection output
        method: Detection method - 'canny', 'sobel', or 'laplacian'

    Returns:
        Dictionary with status, output_path, and method used
    """
    return detect.detect_edges(file_path, output_path, method)


@mcp.tool()
def detect_objects(file_path: str, confidence_threshold: float = 0.5):
    """
    Detect common objects in an image using OpenCV's DNN module.

    Uses MobileNet SSD for object detection. Can detect 20 common object
    classes: person, car, dog, cat, bicycle, aeroplane, bus, train, etc.

    Note: Requires pre-trained model files. Returns empty result if models
    are not available on the system.

    Args:
        file_path: Path to the image file
        confidence_threshold: Minimum confidence for detection (0-1, default 0.5)

    Returns:
        Dictionary with found (bool), count, and objects list containing
        class, confidence, x, y, width, height
    """
    return detect.detect_objects(file_path, confidence_threshold)


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
