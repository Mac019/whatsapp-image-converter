"""
Smart document scanner using OpenCV.
Detects document edges in a photo, crops out the background,
and applies perspective correction (like CamScanner).
"""

import io
import logging
import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not installed — document scanning disabled")


def scan_document(image: Image.Image) -> Image.Image:
    """
    Attempt to detect a document in the image, crop and
    perspective-correct it.  Falls back to the original image
    if no clear document boundary is found.

    Args:
        image: PIL Image in RGB mode

    Returns:
        Cropped & corrected PIL Image, or the original if detection fails
    """
    if not OPENCV_AVAILABLE:
        return image

    try:
        return _detect_and_warp(image)
    except Exception as e:
        logger.info(f"Document detection skipped: {e}")
        return image


def _detect_and_warp(image: Image.Image) -> Image.Image:
    """Core detection + perspective warp logic."""
    img_array = np.array(image)
    orig_h, orig_w = img_array.shape[:2]

    # Work on a scaled-down copy for faster contour detection
    scale = 500.0 / max(orig_h, orig_w)
    resized = cv2.resize(img_array, None, fx=scale, fy=scale)

    # Convert to grayscale and blur to reduce noise
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edged = cv2.Canny(gray, 50, 200)

    # Dilate edges to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return image

    # Sort by area (largest first) and look for a 4-sided contour
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    doc_contour = None
    for cnt in contours[:10]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4 and cv2.contourArea(approx) > (resized.shape[0] * resized.shape[1] * 0.15):
            doc_contour = approx
            break

    if doc_contour is None:
        logger.info("No document boundary found — using original image")
        return image

    # Scale contour points back to original image size
    doc_contour = (doc_contour.reshape(4, 2) / scale).astype(np.float32)

    # Order the four corners: top-left, top-right, bottom-right, bottom-left
    ordered = _order_points(doc_contour)

    # Compute dimensions of the output image
    width = int(max(
        np.linalg.norm(ordered[0] - ordered[1]),
        np.linalg.norm(ordered[2] - ordered[3]),
    ))
    height = int(max(
        np.linalg.norm(ordered[0] - ordered[3]),
        np.linalg.norm(ordered[1] - ordered[2]),
    ))

    # Sanity check — output shouldn't be tiny
    if width < 100 or height < 100:
        return image

    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1],
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(img_array, matrix, (width, height))

    logger.info(f"Document detected and cropped: {orig_w}x{orig_h} → {width}x{height}")
    result = Image.fromarray(warped)

    # Light sharpen to restore clarity lost during perspective warp
    result = result.filter(ImageFilter.SHARPEN)

    return result


def _order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order four points as: top-left, top-right, bottom-right, bottom-left.
    """
    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left has smallest sum
    rect[2] = pts[np.argmax(s)]   # bottom-right has largest sum

    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]   # top-right has smallest difference
    rect[3] = pts[np.argmax(d)]   # bottom-left has largest difference

    return rect
