"""
OCR wrapper using Tesseract for text extraction from images and PDFs.
Supports English and Hindi.
"""

import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed — OCR disabled")


def extract_text_from_image(image_data: bytes, lang: str = "eng+hin") -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_data: Raw image bytes (JPEG, PNG, etc.)
        lang: Tesseract language code (e.g., "eng", "hin", "eng+hin")

    Returns:
        Extracted text string
    """
    if not TESSERACT_AVAILABLE:
        raise RuntimeError("Tesseract is not installed. Install with: pip install pytesseract")

    image = Image.open(io.BytesIO(image_data))

    # Convert to RGB if needed
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    text = pytesseract.image_to_string(image, lang=lang)
    text = text.strip()

    logger.info(f"OCR extracted {len(text)} characters from image")
    return text


def extract_text_from_pdf(pdf_data: bytes, lang: str = "eng+hin") -> str:
    """
    Extract text from a PDF. First tries PyPDF2 text extraction,
    falls back to OCR on rendered pages.

    Args:
        pdf_data: Raw PDF bytes
        lang: Tesseract language code for OCR fallback

    Returns:
        Extracted text string
    """
    # Try direct text extraction first using PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(pdf_data))
        text_parts = []
        for page in reader.pages:
            try:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text.strip())
            except Exception:
                pass

        if text_parts:
            result = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(result)} chars from PDF (direct)")
            return result
    except ImportError:
        logger.warning("PyPDF2 not installed — skipping direct text extraction")
    except Exception as e:
        logger.warning(f"Direct text extraction failed: {e}")

    # Fall back to OCR on rendered pages
    if not TESSERACT_AVAILABLE:
        return ""

    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_data, dpi=200)

        ocr_parts = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang=lang)
            if page_text.strip():
                ocr_parts.append(f"--- Page {i + 1} ---\n{page_text.strip()}")

        result = "\n\n".join(ocr_parts)
        logger.info(f"OCR extracted {len(result)} chars from {len(images)} PDF pages")
        return result

    except ImportError:
        logger.warning("pdf2image not installed — cannot OCR PDF pages")
        return ""
    except Exception as e:
        logger.error(f"OCR on PDF failed: {e}")
        return ""


def create_text_file(text: str) -> bytes:
    """Create a .txt file from text content."""
    return text.encode("utf-8")
