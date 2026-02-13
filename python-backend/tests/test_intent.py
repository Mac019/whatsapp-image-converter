"""Tests for intent detection."""

import pytest
from utils.intent import (
    Intent, detect_intent, detect_intent_from_caption,
    detect_intent_from_button, detect_intent_from_list,
)


class TestDetectIntent:
    def test_greeting(self):
        assert detect_intent("hi") == Intent.GREETING
        assert detect_intent("Hello") == Intent.GREETING
        assert detect_intent("namaste") == Intent.GREETING
        assert detect_intent("hey there") == Intent.GREETING

    def test_help(self):
        assert detect_intent("help") == Intent.HELP
        assert detect_intent("menu") == Intent.HELP
        assert detect_intent("what can you do") == Intent.HELP

    def test_cancel(self):
        assert detect_intent("cancel") == Intent.CANCEL
        assert detect_intent("stop") == Intent.CANCEL
        assert detect_intent("band karo") == Intent.CANCEL

    def test_done(self):
        assert detect_intent("done") == Intent.DONE
        assert detect_intent("that's all") == Intent.DONE
        assert detect_intent("bas") == Intent.DONE

    def test_convert(self):
        assert detect_intent("convert") == Intent.CONVERT
        assert detect_intent("make pdf") == Intent.CONVERT
        assert detect_intent("image to pdf") == Intent.CONVERT

    def test_compress(self):
        assert detect_intent("compress") == Intent.COMPRESS
        assert detect_intent("reduce") == Intent.COMPRESS
        assert detect_intent("chhota") == Intent.COMPRESS

    def test_merge(self):
        assert detect_intent("merge") == Intent.MERGE
        assert detect_intent("combine") == Intent.MERGE
        assert detect_intent("ek pdf") == Intent.MERGE

    def test_split(self):
        assert detect_intent("split") == Intent.SPLIT
        assert detect_intent("extract pages") == Intent.SPLIT

    def test_rotate(self):
        assert detect_intent("rotate") == Intent.ROTATE
        assert detect_intent("ghumao") == Intent.ROTATE

    def test_reorder(self):
        assert detect_intent("reorder") == Intent.REORDER
        assert detect_intent("rearrange") == Intent.REORDER

    def test_lock_pdf(self):
        assert detect_intent("lock") == Intent.LOCK_PDF
        assert detect_intent("password protect") == Intent.LOCK_PDF
        assert detect_intent("password lagao") == Intent.LOCK_PDF

    def test_unlock_pdf(self):
        assert detect_intent("unlock") == Intent.UNLOCK_PDF
        assert detect_intent("unlock pdf") == Intent.UNLOCK_PDF
        assert detect_intent("remove password") == Intent.UNLOCK_PDF
        assert detect_intent("password hatao") == Intent.UNLOCK_PDF

    def test_ocr(self):
        assert detect_intent("ocr") == Intent.OCR
        assert detect_intent("extract text") == Intent.OCR
        assert detect_intent("text nikalo") == Intent.OCR

    def test_pdf_to_word(self):
        assert detect_intent("pdf to word") == Intent.PDF_TO_WORD
        assert detect_intent("pdf to docx") == Intent.PDF_TO_WORD

    def test_pdf_to_image(self):
        assert detect_intent("pdf to image") == Intent.PDF_TO_IMAGE
        assert detect_intent("pdf to jpg") == Intent.PDF_TO_IMAGE

    def test_pdf_to_ppt(self):
        assert detect_intent("pdf to ppt") == Intent.PDF_TO_PPT

    def test_pdf_to_excel(self):
        assert detect_intent("pdf to excel") == Intent.PDF_TO_EXCEL

    def test_word_to_pdf(self):
        assert detect_intent("word to pdf") == Intent.WORD_TO_PDF
        assert detect_intent("doc to pdf") == Intent.WORD_TO_PDF

    def test_excel_to_pdf(self):
        assert detect_intent("excel to pdf") == Intent.EXCEL_TO_PDF

    def test_ppt_to_pdf(self):
        assert detect_intent("ppt to pdf") == Intent.PPT_TO_PDF

    def test_enhance(self):
        assert detect_intent("enhance") == Intent.ENHANCE
        assert detect_intent("sharpen") == Intent.ENHANCE

    def test_remove_bg(self):
        assert detect_intent("remove bg") == Intent.REMOVE_BG
        assert detect_intent("remove background") == Intent.REMOVE_BG
        assert detect_intent("bg hatao") == Intent.REMOVE_BG

    def test_watermark(self):
        assert detect_intent("watermark") == Intent.WATERMARK

    def test_sign(self):
        assert detect_intent("sign") == Intent.SIGN_PDF
        assert detect_intent("add signature") == Intent.SIGN_PDF

    def test_page_numbers(self):
        assert detect_intent("page numbers") == Intent.PAGE_NUMBERS
        assert detect_intent("page number") == Intent.PAGE_NUMBERS

    def test_archive(self):
        assert detect_intent("archive") == Intent.PDF_ARCHIVE
        assert detect_intent("pdf/a") == Intent.PDF_ARCHIVE

    def test_status(self):
        assert detect_intent("status") == Intent.STATUS
        assert detect_intent("how many") == Intent.STATUS

    def test_unknown(self):
        assert detect_intent("asdfghjkl") == Intent.UNKNOWN
        assert detect_intent("") == Intent.UNKNOWN
        assert detect_intent(None) == Intent.UNKNOWN

    def test_case_insensitive(self):
        assert detect_intent("HELP") == Intent.HELP
        assert detect_intent("Merge") == Intent.MERGE
        assert detect_intent("PDF TO WORD") == Intent.PDF_TO_WORD


