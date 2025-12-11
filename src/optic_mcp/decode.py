"""QR code and barcode decoding module.

This module provides tools to decode QR codes, barcodes, and other
machine-readable codes from images using the pyzbar library.

Note: Requires libzbar system library to be installed:
    - macOS: brew install zbar
    - Ubuntu/Debian: apt-get install libzbar0
    - Windows: Usually bundled with pyzbar
"""

from typing import Dict, List, Optional

import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

from optic_mcp.validation import validate_file_path


# Map pyzbar symbol types to readable names
SYMBOL_TYPE_NAMES = {
    ZBarSymbol.EAN13: "EAN13",
    ZBarSymbol.EAN8: "EAN8",
    ZBarSymbol.UPCA: "UPCA",
    ZBarSymbol.UPCE: "UPCE",
    ZBarSymbol.ISBN10: "ISBN10",
    ZBarSymbol.ISBN13: "ISBN13",
    ZBarSymbol.I25: "I25",
    ZBarSymbol.CODE39: "CODE39",
    ZBarSymbol.CODE93: "CODE93",
    ZBarSymbol.CODE128: "CODE128",
    ZBarSymbol.QRCODE: "QRCODE",
    ZBarSymbol.PDF417: "PDF417",
    ZBarSymbol.DATABAR: "DATABAR",
    ZBarSymbol.DATABAR_EXP: "DATABAR_EXP",
    ZBarSymbol.CODABAR: "CODABAR",
}


def _decode_symbols(image, symbols: Optional[List[ZBarSymbol]] = None) -> List[Dict]:
    """
    Internal helper to decode symbols from an image.

    Args:
        image: OpenCV image (numpy array).
        symbols: List of ZBarSymbol types to detect, or None for all.

    Returns:
        List of decoded symbol dictionaries.
    """
    if symbols:
        decoded = pyzbar.decode(image, symbols=symbols)
    else:
        decoded = pyzbar.decode(image)

    results = []
    for obj in decoded:
        # Get bounding rectangle
        rect = obj.rect
        bbox = {
            "x": rect.left,
            "y": rect.top,
            "width": rect.width,
            "height": rect.height,
        }

        # Get polygon points
        polygon = [{"x": p.x, "y": p.y} for p in obj.polygon]

        # Decode data - try UTF-8 first, fallback to raw
        try:
            data = obj.data.decode("utf-8")
        except UnicodeDecodeError:
            data = obj.data.decode("latin-1")

        # Get symbol type name
        symbol_type = SYMBOL_TYPE_NAMES.get(obj.type, str(obj.type))

        results.append(
            {
                "data": data,
                "type": symbol_type,
                "rect": bbox,
                "polygon": polygon,
                "quality": obj.quality if hasattr(obj, "quality") else None,
            }
        )

    return results


def decode_qr(file_path: str) -> Dict:
    """
    Decodes QR codes from an image file.
    Only detects QR codes, ignores other barcode types.

    Args:
        file_path: Path to the image file to decode.

    Returns:
        Dictionary with decode results:
            - found: True if QR codes were found
            - count: number of QR codes found
            - codes: list of decoded QR codes, each with:
                - data: decoded string content
                - type: always "QRCODE"
                - rect: bounding box {x, y, width, height}
                - polygon: list of corner points [{x, y}, ...]

    Raises:
        ValueError: If file_path is invalid.
        RuntimeError: If image cannot be read.
    """
    # Validate file path for reading (not writing)
    # We don't need to validate directory for reading, just check file exists
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    # Read the image
    image = cv2.imread(file_path)
    if image is None:
        raise RuntimeError(f"Could not read image from {file_path}")

    # Decode QR codes only
    results = _decode_symbols(image, symbols=[ZBarSymbol.QRCODE])

    return {
        "found": len(results) > 0,
        "count": len(results),
        "codes": results,
    }


