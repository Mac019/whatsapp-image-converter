"""
Image to PDF conversion utilities.
Uses Pillow for image processing and img2pdf for conversion.
"""

import io
import logging
from typing import List, Tuple
from PIL import Image
import img2pdf
from utils.scanner import scan_document

logger = logging.getLogger(__name__)

# Maximum dimensions for images (to prevent memory issues)
MAX_DIMENSION = 8192

# Supported image formats
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


COMPRESS_MAX_DIMENSION = 2048
COMPRESS_QUALITY = 40


def _process_image(image_data: bytes, mime_type: str, compress: bool = False) -> Image.Image:
    """
    Open, validate, and normalize an image for PDF conversion.

    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image
        compress: If True, apply aggressive resizing

    Returns:
        Processed PIL Image in RGB mode
    """
    if mime_type not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {mime_type}")

    image = Image.open(io.BytesIO(image_data))

    # Convert to RGB if necessary (for PNG with transparency)
    if image.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Handle EXIF orientation
    try:
        exif = image._getexif()
        if exif:
            orientation = exif.get(274)
            if orientation:
                rotations = {3: 180, 6: 270, 8: 90}
                if orientation in rotations:
                    image = image.rotate(rotations[orientation], expand=True)
    except (AttributeError, KeyError, TypeError):
        pass

    # Resize based on compress mode
    max_dim = COMPRESS_MAX_DIMENSION if compress else MAX_DIMENSION
    if max(image.size) > max_dim:
        ratio = max_dim / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized image to {new_size}")

    return image


def _image_to_jpeg_bytes(image: Image.Image, compress: bool = False) -> bytes:
    """Convert a PIL Image to JPEG bytes."""
    img_buffer = io.BytesIO()
    if compress:
        image.save(img_buffer, format="JPEG", quality=COMPRESS_QUALITY)
    else:
        # Max quality: no chroma subsampling, highest quality
        image.save(img_buffer, format="JPEG", quality=100, subsampling=0)
    img_buffer.seek(0)
    return img_buffer.getvalue()


def _image_to_png_bytes(image: Image.Image) -> bytes:
    """Convert a PIL Image to PNG bytes (lossless)."""
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG", optimize=False)
    img_buffer.seek(0)
    return img_buffer.getvalue()


def convert_image_to_pdf(
    image_data: bytes, mime_type: str = "image/jpeg", compress: bool = False
) -> bytes:
    """
    Convert an image to PDF.

    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image
        compress: If True, produce a smaller PDF (lower quality, smaller dimensions)

    Returns:
        PDF file as bytes
    """
    mode = "compressed" if compress else "normal"
    logger.info(f"Converting image ({mode}) of type {mime_type}, size {len(image_data)} bytes")

    image = _process_image(image_data, mime_type, compress=compress)
    image = scan_document(image)

    if compress:
        img_bytes = _image_to_jpeg_bytes(image, compress=True)
    else:
        # Lossless PNG for maximum quality — no JPEG artifacts
        img_bytes = _image_to_png_bytes(image)

    pdf_bytes = img2pdf.convert(img_bytes)

    logger.info(f"Created PDF of size {len(pdf_bytes)} bytes")
    return pdf_bytes


def merge_images_to_pdf(
    images: List[Tuple[bytes, str]], compress: bool = False
) -> bytes:
    """
    Merge multiple images into a single multi-page PDF.

    Args:
        images: List of (image_data, mime_type) tuples
        compress: If True, compress each page

    Returns:
        Multi-page PDF as bytes
    """
    if not images:
        raise ValueError("No images to merge")

    logger.info(f"Merging {len(images)} images into PDF (compress={compress})")

    pages = []
    for i, (image_data, mime_type) in enumerate(images):
        image = _process_image(image_data, mime_type, compress=compress)
        image = scan_document(image)
        if compress:
            img_bytes = _image_to_jpeg_bytes(image, compress=True)
        else:
            img_bytes = _image_to_png_bytes(image)
        pages.append(img_bytes)
        logger.info(f"Processed page {i + 1}/{len(images)}")

    pdf_bytes = img2pdf.convert(pages)

    logger.info(f"Created merged PDF: {len(images)} pages, {len(pdf_bytes)} bytes")
    return pdf_bytes


def validate_image(image_data: bytes) -> bool:
    """
    Validate that the data is a valid image.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image: {str(e)}")
        return False
