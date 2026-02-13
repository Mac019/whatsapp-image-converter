"""Tests for PDF tools — split, rotate, reorder, compress, protect, unlock,
page numbers, watermark, sign, archive, info."""

import io
import pytest
import pikepdf


class TestSplitPdf:
    def test_extract_single_page(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        result = split_pdf(sample_pdf_bytes, "2")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1

    def test_extract_range(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        result = split_pdf(sample_pdf_bytes, "1-2")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_extract_comma_separated(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        result = split_pdf(sample_pdf_bytes, "1,3")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_extract_mixed(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        result = split_pdf(sample_pdf_bytes, "1-2,3")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_invalid_pages_raises(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        with pytest.raises(ValueError, match="No valid pages"):
            split_pdf(sample_pdf_bytes, "99")

    def test_out_of_range_filtered(self, sample_pdf_bytes):
        from utils.pdf_tools import split_pdf
        result = split_pdf(sample_pdf_bytes, "1,99")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1


class TestRotatePdf:
    def test_rotate_90(self, sample_1page_pdf):
        from utils.pdf_tools import rotate_pdf
        result = rotate_pdf(sample_1page_pdf, 90)
        with pikepdf.open(io.BytesIO(result)) as pdf:
            rotation = int(pdf.pages[0].get("/Rotate", 0))
            assert rotation == 90

    def test_rotate_180(self, sample_1page_pdf):
        from utils.pdf_tools import rotate_pdf
        result = rotate_pdf(sample_1page_pdf, 180)
        with pikepdf.open(io.BytesIO(result)) as pdf:
            rotation = int(pdf.pages[0].get("/Rotate", 0))
            assert rotation == 180

    def test_rotate_270(self, sample_1page_pdf):
        from utils.pdf_tools import rotate_pdf
        result = rotate_pdf(sample_1page_pdf, 270)
        with pikepdf.open(io.BytesIO(result)) as pdf:
            rotation = int(pdf.pages[0].get("/Rotate", 0))
            assert rotation == 270

    def test_invalid_angle_raises(self, sample_1page_pdf):
        from utils.pdf_tools import rotate_pdf
        with pytest.raises(ValueError, match="90, 180, or 270"):
            rotate_pdf(sample_1page_pdf, 45)

    def test_rotate_all_pages(self, sample_pdf_bytes):
        from utils.pdf_tools import rotate_pdf
        result = rotate_pdf(sample_pdf_bytes, 90)
        with pikepdf.open(io.BytesIO(result)) as pdf:
            for page in pdf.pages:
                assert int(page.get("/Rotate", 0)) == 90

    def test_result_is_valid_pdf(self, sample_1page_pdf):
        from utils.pdf_tools import rotate_pdf
        result = rotate_pdf(sample_1page_pdf, 90)
        assert len(result) > 0
        # Should be parseable
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1


class TestReorderPdf:
    def test_reverse_order(self, sample_pdf_bytes):
        from utils.pdf_tools import reorder_pdf
        result = reorder_pdf(sample_pdf_bytes, "3,2,1")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_subset_order(self, sample_pdf_bytes):
        from utils.pdf_tools import reorder_pdf
        result = reorder_pdf(sample_pdf_bytes, "2,1")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_invalid_order_raises(self, sample_pdf_bytes):
        from utils.pdf_tools import reorder_pdf
        with pytest.raises(ValueError, match="No valid pages"):
            reorder_pdf(sample_pdf_bytes, "99,100")


class TestProtectAndUnlock:
    def test_protect_then_unlock(self, sample_1page_pdf):
        from utils.pdf_tools import protect_pdf, unlock_pdf
        password = "test123"
        protected = protect_pdf(sample_1page_pdf, password)

        # Protected PDF should be encrypted
        with pikepdf.open(io.BytesIO(protected), password=password) as pdf:
            assert len(pdf.pages) == 1

        # Unlock it
        unlocked = unlock_pdf(protected, password)
        with pikepdf.open(io.BytesIO(unlocked)) as pdf:
            assert len(pdf.pages) == 1

    def test_wrong_password_raises(self, sample_1page_pdf):
        from utils.pdf_tools import protect_pdf, unlock_pdf
        protected = protect_pdf(sample_1page_pdf, "correct")
        with pytest.raises(ValueError, match="Wrong password"):
            unlock_pdf(protected, "wrong")


class TestCompressPdf:
    def test_compress_low(self, sample_pdf_bytes):
        from utils.pdf_tools import compress_pdf
        result = compress_pdf(sample_pdf_bytes, "low")
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_compress_medium(self, sample_pdf_bytes):
        from utils.pdf_tools import compress_pdf
        result = compress_pdf(sample_pdf_bytes, "medium")
        assert len(result) > 0

    def test_compress_high(self, sample_pdf_bytes):
        from utils.pdf_tools import compress_pdf
        result = compress_pdf(sample_pdf_bytes, "high")
        assert len(result) > 0


class TestMergePdfs:
    def test_merge_two(self, sample_1page_pdf):
        from utils.pdf_tools import merge_pdfs
        result = merge_pdfs([sample_1page_pdf, sample_1page_pdf])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_merge_three(self, sample_1page_pdf, sample_pdf_bytes):
        from utils.pdf_tools import merge_pdfs
        result = merge_pdfs([sample_1page_pdf, sample_pdf_bytes])
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 4  # 1 + 3

    def test_merge_minimum_raises(self, sample_1page_pdf):
        from utils.pdf_tools import merge_pdfs
        with pytest.raises(ValueError, match="at least 2"):
            merge_pdfs([sample_1page_pdf])


class TestAddPageNumbers:
    def test_adds_page_numbers(self, sample_pdf_bytes):
        from utils.pdf_tools import add_page_numbers
        result = add_page_numbers(sample_pdf_bytes)
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_single_page(self, sample_1page_pdf):
        from utils.pdf_tools import add_page_numbers
        result = add_page_numbers(sample_1page_pdf)
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1


class TestAddWatermark:
    def test_adds_watermark(self, sample_pdf_bytes):
        from utils.pdf_tools import add_watermark
        result = add_watermark(sample_pdf_bytes, "CONFIDENTIAL")
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_single_page_watermark(self, sample_1page_pdf):
        from utils.pdf_tools import add_watermark
        result = add_watermark(sample_1page_pdf, "DRAFT")
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1


class TestSignPdf:
    def test_sign_last_page(self, sample_pdf_bytes, signature_image_bytes):
        from utils.pdf_tools import sign_pdf
        result = sign_pdf(sample_pdf_bytes, signature_image_bytes)
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 3

    def test_sign_first_page(self, sample_pdf_bytes, signature_image_bytes):
        from utils.pdf_tools import sign_pdf
        result = sign_pdf(sample_pdf_bytes, signature_image_bytes, page_num=1)
        assert len(result) > 0


class TestMakePdfArchive:
    def test_archive(self, sample_1page_pdf):
        from utils.pdf_tools import make_pdf_archive
        result = make_pdf_archive(sample_1page_pdf)
        assert len(result) > 0
        with pikepdf.open(io.BytesIO(result)) as pdf:
            assert len(pdf.pages) == 1


class TestGetPdfInfo:
    def test_info(self, sample_pdf_bytes):
        from utils.pdf_tools import get_pdf_info
        info = get_pdf_info(sample_pdf_bytes)
        assert info["pages"] == 3
        assert info["size_bytes"] == len(sample_pdf_bytes)
        assert info["encrypted"] is False

    def test_info_single_page(self, sample_1page_pdf):
        from utils.pdf_tools import get_pdf_info
        info = get_pdf_info(sample_1page_pdf)
        assert info["pages"] == 1


class TestParsePageSpec:
    def test_single(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("1") == [1]

    def test_range(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("1-3") == [1, 2, 3]

    def test_comma(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("1,3,5") == [1, 3, 5]

    def test_mixed(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("1-2,5") == [1, 2, 5]

    def test_deduplicate(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("1,1,2") == [1, 2]

    def test_empty(self):
        from utils.pdf_tools import _parse_page_spec
        assert _parse_page_spec("") == []