class TestDetectIntentFromCaption:
    def test_compress_caption(self):
        assert detect_intent_from_caption("compress") == Intent.COMPRESS

    def test_merge_caption(self):
        assert detect_intent_from_caption("merge") == Intent.MERGE

    def test_enhance_caption(self):
        assert detect_intent_from_caption("enhance") == Intent.ENHANCE

    def test_non_caption_intent_returns_none(self):
        assert detect_intent_from_caption("convert") is None
        assert detect_intent_from_caption("split") is None

    def test_none_caption(self):
        assert detect_intent_from_caption(None) is None

    def test_empty_caption(self):
        assert detect_intent_from_caption("") is None


class TestDetectIntentFromButton:
    def test_convert_button(self):
        assert detect_intent_from_button("btn_convert") == Intent.CONVERT

    def test_compress_button(self):
        assert detect_intent_from_button("btn_compress") == Intent.COMPRESS

    def test_merge_button(self):
        assert detect_intent_from_button("btn_merge") == Intent.MERGE

    def test_rotate_buttons(self):
        assert detect_intent_from_button("btn_rotate_90") == Intent.ROTATE
        assert detect_intent_from_button("btn_rotate_180") == Intent.ROTATE
        assert detect_intent_from_button("btn_rotate_270") == Intent.ROTATE

    def test_quality_buttons(self):
        assert detect_intent_from_button("btn_quality_low") == Intent.COMPRESS
        assert detect_intent_from_button("btn_quality_medium") == Intent.COMPRESS

    def test_unknown_button(self):
        assert detect_intent_from_button("btn_nonexistent") == Intent.UNKNOWN


class TestDetectIntentFromList:
    def test_all_list_items(self):
        assert detect_intent_from_list("list_convert") == Intent.CONVERT
        assert detect_intent_from_list("list_compress") == Intent.COMPRESS
        assert detect_intent_from_list("list_merge") == Intent.MERGE
        assert detect_intent_from_list("list_enhance") == Intent.ENHANCE
        assert detect_intent_from_list("list_remove_bg") == Intent.REMOVE_BG
        assert detect_intent_from_list("list_split") == Intent.SPLIT
        assert detect_intent_from_list("list_rotate") == Intent.ROTATE
        assert detect_intent_from_list("list_reorder") == Intent.REORDER
        assert detect_intent_from_list("list_lock") == Intent.LOCK_PDF
        assert detect_intent_from_list("list_unlock") == Intent.UNLOCK_PDF
        assert detect_intent_from_list("list_ocr") == Intent.OCR
        assert detect_intent_from_list("list_page_numbers") == Intent.PAGE_NUMBERS
        assert detect_intent_from_list("list_watermark") == Intent.WATERMARK
        assert detect_intent_from_list("list_sign") == Intent.SIGN_PDF
        assert detect_intent_from_list("list_archive") == Intent.PDF_ARCHIVE
        assert detect_intent_from_list("list_pdf_to_word") == Intent.PDF_TO_WORD
        assert detect_intent_from_list("list_pdf_to_image") == Intent.PDF_TO_IMAGE
        assert detect_intent_from_list("list_pdf_to_ppt") == Intent.PDF_TO_PPT
        assert detect_intent_from_list("list_pdf_to_excel") == Intent.PDF_TO_EXCEL
        assert detect_intent_from_list("list_word_to_pdf") == Intent.WORD_TO_PDF
        assert detect_intent_from_list("list_excel_to_pdf") == Intent.EXCEL_TO_PDF
        assert detect_intent_from_list("list_ppt_to_pdf") == Intent.PPT_TO_PDF

    def test_unknown_list(self):
        assert detect_intent_from_list("list_nope") == Intent.UNKNOWN
