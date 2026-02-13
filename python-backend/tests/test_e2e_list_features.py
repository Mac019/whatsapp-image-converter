"""
End-to-end tests for ALL 20 features accessible from the WhatsApp list menu.
Tests simulate the full user conversation flow:
  1. User taps a feature from the list menu
  2. Bot sets the correct intent and asks for input
  3. User sends the required file (image or PDF)
  4. Bot processes and sends back the result

Every feature listed in FEATURE_SECTIONS and FEATURE_SECTIONS_2 is tested.
"""

import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from utils.session import _sessions, get_session, clear_session, update_session


@pytest.fixture(autouse=True)
def clean_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


MOCK_SETTINGS = {
    "access_token": "test_token",
    "phone_number_id": "12345",
    "webhook_verify_token": "verify_me",
}
SENDER = "919999999999"


# ── Message builders ──────────────────────────────────────────────

def _list_reply_message(list_id):
    return {
        "id": "msg1", "type": "interactive", "from": SENDER,
        "interactive": {"list_reply": {"id": list_id}},
    }


def _button_reply_message(button_id):
    return {
        "id": "msg2", "type": "interactive", "from": SENDER,
        "interactive": {"button_reply": {"id": button_id}},
    }


def _image_message(media_id="img_123", caption=None):
    msg = {
        "id": "msg3", "type": "image", "from": SENDER,
        "image": {"id": media_id, "mime_type": "image/jpeg"},
    }
    if caption:
        msg["image"]["caption"] = caption
    return msg


def _document_message(media_id="doc_123", mime_type="application/pdf", filename="test.pdf"):
    return {
        "id": "msg4", "type": "document", "from": SENDER,
        "document": {"id": media_id, "mime_type": mime_type, "filename": filename},
    }


def _text_message(text):
    return {"id": "msg5", "type": "text", "from": SENDER, "text": {"body": text}}


@pytest.fixture
def mock_whatsapp():
    """Mock all WhatsApp API functions."""
    with patch("utils.flow.send_text_message", new_callable=AsyncMock) as send_text, \
         patch("utils.flow.send_list_message", new_callable=AsyncMock) as send_list, \
         patch("utils.flow.send_button_message", new_callable=AsyncMock) as send_button, \
         patch("utils.flow.send_document_message", new_callable=AsyncMock) as send_doc, \
         patch("utils.flow.send_image_message", new_callable=AsyncMock) as send_img, \
         patch("utils.flow.send_typing_indicator", new_callable=AsyncMock) as send_typing, \
         patch("utils.flow.download_media", new_callable=AsyncMock) as download, \
         patch("utils.flow.upload_media", new_callable=AsyncMock) as upload, \
         patch("utils.flow.log_conversion") as log_conv:
        upload.return_value = "uploaded_media_id"
        yield {
            "send_text": send_text,
            "send_list": send_list,
            "send_button": send_button,
            "send_doc": send_doc,
            "send_img": send_img,
            "send_typing": send_typing,
            "download": download,
            "upload": upload,
            "log_conversion": log_conv,
        }


# ================================================================
# FEATURE SECTION 1: Image Tools (5 features)
# ================================================================


