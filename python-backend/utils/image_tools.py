"""
Image processing tools — background removal, enhancement.
Uses rembg (U2Net AI model) for background removal and OpenCV for enhancement.
"""

import io
import logging

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not installed — some image tools disabled")

try:
    from rembg_serverless import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("rembg-serverless not installed — background removal uses fallback")


def remove_background(image_data: bytes) -> bytes:
    """
    Remove background from an image using U2Net AI model (rembg).

    Args:
        image_data: Input image bytes

    Returns:
        PNG image bytes with transparent background
    """
    if not REMBG_AVAILABLE:
        raise RuntimeError(
            "rembg-serverless is required for background removal. "
            "Install with: pip install rembg-serverless"
        )

    result = rembg_remove(image_data)

    # Verify we got a valid image back
    img = Image.open(io.BytesIO(result))
    logger.info(f"Background removed: {img.width}x{img.height}")
    return result


def enhance_document(image_data: bytes) -> bytes:
    """
    Enhance a document/photo image — improve contrast, sharpness, and clarity
    without introducing blur or artifacts.

    Args:
        image_data: Input image bytes

    Returns:
        Enhanced image bytes (PNG)
    """
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    # Step 1: Auto-contrast via CLAHE on lightness (if OpenCV available)
    if OPENCV_AVAILABLE:
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)

        # Gentle CLAHE — just enough to improve contrast
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)

        enhanced_lab = cv2.merge((cl, a, b))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        enhanced_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(enhanced_rgb)

    # Step 2: Gentle sharpening via Pillow (no harsh kernels)
    image = ImageEnhance.Sharpness(image).enhance(1.4)

    # Step 3: Slight contrast boost
    image = ImageEnhance.Contrast(image).enhance(1.15)

    # Step 4: Slight brightness correction
    image = ImageEnhance.Brightness(image).enhance(1.05)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    logger.info(f"Document enhanced: {image.width}x{image.height}")
    return buf.getvalue()