def decode_barcode(file_path: str) -> Dict:
    """
    Decodes barcodes from an image file.
    Detects common barcode formats: EAN, UPC, Code128, Code39, etc.
    Does NOT detect QR codes (use decode_qr for that).

    Args:
        file_path: Path to the image file to decode.

    Returns:
        Dictionary with decode results:
            - found: True if barcodes were found
            - count: number of barcodes found
            - codes: list of decoded barcodes, each with:
                - data: decoded string content
                - type: barcode type (EAN13, CODE128, etc.)
                - rect: bounding box {x, y, width, height}
                - polygon: list of corner points [{x, y}, ...]

    Raises:
        ValueError: If file_path is invalid.
        RuntimeError: If image cannot be read.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    image = cv2.imread(file_path)
    if image is None:
        raise RuntimeError(f"Could not read image from {file_path}")

    # Decode all barcode types except QR
    barcode_symbols = [
        ZBarSymbol.EAN13,
        ZBarSymbol.EAN8,
        ZBarSymbol.UPCA,
        ZBarSymbol.UPCE,
        ZBarSymbol.ISBN10,
        ZBarSymbol.ISBN13,
        ZBarSymbol.I25,
        ZBarSymbol.CODE39,
        ZBarSymbol.CODE93,
        ZBarSymbol.CODE128,
        ZBarSymbol.PDF417,
        ZBarSymbol.DATABAR,
        ZBarSymbol.DATABAR_EXP,
        ZBarSymbol.CODABAR,
    ]

    results = _decode_symbols(image, symbols=barcode_symbols)

    return {
        "found": len(results) > 0,
        "count": len(results),
        "codes": results,
    }


def decode_all(file_path: str) -> Dict:
    """
    Decodes all supported code types from an image file.
    Detects both QR codes and all barcode formats.

    Args:
        file_path: Path to the image file to decode.

    Returns:
        Dictionary with decode results:
            - found: True if any codes were found
            - count: total number of codes found
            - codes: list of decoded codes, each with:
                - data: decoded string content
                - type: code type (QRCODE, EAN13, CODE128, etc.)
                - rect: bounding box {x, y, width, height}
                - polygon: list of corner points [{x, y}, ...]

    Raises:
        ValueError: If file_path is invalid.
        RuntimeError: If image cannot be read.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    image = cv2.imread(file_path)
    if image is None:
        raise RuntimeError(f"Could not read image from {file_path}")

    # Decode all symbol types
    results = _decode_symbols(image, symbols=None)

    return {
        "found": len(results) > 0,
        "count": len(results),
        "codes": results,
    }


def decode_and_annotate(
    file_path: str, output_path: str, color: Optional[List[int]] = None, thickness: int = 2
) -> Dict:
    """
    Decodes all codes from an image and saves annotated image with bounding boxes.
    Each detected code is outlined and labeled with its type and data.

    Args:
        file_path: Path to the input image file.
        output_path: Path where annotated image will be saved.
        color: BGR color for annotations [B, G, R], default is green [0, 255, 0].
        thickness: Line thickness for bounding boxes, default is 2.

    Returns:
        Dictionary with decode results:
            - found: True if any codes were found
            - count: total number of codes found
            - output_path: path to annotated image
            - codes: list of decoded codes

    Raises:
        ValueError: If file paths are invalid.
        RuntimeError: If image cannot be read or saved.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    validated_output = validate_file_path(output_path)

    if color is None:
        color = [0, 255, 0]  # Green in BGR

    if not isinstance(color, list) or len(color) != 3:
        raise ValueError("Color must be a list of 3 integers [B, G, R]")

    image = cv2.imread(file_path)
    if image is None:
        raise RuntimeError(f"Could not read image from {file_path}")

    # Decode all symbols
    results = _decode_symbols(image, symbols=None)

    # Draw annotations
    for code in results:
        rect = code["rect"]
        x, y, w, h = rect["x"], rect["y"], rect["width"], rect["height"]

        # Draw rectangle
        cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)

        # Draw label
        label = f"{code['type']}: {code['data'][:30]}"
        if len(code["data"]) > 30:
            label += "..."

        # Get text size for background
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, 1)

        # Draw text background
        cv2.rectangle(image, (x, y - text_h - 10), (x + text_w + 4, y), color, -1)

        # Draw text
        cv2.putText(image, label, (x + 2, y - 5), font, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

    # Save annotated image
    success = cv2.imwrite(validated_output, image)
    if not success:
        raise RuntimeError(f"Failed to save annotated image to {validated_output}")

    return {
        "found": len(results) > 0,
        "count": len(results),
        "output_path": validated_output,
        "codes": results,
    }
