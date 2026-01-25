"""
Image to PDF conversion utilities.
Uses Pillow for image processing and img2pdf for conversion.
"""

import io
import logging
from PIL import Image
import img2pdf

logger = logging.getLogger(__name__)

# Maximum dimensions for images (to prevent memory issues)
MAX_DIMENSION = 4096

# Supported image formats
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


def convert_image_to_pdf(image_data: bytes, mime_type: str = "image/jpeg") -> bytes:
    """
    Convert an image to PDF.
    
    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image
        
    Returns:
        PDF file as bytes
    """
    logger.info(f"Converting image of type {mime_type}, size {len(image_data)} bytes")
    
    # Validate mime type
    if mime_type not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {mime_type}")
    
    # Open and process the image
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary (for PNG with transparency)
    if image.mode in ("RGBA", "P", "LA"):
        # Create white background
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
            orientation = exif.get(274)  # 274 is the orientation tag
            if orientation:
                rotations = {
                    3: 180,
                    6: 270,
                    8: 90,
                }
                if orientation in rotations:
                    image = image.rotate(rotations[orientation], expand=True)
    except (AttributeError, KeyError, TypeError):
        pass  # No EXIF data or no orientation tag
    
    # Resize if too large
    if max(image.size) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized image to {new_size}")
    
    # Convert to JPEG bytes for img2pdf
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="JPEG", quality=95)
    img_buffer.seek(0)
    
    # Convert to PDF using img2pdf
    pdf_bytes = img2pdf.convert(img_buffer.getvalue())
    
    logger.info(f"Created PDF of size {len(pdf_bytes)} bytes")
    
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
