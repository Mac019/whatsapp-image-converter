"""
Core PDF manipulation tools using pikepdf.
Split, rotate, reorder, compress, protect, unlock, page numbers, watermark, sign, archive.
All operations work in-memory — nothing stored on disk.
"""

import io
import logging
from typing import List, Optional

import pikepdf

logger = logging.getLogger(__name__)


def split_pdf(pdf_data: bytes, page_spec: str) -> bytes:
    """
    Extract specific pages from a PDF.

    Args:
        pdf_data: Input PDF bytes
        page_spec: Page specification like "1-3,5,7-9" (1-indexed)

    Returns:
        New PDF with only the specified pages
    """
    pages = _parse_page_spec(page_spec)

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        total = len(pdf.pages)
        # Filter valid page indices (convert 1-indexed to 0-indexed)
        valid_pages = [p - 1 for p in pages if 1 <= p <= total]

        if not valid_pages:
            raise ValueError(f"No valid pages in range. PDF has {total} pages.")

        output = pikepdf.new()
        for idx in valid_pages:
            output.pages.append(pdf.pages[idx])

        buf = io.BytesIO()
        output.save(buf)
        buf.seek(0)
        logger.info(f"Split PDF: extracted {len(valid_pages)} pages from {total}")
        return buf.getvalue()


def rotate_pdf(pdf_data: bytes, angle: int) -> bytes:
    """
    Rotate all pages of a PDF.

    Args:
        pdf_data: Input PDF bytes
        angle: Rotation angle (90, 180, 270)

    Returns:
        Rotated PDF bytes
    """
    if angle not in (90, 180, 270):
        raise ValueError("Angle must be 90, 180, or 270")

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        for page in pdf.pages:
            current = int(page.get("/Rotate", 0))
            page["/Rotate"] = (current + angle) % 360

        buf = io.BytesIO()
        pdf.save(buf)
        buf.seek(0)
        logger.info(f"Rotated PDF {angle}° ({len(pdf.pages)} pages)")
        return buf.getvalue()


def reorder_pdf(pdf_data: bytes, order_spec: str) -> bytes:
    """
    Reorder pages of a PDF.

    Args:
        pdf_data: Input PDF bytes
        order_spec: Comma-separated page numbers like "3,1,2,4" (1-indexed)

    Returns:
        Reordered PDF bytes
    """
    order = [int(x.strip()) for x in order_spec.split(",") if x.strip().isdigit()]

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        total = len(pdf.pages)
        valid_order = [p - 1 for p in order if 1 <= p <= total]

        if not valid_order:
            raise ValueError(f"No valid pages. PDF has {total} pages.")

        output = pikepdf.new()
        for idx in valid_order:
            output.pages.append(pdf.pages[idx])

        buf = io.BytesIO()
        output.save(buf)
        buf.seek(0)
        logger.info(f"Reordered PDF: {len(valid_order)} pages")
        return buf.getvalue()


def protect_pdf(pdf_data: bytes, password: str) -> bytes:
    """
    Password-protect a PDF.

    Args:
        pdf_data: Input PDF bytes
        password: Password to set

    Returns:
        Encrypted PDF bytes
    """
    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        encryption = pikepdf.Encryption(
            owner=password,
            user=password,
            R=6,  # AES-256
        )
        buf = io.BytesIO()
        pdf.save(buf, encryption=encryption)
        buf.seek(0)
        logger.info("PDF password-protected successfully")
        return buf.getvalue()


def unlock_pdf(pdf_data: bytes, password: str) -> bytes:
    """
    Remove password protection from a PDF.

    Args:
        pdf_data: Input encrypted PDF bytes
        password: Password to unlock

    Returns:
        Unprotected PDF bytes
    """
    try:
        with pikepdf.open(io.BytesIO(pdf_data), password=password) as pdf:
            buf = io.BytesIO()
            pdf.save(buf)
            buf.seek(0)
            logger.info("PDF unlocked successfully")
            return buf.getvalue()
    except pikepdf.PasswordError:
        raise ValueError("Wrong password")


