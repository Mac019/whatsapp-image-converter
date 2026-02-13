"""Tests for PDF format conversions."""

import io
import pytest
import pikepdf


class TestPdfToWord:
    def test_converts(self, sample_1page_pdf):
        from utils.pdf_converter import pdf_to_word
        result = pdf_to_word(sample_1page_pdf)
        assert len(result) > 0
        # .docx files start with PK (ZIP header)
        assert result[:2] == b"PK"


class TestPdfToExcel:
    def test_converts(self, sample_pdf_bytes):
        from utils.pdf_converter import pdf_to_excel
        result = pdf_to_excel(sample_pdf_bytes)
        assert len(result) > 0
        # .xlsx files start with PK (ZIP header)
        assert result[:2] == b"PK"

    def test_single_page(self, sample_1page_pdf):
        from utils.pdf_converter import pdf_to_excel
        result = pdf_to_excel(sample_1page_pdf)
        assert len(result) > 0


class TestMergeMixed:
    def test_merge_two_pdfs(self, sample_1page_pdf):
        from utils.pdf_converter import merge_mixed
        result = merge_mixed([
            (sample_1page_pdf, "application/pdf"),
            (sample_1page_pdf, "application/pdf"),
        ])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_merge_pdf_and_image(self, sample_1page_pdf, sample_image_bytes):
        from utils.pdf_converter import merge_mixed
        result = merge_mixed([
            (sample_1page_pdf, "application/pdf"),
            (sample_image_bytes, "image/jpeg"),
        ])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_merge_empty_raises(self):
        from utils.pdf_converter import merge_mixed
        with pytest.raises(ValueError, match="No valid files"):
            merge_mixed([])

    def test_skips_unsupported(self, sample_1page_pdf):
        from utils.pdf_converter import merge_mixed
        result = merge_mixed([
            (sample_1page_pdf, "application/pdf"),
            (b"not a real file", "application/x-unknown"),
        ])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1
