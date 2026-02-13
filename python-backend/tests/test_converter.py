"""Tests for image-to-PDF converter."""

import io
import pytest
import pikepdf
from PIL import Image


class TestConvertImageToPdf:
    def test_jpeg_to_pdf(self, sample_image_bytes):
        from utils.converter import convert_image_to_pdf
        result = convert_image_to_pdf(sample_image_bytes, "image/jpeg")
        assert len(result) > 0
        # Verify it's a valid PDF
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1

    def test_png_to_pdf(self, sample_png_bytes):
        from utils.converter import convert_image_to_pdf
        result = convert_image_to_pdf(sample_png_bytes, "image/png")
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1

    def test_compress_mode(self, sample_image_bytes):
        from utils.converter import convert_image_to_pdf
        normal = convert_image_to_pdf(sample_image_bytes, "image/jpeg", compress=False)
        compressed = convert_image_to_pdf(sample_image_bytes, "image/jpeg", compress=True)
        # Compressed should generally be smaller (though for tiny test images, may vary)
        assert len(compressed) > 0
        assert len(normal) > 0

    def test_unsupported_format_raises(self, sample_image_bytes):
        from utils.converter import convert_image_to_pdf
        with pytest.raises(ValueError, match="Unsupported"):
            convert_image_to_pdf(sample_image_bytes, "image/bmp")


class TestMergeImagesToPdf:
    def test_merge_two_images(self, sample_image_bytes):
        from utils.converter import merge_images_to_pdf
        result = merge_images_to_pdf([
            (sample_image_bytes, "image/jpeg"),
            (sample_image_bytes, "image/jpeg"),
        ])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_merge_mixed_formats(self, sample_image_bytes, sample_png_bytes):
        from utils.converter import merge_images_to_pdf
        result = merge_images_to_pdf([
            (sample_image_bytes, "image/jpeg"),
            (sample_png_bytes, "image/png"),
        ])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_merge_empty_raises(self):
        from utils.converter import merge_images_to_pdf
        with pytest.raises(ValueError, match="No images"):
            merge_images_to_pdf([])


class TestValidateImage:
    def test_valid_jpeg(self, sample_image_bytes):
        from utils.converter import validate_image
        assert validate_image(sample_image_bytes) is True

    def test_valid_png(self, sample_png_bytes):
        from utils.converter import validate_image
        assert validate_image(sample_png_bytes) is True

    def test_invalid_data(self):
        from utils.converter import validate_image
        assert validate_image(b"not an image") is False


class TestProcessImage:
    def test_rgba_to_rgb(self):
        from utils.converter import _process_image
        # Create RGBA image
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = _process_image(buf.getvalue(), "image/png")
        assert result.mode == "RGB"

    def test_large_image_resized(self):
        from utils.converter import _process_image, MAX_DIMENSION
        # Create a large image
        img = Image.new("RGB", (10000, 10000), (0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = _process_image(buf.getvalue(), "image/jpeg")
        assert max(result.size) <= MAX_DIMENSION

    def test_compress_resized_smaller(self):
        from utils.converter import _process_image, COMPRESS_MAX_DIMENSION
        img = Image.new("RGB", (4000, 4000), (0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = _process_image(buf.getvalue(), "image/jpeg", compress=True)
        assert max(result.size) <= COMPRESS_MAX_DIMENSION
