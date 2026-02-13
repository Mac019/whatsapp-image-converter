"""Shared test fixtures — sample PDFs, images, etc."""

import io
import pytest
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter


@pytest.fixture
def sample_image_bytes():
    """A small red 100x80 JPEG image."""
    img = Image.new("RGB", (100, 80), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes():
    """A small RGBA PNG with transparency."""
    img = Image.new("RGBA", (100, 80), color=(0, 128, 255, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_pdf_bytes():
    """A 3-page PDF with text content."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)

    for i in range(1, 4):
        c.setFont("Helvetica", 24)
        c.drawString(72, 700, f"Page {i} of 3")
        c.setFont("Helvetica", 12)
        c.drawString(72, 650, f"This is test content on page {i}.")
        c.drawString(72, 630, "Column A\tColumn B\tColumn C")
        c.showPage()

    c.save()
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_1page_pdf():
    """A single-page PDF."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica", 14)
    c.drawString(72, 700, "Single page document")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def signature_image_bytes():
    """A small signature-like image (black on white)."""
    img = Image.new("RGBA", (200, 60), color=(255, 255, 255, 0))
    # Draw a simple line across the image
    for x in range(20, 180):
        y = 30 + int(10 * ((x % 20) - 10) / 10)
        img.putpixel((x, y), (0, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
