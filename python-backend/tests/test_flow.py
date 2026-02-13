"""Tests for the conversation flow controller.
Mocks all WhatsApp API calls and tests the routing logic."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from utils.session import _sessions, get_session, clear_session


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


def _text_message(text):
    return {"id": "msg1", "type": "text", "from": SENDER, "text": {"body": text}}


def _image_message(media_id="img_123", caption=None):
    msg = {"id": "msg2", "type": "image", "from": SENDER, "image": {"id": media_id, "mime_type": "image/jpeg"}}
    if caption:
        msg["image"]["caption"] = caption
    return msg


def _document_message(media_id="doc_123", mime_type="application/pdf", filename="test.pdf"):
    return {
        "id": "msg3", "type": "document", "from": SENDER,
        "document": {"id": media_id, "mime_type": mime_type, "filename": filename},
    }


def _list_reply_message(list_id):
    return {
        "id": "msg4", "type": "interactive", "from": SENDER,
        "interactive": {"list_reply": {"id": list_id}},
    }


def _button_reply_message(button_id):
    return {
        "id": "msg5", "type": "interactive", "from": SENDER,
        "interactive": {"button_reply": {"id": button_id}},
    }


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
         patch("utils.flow.upload_media", new_callable=AsyncMock) as upload:
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
        }


class TestGreeting:
    @pytest.mark.asyncio
    async def test_hi_sends_feature_menu(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("hi"), SENDER, MOCK_SETTINGS)
        mock_whatsapp["send_list"].assert_called_once()

    @pytest.mark.asyncio
    async def test_hello_sends_feature_menu(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("hello"), SENDER, MOCK_SETTINGS)
        mock_whatsapp["send_list"].assert_called_once()


class TestHelp:
    @pytest.mark.asyncio
    async def test_help_sends_text_and_list(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("help"), SENDER, MOCK_SETTINGS)
        assert mock_whatsapp["send_text"].call_count >= 1
        assert mock_whatsapp["send_list"].call_count >= 1


class TestCancel:
    @pytest.mark.asyncio
    async def test_cancel_clears_session(self, mock_whatsapp):
        from utils.flow import handle_message
        from utils.session import update_session
        update_session(SENDER, state="collecting_images", intent="merge")
        await handle_message(_text_message("cancel"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "idle"
        assert session.intent is None


class TestConvert:
    @pytest.mark.asyncio
    async def test_convert_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("convert"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "convert"
        mock_whatsapp["send_text"].assert_called_once()


class TestCompress:
    @pytest.mark.asyncio
    async def test_compress_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("compress"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "compress"


class TestMerge:
    @pytest.mark.asyncio
    async def test_merge_sets_collecting_state(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("merge"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.state == "collecting_images"
        assert session.intent == "merge"

    @pytest.mark.asyncio
    async def test_status_during_merge(self, mock_whatsapp):
        from utils.flow import handle_message
        from utils.session import update_session, add_image_to_session
        update_session(SENDER, state="collecting_images", intent="merge")
        add_image_to_session(SENDER, "m1", "image/jpeg")
        await handle_message(_text_message("status"), SENDER, MOCK_SETTINGS)
        call_args = mock_whatsapp["send_text"].call_args[0]
        assert "1" in call_args[2]  # Should mention count


class TestRotate:
    @pytest.mark.asyncio
    async def test_rotate_sends_buttons(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("rotate"), SENDER, MOCK_SETTINGS)
        mock_whatsapp["send_button"].assert_called_once()

    @pytest.mark.asyncio
    async def test_rotate_button_sets_angle(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_button_reply_message("btn_rotate_90"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.rotation_angle == 90


class TestSplit:
    @pytest.mark.asyncio
    async def test_split_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("split"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "split"


class TestLockUnlock:
    @pytest.mark.asyncio
    async def test_lock_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("lock"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "lock_pdf"

    @pytest.mark.asyncio
    async def test_unlock_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("unlock"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "unlock_pdf"


class TestOcr:
    @pytest.mark.asyncio
    async def test_ocr_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("ocr"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "ocr"


class TestWatermark:
    @pytest.mark.asyncio
    async def test_watermark_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("watermark"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "watermark"


class TestSign:
    @pytest.mark.asyncio
    async def test_sign_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("sign"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "sign_pdf"


class TestPdfConversions:
    @pytest.mark.asyncio
    async def test_pdf_to_word_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("pdf to word"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_word"

    @pytest.mark.asyncio
    async def test_pdf_to_image_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("pdf to image"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_image"

    @pytest.mark.asyncio
    async def test_pdf_to_ppt_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("pdf to ppt"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_ppt"

    @pytest.mark.asyncio
    async def test_pdf_to_excel_sets_intent(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("pdf to excel"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "pdf_to_excel"


class TestListReply:
    @pytest.mark.asyncio
    async def test_list_convert(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_convert"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "convert"

    @pytest.mark.asyncio
    async def test_list_split(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_list_reply_message("list_split"), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.intent == "split"


class TestFallback:
    @pytest.mark.asyncio
    async def test_unknown_message(self, mock_whatsapp):
        from utils.flow import handle_message
        await handle_message(_text_message("asdfghjkl"), SENDER, MOCK_SETTINGS)
        call_args = mock_whatsapp["send_text"].call_args[0]
        assert "understand" in call_args[2].lower() or "help" in call_args[2].lower()

    @pytest.mark.asyncio
    async def test_unsupported_type(self, mock_whatsapp):
        from utils.flow import handle_message
        msg = {"id": "msg_x", "type": "sticker", "from": SENDER}
        await handle_message(msg, SENDER, MOCK_SETTINGS)
        mock_whatsapp["send_text"].assert_called_once()


class TestImageHandling:
    @pytest.mark.asyncio
    async def test_image_default_converts(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message
        mock_whatsapp["download"].return_value = sample_image_bytes
        await handle_message(_image_message(), SENDER, MOCK_SETTINGS)
        mock_whatsapp["upload"].assert_called_once()
        mock_whatsapp["send_doc"].assert_called_once()

    @pytest.mark.asyncio
    async def test_image_with_compress_caption(self, mock_whatsapp, sample_image_bytes):
        from utils.flow import handle_message
        mock_whatsapp["download"].return_value = sample_image_bytes
        await handle_message(_image_message(caption="compress"), SENDER, MOCK_SETTINGS)
        mock_whatsapp["send_doc"].assert_called_once()
        # Caption in the sent doc should mention "compress"
        call_kwargs = mock_whatsapp["send_doc"].call_args
        assert "ompress" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_image_during_merge(self, mock_whatsapp):
        from utils.flow import handle_message
        from utils.session import update_session
        update_session(SENDER, state="collecting_images", intent="merge")
        await handle_message(_image_message(), SENDER, MOCK_SETTINGS)
        session = get_session(SENDER)
        assert session.image_count == 1
        # Should send "added" confirmation
        call_args = mock_whatsapp["send_text"].call_args[0]
        assert "added" in call_args[2].lower() or "1" in call_args[2]