class TestListConvert:
    """list_convert → Image to PDF: user taps → bot asks for image → user sends image → gets PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_convert"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "convert", f"Expected intent 'convert', got '{session.intent}'"
        mock_whatsapp["send_text"].assert_called_once()
        assert "image" in mock_whatsapp["send_text"].call_args[0][2].lower()

    @pytest.mark.asyncio
    async def test_full_flow_image_to_pdf(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Image to PDF" from list
        await handle_message(_list_reply_message("list_convert"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "convert"

        # Step 2: User sends an image
        mock_whatsapp["download"].return_value = sample_image_bytes
        await handle_message(_image_message(), SENDER, MOCK_SETTINGS)

        # Verify: bot uploaded PDF and sent document back
        mock_whatsapp["upload"].assert_called_once()
        mock_whatsapp["send_doc"].assert_called_once()


class TestListCompress:
    """list_compress → Compress PDF: user taps → bot asks for file → user sends image/PDF → gets compressed."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_compress"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "compress", f"Expected intent 'compress', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_compress_image(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Compress PDF"
        await handle_message(_list_reply_message("list_compress"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends image
        mock_whatsapp["download"].return_value = sample_image_bytes
        await handle_message(_image_message(), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called_once()
        mock_whatsapp["send_doc"].assert_called_once()
        # Caption should mention compress
        call_kwargs = mock_whatsapp["send_doc"].call_args
        assert "ompress" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_full_flow_compress_pdf(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Compress PDF"
        await handle_message(_list_reply_message("list_compress"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()


class TestListMerge:
    """list_merge → Merge Files: user taps → bot starts collecting → user sends files → types done."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_collecting_state(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_merge"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "collecting_images"
        assert session.intent == "merge"

    @pytest.mark.asyncio
    async def test_full_flow_merge_images(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Merge Files"
        await handle_message(_list_reply_message("list_merge"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends 2 images
        await handle_message(_image_message("img_1"), SENDER, MOCK_SETTINGS)
        await handle_message(_image_message("img_2"), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.image_count == 2

        # Step 3: User types "done"
        mock_whatsapp["download"].return_value = sample_image_bytes
        await handle_message(_text_message("done"), SENDER, MOCK_SETTINGS)

        # Verify: merge was attempted
        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()


class TestListEnhance:
    """list_enhance → Enhance Image: user taps → bot asks for image → user sends image → gets enhanced."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_enhance"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "enhance", f"Expected intent 'enhance', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_enhance(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Enhance Image"
        await handle_message(_list_reply_message("list_enhance"), SENDER, MOCK_SETTINGS)
        assert get_session(SENDER).intent == "enhance"

        # Step 2: User sends an image
        mock_whatsapp["download"].return_value = sample_image_bytes
        with patch("utils.image_tools.enhance_document", return_value=sample_image_bytes) as mock_enhance:
            await handle_message(_image_message(), SENDER, MOCK_SETTINGS)
            mock_enhance.assert_called_once()

        mock_whatsapp["upload"].assert_called_once()
        mock_whatsapp["send_img"].assert_called_once()


class TestListRemoveBg:
    """list_remove_bg → Remove Background: user taps → bot asks for image → user sends image → gets result."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_remove_bg"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "remove_bg", f"Expected intent 'remove_bg', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_remove_bg(self, mock_whatsapp, sample_png_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Remove Background"
        await handle_message(_list_reply_message("list_remove_bg"), SENDER, MOCK_SETTINGS)
        assert get_session(SENDER).intent == "remove_bg"

        # Step 2: User sends image
        mock_whatsapp["download"].return_value = sample_png_bytes
        with patch("utils.image_tools.remove_background", return_value=sample_png_bytes) as mock_rm_bg:
            await handle_message(_image_message(), SENDER, MOCK_SETTINGS)
            mock_rm_bg.assert_called_once()

        mock_whatsapp["upload"].assert_called_once()
        mock_whatsapp["send_img"].assert_called_once()


# ================================================================
# FEATURE SECTION 2: PDF Tools (5 features)
# ================================================================


class TestListSplit:
    """list_split → Split PDF: user taps → sends PDF → enters page spec → gets split PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_split"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "split", f"Expected intent 'split', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_split(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Split PDF"
        await handle_message(_list_reply_message("list_split"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.state == "awaiting_input"
        assert session.pdf_data is not None

        # Step 3: User sends page spec
        await handle_message(_text_message("1-2"), SENDER, MOCK_SETTINGS)

        # Verify result sent
        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "split" in str(mock_whatsapp["send_doc"].call_args).lower() or \
               "extract" in str(mock_whatsapp["send_doc"].call_args).lower()


class TestListRotate:
    """list_rotate → Rotate PDF: user taps → selects angle → sends PDF → gets rotated PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sends_angle_buttons(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_rotate"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "rotate", f"Expected intent 'rotate', got '{session.intent}'"
        mock_whatsapp["send_button"].assert_called_once()

    @pytest.mark.asyncio
    async def test_full_flow_rotate(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Rotate PDF"
        await handle_message(_list_reply_message("list_rotate"), SENDER, MOCK_SETTINGS)

        # Step 2: User selects 90°
        await handle_message(_button_reply_message("btn_rotate_90"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.rotation_angle == 90

        # Step 3: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()


class TestListReorder:
    """list_reorder → Reorder Pages: user taps → sends PDF → enters order → gets reordered PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_reorder"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "reorder", f"Expected intent 'reorder', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_reorder(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Reorder Pages"
        await handle_message(_list_reply_message("list_reorder"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.state == "awaiting_input"

        # Step 3: User sends page order
        await handle_message(_text_message("3,1,2"), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()


class TestListLock:
    """list_lock → Lock PDF: user taps → sends PDF → enters password → gets locked PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_lock"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "lock_pdf", f"Expected intent 'lock_pdf', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_lock(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Lock PDF"
        await handle_message(_list_reply_message("list_lock"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.state == "awaiting_input"

        # Step 3: User sends password
        await handle_message(_text_message("mypassword123"), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "protect" in str(mock_whatsapp["send_doc"].call_args).lower()


class TestListUnlock:
    """list_unlock → Unlock PDF: user taps → sends locked PDF → enters password → gets unlocked PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_unlock"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "unlock_pdf", f"Expected intent 'unlock_pdf', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_unlock(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message
        from utils.pdf_tools import protect_pdf

        # Create a locked PDF for testing
        locked_pdf = protect_pdf(sample_pdf_bytes, "secret123")

        # Step 1: User taps "Unlock PDF"
        await handle_message(_list_reply_message("list_unlock"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends locked PDF
        mock_whatsapp["download"].return_value = locked_pdf
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.state == "awaiting_input"

        # Step 3: User sends password
        await handle_message(_text_message("secret123"), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "unlock" in str(mock_whatsapp["send_doc"].call_args).lower()


# ================================================================
# FEATURE SECTION 2, Group 1: More PDF Tools (5 features)
# ================================================================


class TestListOcr:
    """list_ocr → Extract Text (OCR): user taps → sends image/PDF → gets extracted text."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_ocr"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "ocr", f"Expected intent 'ocr', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_ocr_image(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Extract Text (OCR)"
        await handle_message(_list_reply_message("list_ocr"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends image
        mock_whatsapp["download"].return_value = sample_image_bytes
        with patch("utils.ocr.extract_text_from_image", return_value="Hello World") as mock_ocr:
            await handle_message(_image_message(), SENDER, MOCK_SETTINGS)
            mock_ocr.assert_called_once()

        # Bot should send text back
        text_calls = mock_whatsapp["send_text"].call_args_list
        found_text = any("Hello World" in str(c) for c in text_calls)
        assert found_text, "Extracted text should be sent back to user"

    @pytest.mark.asyncio
    async def test_full_flow_ocr_pdf(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Extract Text (OCR)"
        await handle_message(_list_reply_message("list_ocr"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        with patch("utils.ocr.extract_text_from_pdf", return_value="PDF content here") as mock_ocr:
            await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
            mock_ocr.assert_called_once()


class TestListPageNumbers:
    """list_page_numbers → Page Numbers: user taps → sends PDF → gets numbered PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_page_numbers"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "page_numbers", f"Expected intent 'page_numbers', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_page_numbers(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Page Numbers"
        await handle_message(_list_reply_message("list_page_numbers"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "number" in str(mock_whatsapp["send_doc"].call_args).lower()


class TestListWatermark:
    """list_watermark → Watermark: user taps → sends PDF → enters text → gets watermarked PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_watermark"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "watermark", f"Expected intent 'watermark', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_watermark(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Watermark"
        await handle_message(_list_reply_message("list_watermark"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.state == "awaiting_input"

        # Step 3: User sends watermark text
        await handle_message(_text_message("CONFIDENTIAL"), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "watermark" in str(mock_whatsapp["send_doc"].call_args).lower()


class TestListSign:
    """list_sign → Sign PDF: user taps → sends PDF → sends signature image → gets signed PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_sign"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "sign_pdf", f"Expected intent 'sign_pdf', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_sign(self, mock_whatsapp, sample_pdf_bytes, signature_image_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Sign PDF"
        await handle_message(_list_reply_message("list_sign"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        session = get_session(SENDER)
        assert session.has_pdf, "PDF should be stored in session"

        # Step 3: User sends signature image
        mock_whatsapp["download"].return_value = signature_image_bytes
        await handle_message(_image_message("sig_img_123"), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "sign" in str(mock_whatsapp["send_doc"].call_args).lower()


class TestListArchive:
    """list_archive → Archive PDF: user taps → sends PDF → gets archived PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_archive"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_archive", f"Expected intent 'pdf_archive', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_archive(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "Archive PDF"
        await handle_message(_list_reply_message("list_archive"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert "archiv" in str(mock_whatsapp["send_doc"].call_args).lower()


# ================================================================
# FEATURE SECTION 2, Group 2: Convert Formats (5 features)
# ================================================================


class TestListPdfToWord:
    """list_pdf_to_word → PDF to Word: user taps → sends PDF → gets .docx."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_pdf_to_word"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_word", f"Expected intent 'pdf_to_word', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_pdf_to_word(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "PDF to Word"
        await handle_message(_list_reply_message("list_pdf_to_word"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        with patch("utils.pdf_converter.pdf_to_word", return_value=b"fake_docx_data") as mock_conv:
            await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
            mock_conv.assert_called_once()

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        # Verify output filename has .docx
        call_kwargs = mock_whatsapp["send_doc"].call_args
        assert ".docx" in str(call_kwargs)


class TestListPdfToImage:
    """list_pdf_to_image → PDF to Images: user taps → sends PDF → gets images."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_pdf_to_image"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_image", f"Expected intent 'pdf_to_image', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_pdf_to_image(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "PDF to Images"
        await handle_message(_list_reply_message("list_pdf_to_image"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        fake_images = [(b"img1", "page_1.jpg"), (b"img2", "page_2.jpg")]
        with patch("utils.pdf_converter.pdf_to_images", return_value=fake_images) as mock_conv:
            await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
            mock_conv.assert_called_once()

        # Should have sent 2 images
        assert mock_whatsapp["send_img"].call_count == 2


class TestListPdfToPpt:
    """list_pdf_to_ppt → PDF to PPT: user taps → sends PDF → gets .pptx."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_pdf_to_ppt"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_ppt", f"Expected intent 'pdf_to_ppt', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_pdf_to_ppt(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "PDF to PPT"
        await handle_message(_list_reply_message("list_pdf_to_ppt"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        with patch("utils.pdf_converter.pdf_to_ppt", return_value=b"fake_pptx_data") as mock_conv:
            await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
            mock_conv.assert_called_once()

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert ".pptx" in str(mock_whatsapp["send_doc"].call_args)


class TestListPdfToExcel:
    """list_pdf_to_excel → PDF to Excel: user taps → sends PDF → gets .xlsx."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_pdf_to_excel"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_excel", f"Expected intent 'pdf_to_excel', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_pdf_to_excel(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Step 1: User taps "PDF to Excel"
        await handle_message(_list_reply_message("list_pdf_to_excel"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends PDF
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        with patch("utils.pdf_converter.pdf_to_excel", return_value=b"fake_xlsx_data") as mock_conv:
            await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
            mock_conv.assert_called_once()

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()
        assert ".xlsx" in str(mock_whatsapp["send_doc"].call_args)


class TestListWordToPdf:
    """list_word_to_pdf → Office to PDF: user taps → sends Word/Excel/PPT → gets PDF."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_word_to_pdf"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "word_to_pdf", f"Expected intent 'word_to_pdf', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_full_flow_word_to_pdf(self, mock_whatsapp):
        from utils.flow import handle_message

        # Step 1: User taps "Office to PDF"
        await handle_message(_list_reply_message("list_word_to_pdf"), SENDER, MOCK_SETTINGS)

        # Step 2: User sends a Word document
        mock_whatsapp["download"].return_value = b"fake_docx_content"
        with patch("utils.pdf_converter.office_to_pdf", return_value=b"fake_pdf_data") as mock_conv:
            await handle_message(
                _document_message(
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    filename="report.docx",
                ),
                SENDER, MOCK_SETTINGS,
            )
            mock_conv.assert_called_once()

        mock_whatsapp["upload"].assert_called()
        mock_whatsapp["send_doc"].assert_called_once()


# ================================================================
# ADDITIONAL: list_excel_to_pdf and list_ppt_to_pdf
# (These use the same list_word_to_pdf entry but map separately)
# ================================================================


class TestListExcelToPdf:
    """list_excel_to_pdf is in the intent map but not in the menu. Test it anyway."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_excel_to_pdf"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "excel_to_pdf", f"Expected intent 'excel_to_pdf', got '{session.intent}'"


class TestListPptToPdf:
    """list_ppt_to_pdf is in the intent map but not in the menu. Test it anyway."""

    @pytest.mark.asyncio
    async def test_list_reply_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_ppt_to_pdf"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "ppt_to_pdf", f"Expected intent 'ppt_to_pdf', got '{session.intent}'"


# ================================================================
# Cross-cutting: verify cancel works during any feature flow
# ================================================================


class TestCancelDuringFeatureFlow:
    """Verify cancel resets state during any in-progress feature."""

    @pytest.mark.asyncio
    async def test_cancel_during_split_awaiting_input(self, mock_whatsapp, sample_pdf_bytes):
        from utils.flow import handle_message

        # Set up split flow, send PDF, then cancel
        await handle_message(_list_reply_message("list_split"), SENDER, MOCK_SETTINGS)
        mock_whatsapp["download"].return_value = sample_pdf_bytes
        await handle_message(_document_message(), SENDER, MOCK_SETTINGS)
        assert get_session(SENDER).state == "awaiting_input"

        await handle_message(_text_message("cancel"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "idle"
        assert session.intent is None

    @pytest.mark.asyncio
    async def test_cancel_during_merge_collecting(self, mock_whatsapp):
        from utils.flow import handle_message

        await handle_message(_list_reply_message("list_merge"), SENDER, MOCK_SETTINGS)
        await handle_message(_image_message("img_1"), SENDER, MOCK_SETTINGS)
        assert get_session(SENDER).image_count == 1

        await handle_message(_text_message("cancel"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "idle"
        assert session.intent is None


# ================================================================
# Comprehensive: verify ALL 22 list IDs produce correct intents
# (This is the ultimate intent-mapping verification)
# ================================================================


class TestAllListIdsSetCorrectIntent:
    """Verify every single list reply ID maps to the correct session intent."""

    EXPECTED_INTENTS = {
        "list_convert": "convert",
        "list_compress": "compress",
        "list_merge": "merge",      # checked via state
        "list_enhance": "enhance",
        "list_remove_bg": "remove_bg",
        "list_split": "split",
        "list_rotate": "rotate",
        "list_reorder": "reorder",
        "list_lock": "lock_pdf",
        "list_unlock": "unlock_pdf",
        "list_ocr": "ocr",
        "list_page_numbers": "page_numbers",
        "list_watermark": "watermark",
        "list_sign": "sign_pdf",
        "list_archive": "pdf_archive",
        "list_pdf_to_word": "pdf_to_word",
        "list_pdf_to_image": "pdf_to_image",
        "list_pdf_to_ppt": "pdf_to_ppt",
        "list_pdf_to_excel": "pdf_to_excel",
        "list_word_to_pdf": "word_to_pdf",
        "list_excel_to_pdf": "excel_to_pdf",
        "list_ppt_to_pdf": "ppt_to_pdf",
    }

    @pytest.mark.asyncio
    @pytest.mark.parametrize("list_id,expected_intent", [
        ("list_convert", "convert"),
        ("list_compress", "compress"),
        ("list_enhance", "enhance"),
        ("list_remove_bg", "remove_bg"),
        ("list_split", "split"),
        ("list_rotate", "rotate"),
        ("list_reorder", "reorder"),
        ("list_lock", "lock_pdf"),
        ("list_unlock", "unlock_pdf"),
        ("list_ocr", "ocr"),
        ("list_page_numbers", "page_numbers"),
        ("list_watermark", "watermark"),
        ("list_sign", "sign_pdf"),
        ("list_archive", "pdf_archive"),
        ("list_pdf_to_word", "pdf_to_word"),
        ("list_pdf_to_image", "pdf_to_image"),
        ("list_pdf_to_ppt", "pdf_to_ppt"),
        ("list_pdf_to_excel", "pdf_to_excel"),
        ("list_word_to_pdf", "word_to_pdf"),
        ("list_excel_to_pdf", "excel_to_pdf"),
        ("list_ppt_to_pdf", "ppt_to_pdf"),
    ])
    async def test_list_id_sets_correct_intent(self, mock_whatsapp, list_id, expected_intent):
        from utils.flow import handle_message
        _sessions.clear()  # Ensure clean state for each parametrized run
        await handle_message(_list_reply_message(list_id), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == expected_intent, \
            f"List ID '{list_id}': expected intent '{expected_intent}', got '{session.intent}'"

    @pytest.mark.asyncio
    async def test_list_merge_sets_collecting_state(self, mock_whatsapp):
        """Merge is special — it sets state to 'collecting_images' not just intent."""
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_merge"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "collecting_images"
        assert session.intent == "merge"