def compress_pdf(pdf_data: bytes, quality: str = "medium") -> bytes:
    """
    Compress a PDF by rewriting it with pikepdf optimizations.

    Args:
        pdf_data: Input PDF bytes
        quality: "low", "medium", or "high" (low = most compression)

    Returns:
        Compressed PDF bytes
    """
    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        buf = io.BytesIO()

        if quality == "low":
            # Aggressive: linearize and compress streams
            pdf.save(buf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        elif quality == "medium":
            pdf.save(buf, compress_streams=True)
        else:
            # High quality: minimal compression
            pdf.save(buf)

        buf.seek(0)
        original_size = len(pdf_data)
        compressed_size = len(buf.getvalue())
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        logger.info(f"Compressed PDF: {original_size} → {compressed_size} bytes ({ratio:.1f}% reduction)")
        return buf.getvalue()


def merge_pdfs(pdf_list: List[bytes]) -> bytes:
    """
    Merge multiple PDFs into one.

    Args:
        pdf_list: List of PDF bytes

    Returns:
        Merged PDF bytes
    """
    if len(pdf_list) < 2:
        raise ValueError("Need at least 2 PDFs to merge")

    output = pikepdf.new()

    for i, pdf_data in enumerate(pdf_list):
        with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
            for page in pdf.pages:
                output.pages.append(page)
        logger.info(f"Added PDF {i + 1}/{len(pdf_list)} to merge")

    buf = io.BytesIO()
    output.save(buf)
    buf.seek(0)
    logger.info(f"Merged {len(pdf_list)} PDFs, total {len(output.pages)} pages")
    return buf.getvalue()


def add_page_numbers(pdf_data: bytes, position: str = "bottom-center") -> bytes:
    """
    Add page numbers to a PDF using reportlab overlay.

    Args:
        pdf_data: Input PDF bytes
        position: Position of page numbers

    Returns:
        PDF with page numbers
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import letter

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            # Get page dimensions
            mediabox = page.get("/MediaBox")
            width = float(mediabox[2])
            height = float(mediabox[3])

            # Create overlay with page number
            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf, pagesize=(width, height))

            text = f"{i + 1} / {total_pages}"
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.4, 0.4, 0.4)

            if position == "bottom-center":
                c.drawCentredString(width / 2, 20, text)
            elif position == "bottom-right":
                c.drawRightString(width - 30, 20, text)
            else:
                c.drawCentredString(width / 2, 20, text)

            c.save()
            overlay_buf.seek(0)

            # Merge overlay onto page
            with pikepdf.open(overlay_buf) as overlay_pdf:
                page.add_overlay(overlay_pdf.pages[0])

        buf = io.BytesIO()
        pdf.save(buf)
        buf.seek(0)
        logger.info(f"Added page numbers to {total_pages} pages")
        return buf.getvalue()


def add_watermark(pdf_data: bytes, watermark_text: str) -> bytes:
    """
    Add a diagonal text watermark to every page of a PDF.

    Args:
        pdf_data: Input PDF bytes
        watermark_text: Text to use as watermark

    Returns:
        Watermarked PDF bytes
    """
    from reportlab.pdfgen import canvas as rl_canvas

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        for page in pdf.pages:
            mediabox = page.get("/MediaBox")
            width = float(mediabox[2])
            height = float(mediabox[3])

            # Create watermark overlay
            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf, pagesize=(width, height))
            c.setFont("Helvetica", 50)
            c.setFillAlpha(0.3)
            c.setFillColorRGB(0.8, 0.8, 0.8)
            c.saveState()
            c.translate(width / 2, height / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
            c.save()
            overlay_buf.seek(0)

            with pikepdf.open(overlay_buf) as overlay_pdf:
                page.add_overlay(overlay_pdf.pages[0])

        buf = io.BytesIO()
        pdf.save(buf)
        buf.seek(0)
        logger.info(f"Added watermark '{watermark_text}' to {len(pdf.pages)} pages")
        return buf.getvalue()


def sign_pdf(pdf_data: bytes, signature_image: bytes, page_num: int = -1) -> bytes:
    """
    Overlay a signature image on a PDF page.

    Args:
        pdf_data: Input PDF bytes
        signature_image: Signature image bytes (PNG/JPG)
        page_num: Page to sign (-1 for last page, 1-indexed)

    Returns:
        Signed PDF bytes
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    sig_img = Image.open(io.BytesIO(signature_image))
    if sig_img.mode == "RGBA":
        pass  # keep transparency
    else:
        sig_img = sig_img.convert("RGBA")

    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        total = len(pdf.pages)
        target_idx = (page_num - 1) if page_num > 0 else (total - 1)
        target_idx = max(0, min(target_idx, total - 1))

        page = pdf.pages[target_idx]
        mediabox = page.get("/MediaBox")
        width = float(mediabox[2])
        height = float(mediabox[3])

        # Scale signature to ~20% of page width
        sig_width = width * 0.2
        sig_height = sig_width * (sig_img.height / sig_img.width)

        # Position: bottom-right
        x = width - sig_width - 40
        y = 40

        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(width, height))

        sig_reader = ImageReader(sig_img)
        c.drawImage(sig_reader, x, y, sig_width, sig_height, mask="auto")
        c.save()
        overlay_buf.seek(0)

        overlay_pdf = pikepdf.open(overlay_buf)
        page.add_overlay(overlay_pdf.pages[0])

        buf = io.BytesIO()
        pdf.save(buf)
        buf.seek(0)
        logger.info(f"Added signature to page {target_idx + 1}")
        return buf.getvalue()


def make_pdf_archive(pdf_data: bytes) -> bytes:
    """
    Add PDF/A-like metadata for archival purposes.

    Args:
        pdf_data: Input PDF bytes

    Returns:
        PDF with archival metadata
    """
    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        with pdf.open_metadata() as meta:
            meta["dc:title"] = "Archived Document"
            meta["dc:description"] = "Archived via DocBot"
            meta["pdf:Producer"] = "DocBot PDF Archiver"
            meta["xmp:CreatorTool"] = "DocBot"

        buf = io.BytesIO()
        pdf.save(buf, linearize=True)
        buf.seek(0)
        logger.info("Created archive-ready PDF with metadata")
        return buf.getvalue()


def get_pdf_info(pdf_data: bytes) -> dict:
    """Get basic info about a PDF (page count, size, etc.)."""
    with pikepdf.open(io.BytesIO(pdf_data)) as pdf:
        return {
            "pages": len(pdf.pages),
            "size_bytes": len(pdf_data),
            "encrypted": pdf.is_encrypted,
        }


# ── Helpers ────────────────────────────────────────────────────────

def _parse_page_spec(spec: str) -> List[int]:
    """
    Parse a page specification string into a list of page numbers.
    Examples: "1-3,5" → [1, 2, 3, 5], "1,2,3" → [1, 2, 3]
    """
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                pages.extend(range(int(start), int(end) + 1))
            except ValueError:
                continue
        elif part.isdigit():
            pages.append(int(part))
    return sorted(set(pages))
