"""
Conversation flow controller.
Routes incoming WhatsApp messages through intent detection and session state
to determine the appropriate action. Handles all DocBot features.
"""

import uuid
import time
import logging
from datetime import datetime
from typing import List, Tuple

from utils.intent import (
    Intent, detect_intent, detect_intent_from_caption,
    detect_intent_from_button, detect_intent_from_list,
)
from utils.session import get_session, update_session, add_image_to_session, clear_session
from utils.converter import convert_image_to_pdf, merge_images_to_pdf
from utils.whatsapp import (
    download_media,
    upload_media,
    send_document_message,
    send_text_message,
    send_button_message,
    send_list_message,
    send_typing_indicator,
    send_image_message,
)
from utils.storage import log_conversion
from utils.errors import ErrorMessages

logger = logging.getLogger(__name__)

# ── Feature Menu (WhatsApp List Message) ──────────────────────────

FEATURE_SECTIONS = [
    {
        "title": "Image Tools",
        "rows": [
            {"id": "list_convert", "title": "Image to PDF", "description": "Convert any image to PDF"},
            {"id": "list_compress", "title": "Compress PDF", "description": "Reduce PDF file size"},
            {"id": "list_merge", "title": "Merge Files", "description": "Combine images/PDFs into one"},
            {"id": "list_enhance", "title": "Enhance Image", "description": "Improve document quality"},
            {"id": "list_remove_bg", "title": "Remove Background", "description": "Make background transparent"},
        ],
    },
    {
        "title": "PDF Tools",
        "rows": [
            {"id": "list_split", "title": "Split PDF", "description": "Extract specific pages"},
            {"id": "list_rotate", "title": "Rotate PDF", "description": "Rotate pages 90/180/270"},
            {"id": "list_reorder", "title": "Reorder Pages", "description": "Change page order"},
            {"id": "list_lock", "title": "Lock PDF", "description": "Add password protection"},
            {"id": "list_unlock", "title": "Unlock PDF", "description": "Remove password"},
        ],
    },
]

# Second list for more features (WhatsApp limit: 10 rows per list)
FEATURE_SECTIONS_2 = [
    {
        "title": "More PDF Tools",
        "rows": [
            {"id": "list_ocr", "title": "Extract Text (OCR)", "description": "Read text from images/PDFs"},
            {"id": "list_page_numbers", "title": "Page Numbers", "description": "Add page numbers to PDF"},
            {"id": "list_watermark", "title": "Watermark", "description": "Add text watermark"},
            {"id": "list_sign", "title": "Sign PDF", "description": "Add signature image"},
            {"id": "list_archive", "title": "Archive PDF", "description": "Create PDF/A for archival"},
        ],
    },
    {
        "title": "Convert Formats",
        "rows": [
            {"id": "list_pdf_to_word", "title": "PDF to Word", "description": "Convert PDF to .docx"},
            {"id": "list_pdf_to_image", "title": "PDF to Images", "description": "Each page as JPG"},
            {"id": "list_pdf_to_ppt", "title": "PDF to PPT", "description": "Convert to PowerPoint"},
            {"id": "list_pdf_to_excel", "title": "PDF to Excel", "description": "Extract tables"},
            {"id": "list_word_to_pdf", "title": "Office to PDF", "description": "Word/Excel/PPT to PDF"},
        ],
    },
]

GREETING_BODY = (
    "Hi! I'm *DocBot* — your free document tool.\n\n"
    "I can convert, compress, merge, split, rotate, OCR, watermark, "
    "and much more. All for free, nothing stored on server.\n\n"
    "Pick a feature below or just send me an image/PDF!"
)

HELP_TEXT = (
    "*Here's everything I can do:*\n\n"
    "*Image Tools:*\n"
    "- Send any image → instant PDF\n"
    "- *compress* → smaller PDF\n"
    "- *merge* → combine multiple files\n"
    "- *enhance* → improve document quality\n"
    "- *remove bg* → transparent background\n\n"
    "*PDF Tools:*\n"
    "- *split* → extract pages (e.g., 1-3,5)\n"
    "- *rotate* → rotate pages\n"
    "- *reorder* → change page order\n"
    "- *lock* → password protect\n"
    "- *unlock* → remove password\n"
    "- *ocr* → extract text\n"
    "- *page numbers* → add numbering\n"
    "- *watermark* → add text stamp\n"
    "- *sign* → add signature\n\n"
    "*Convert:*\n"
    "- *pdf to word/image/ppt/excel*\n"
    "- Send Word/Excel/PPT → get PDF\n\n"
    "Type *cancel* anytime to start over."
)

MERGE_STARTED_TEXT = "Send me the images/PDFs you want to combine.\nType *done* when you're ready."
COMPRESS_READY_TEXT = "Send me an image or PDF and I'll compress it."
CANCEL_TEXT = "Cancelled. Send me a file or type *help* to see options."

FALLBACK_BODY = (
    "I didn't understand that.\n"
    "Send me an image/PDF, or type *help* for options."
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Intents that need a PDF file sent next
PDF_INPUT_INTENTS = {
    "split", "rotate", "reorder", "lock_pdf", "unlock_pdf",
    "compress", "page_numbers", "watermark", "sign_pdf",
    "pdf_archive", "pdf_to_word", "pdf_to_image", "pdf_to_ppt", "pdf_to_excel",
    "ocr",
}

# Intents that need an image file sent next
IMAGE_INPUT_INTENTS = {"convert", "enhance", "remove_bg", "ocr"}

# Intents that need text input after PDF is received
TEXT_AFTER_PDF_INTENTS = {"split", "reorder", "lock_pdf", "unlock_pdf", "watermark"}


# ── Main entry point ───────────────────────────────────────────────

async def handle_message(message: dict, sender: str, settings: dict) -> None:
    """Main message handler."""
    message_id = message.get("id")
    if message_id:
        await send_typing_indicator(settings, sender, message_id)

    message_type = message.get("type")

    if message_type == "text":
        text = message.get("text", {}).get("body", "")
        await _handle_text(sender, text, settings)

    elif message_type == "image":
        await _handle_image(message, sender, settings)

    elif message_type == "document":
        await _handle_document(message, sender, settings)

    elif message_type == "interactive":
        await _handle_interactive(message, sender, settings)

    else:
        await send_text_message(settings, sender, FALLBACK_BODY)


# ── Text message handler ──────────────────────────────────────────

async def _handle_text(sender: str, text: str, settings: dict) -> None:
    intent = detect_intent(text)
    session = get_session(sender)

    # If we're awaiting text input (page spec, password, watermark text, etc.)
    if session.state == "awaiting_input":
        await _handle_awaited_input(sender, text, settings)
        return

    if intent == Intent.GREETING:
        await _send_feature_menu(sender, settings)

    elif intent == Intent.HELP:
        await send_text_message(settings, sender, HELP_TEXT)
        await _send_more_features_menu(sender, settings)

    elif intent == Intent.CANCEL:
        clear_session(sender)
        await send_text_message(settings, sender, CANCEL_TEXT)

    elif intent == Intent.DONE:
        await _handle_done(sender, settings)

    elif intent == Intent.STATUS:
        await _handle_status(sender, settings)

    # Features that need a file sent next
    elif intent == Intent.COMPRESS:
        update_session(sender, state="idle", intent="compress", images=[])
        await send_text_message(settings, sender, COMPRESS_READY_TEXT)

    elif intent == Intent.MERGE:
        update_session(sender, state="collecting_images", intent="merge", images=[])
        await send_text_message(settings, sender, MERGE_STARTED_TEXT)

    elif intent == Intent.CONVERT:
        update_session(sender, intent="convert")
        await send_text_message(settings, sender, "Send me the image you'd like to convert to PDF.")

    elif intent == Intent.ROTATE:
        update_session(sender, intent="rotate")
        await send_button_message(settings, sender, "Choose rotation angle:", [
            {"id": "btn_rotate_90", "title": "90°"},
            {"id": "btn_rotate_180", "title": "180°"},
            {"id": "btn_rotate_270", "title": "270°"},
        ])

    elif intent == Intent.SPLIT:
        update_session(sender, intent="split")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.REORDER:
        update_session(sender, intent="reorder")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.LOCK_PDF:
        update_session(sender, intent="lock_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.UNLOCK_PDF:
        update_session(sender, intent="unlock_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.OCR:
        update_session(sender, intent="ocr")
        await send_text_message(settings, sender, "Send me an image or PDF to extract text from.")

    elif intent == Intent.PAGE_NUMBERS:
        update_session(sender, intent="page_numbers")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.WATERMARK:
        update_session(sender, intent="watermark")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.SIGN_PDF:
        update_session(sender, intent="sign_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent == Intent.ENHANCE:
        update_session(sender, intent="enhance")
        await send_text_message(settings, sender, ErrorMessages.bilingual("image_required"))

    elif intent == Intent.REMOVE_BG:
        update_session(sender, intent="remove_bg")
        await send_text_message(settings, sender, ErrorMessages.bilingual("image_required"))

    elif intent == Intent.PDF_ARCHIVE:
        update_session(sender, intent="pdf_archive")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    # Conversion intents
    elif intent in (Intent.PDF_TO_WORD, Intent.PDF_TO_IMAGE, Intent.PDF_TO_PPT, Intent.PDF_TO_EXCEL):
        update_session(sender, intent=intent.value)
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))

    elif intent in (Intent.WORD_TO_PDF, Intent.EXCEL_TO_PDF, Intent.PPT_TO_PDF):
        update_session(sender, intent=intent.value)
        await send_text_message(settings, sender, "Send me the document file to convert to PDF.")

    else:
        await send_text_message(settings, sender, FALLBACK_BODY)


# ── Image message handler ─────────────────────────────────────────

async def _handle_image(message: dict, sender: str, settings: dict) -> None:
    session = get_session(sender)
    image_info = message.get("image", {})
    media_id = image_info.get("id")
    mime_type = image_info.get("mime_type", "image/jpeg")
    caption = image_info.get("caption")

    if not media_id:
        await send_text_message(settings, sender, "Could not read the image. Please try again.")
        return

    caption_intent = detect_intent_from_caption(caption)

    # Start merge mode from caption
    if caption_intent == Intent.MERGE and session.state != "collecting_images":
        update_session(sender, state="collecting_images", intent="merge", images=[])
        add_image_to_session(sender, media_id, mime_type)
        await send_text_message(settings, sender, "Image 1 added. Send more, then type *done* to merge.")
        return

    # Collecting images for merge
    if session.state == "collecting_images":
        add_image_to_session(sender, media_id, mime_type)
        n = session.image_count
        await send_text_message(settings, sender, f"Image {n} added. Send more or type *done* to merge.")
        return

    # OCR on image
    if session.intent == "ocr":
        await _process_ocr_image(sender, media_id, settings)
        return

    # Enhance image
    if session.intent == "enhance":
        await _process_enhance(sender, media_id, settings)
        return

    # Remove background
    if session.intent == "remove_bg":
        await _process_remove_bg(sender, media_id, settings)
        return

    # Sign PDF — user is sending signature image
    if session.intent == "sign_pdf" and session.has_pdf:
        await _process_sign_pdf(sender, media_id, settings)
        return

    # Default: compress or convert to PDF
    compress = session.intent == "compress" or caption_intent == Intent.COMPRESS
    await _process_single_image(sender, media_id, mime_type, compress, settings)
    clear_session(sender)


# ── Document message handler ──────────────────────────────────────

async def _handle_document(message: dict, sender: str, settings: dict) -> None:
    """Handle incoming document files (PDF, Word, Excel, PPT)."""
    session = get_session(sender)
    doc_info = message.get("document", {})
    media_id = doc_info.get("id")
    mime_type = doc_info.get("mime_type", "")
    filename = doc_info.get("filename", "document")

    if not media_id:
        await send_text_message(settings, sender, "Could not read the document. Please try again.")
        return

    is_pdf = mime_type == "application/pdf" or filename.lower().endswith(".pdf")
    is_office = any(mime_type.startswith(t) for t in [
        "application/vnd.openxmlformats", "application/msword",
        "application/vnd.ms-excel", "application/vnd.ms-powerpoint",
    ]) or any(filename.lower().endswith(ext) for ext in [
        ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ])

    # If collecting for merge, add to collection
    if session.state == "collecting_images":
        if is_pdf:
            add_image_to_session(sender, media_id, "application/pdf")
            n = session.image_count
            await send_text_message(settings, sender, f"PDF added ({n} files total). Send more or type *done*.")
        else:
            await send_text_message(settings, sender, "Only images and PDFs can be merged. Send a PDF or image.")
        return

    # Download the document
    start_time = time.time()
    try:
        file_data = await download_media(settings, media_id)
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        await send_text_message(settings, sender, ErrorMessages.bilingual("network_error"))
        return

    if len(file_data) > MAX_FILE_SIZE:
        await send_text_message(settings, sender, ErrorMessages.bilingual("file_too_large", limit="10 MB"))
        return

    # Handle PDF input
    if is_pdf:
        await _handle_pdf_input(sender, file_data, filename, settings, start_time)
        return

    # Handle Office document → convert to PDF
    if is_office:
        await _handle_office_input(sender, file_data, filename, mime_type, settings, start_time)
        return

    await send_text_message(settings, sender, ErrorMessages.bilingual("unsupported_format", expected="PDF, Word, Excel, or PPT"))


async def _handle_pdf_input(sender: str, pdf_data: bytes, filename: str, settings: dict, start_time: float) -> None:
    """Process a PDF based on current session intent."""
    session = get_session(sender)
    intent = session.intent

    # If no specific intent, store PDF and ask what to do
    if not intent or intent not in PDF_INPUT_INTENTS:
        update_session(sender, pdf_data=pdf_data, pdf_filename=filename)
        await send_text_message(
            settings, sender,
            f"Got your PDF ({len(pdf_data) // 1024} KB). What would you like to do with it?\n"
            "Type: *split*, *rotate*, *compress*, *lock*, *unlock*, *ocr*, *watermark*, "
            "*page numbers*, *sign*, *pdf to word*, *pdf to image*, *pdf to ppt*, *pdf to excel*"
        )
        return

    # Intents that need additional input after receiving PDF
    if intent in TEXT_AFTER_PDF_INTENTS:
        update_session(sender, pdf_data=pdf_data, pdf_filename=filename, state="awaiting_input")

        if intent == "split":
            await send_text_message(settings, sender,
                f"PDF received ({_get_pdf_page_count(pdf_data)} pages). "
                "Send page range to extract.\nExample: *1-3,5* or *2,4,6*")
        elif intent == "reorder":
            pages = _get_pdf_page_count(pdf_data)
            await send_text_message(settings, sender,
                f"PDF received ({pages} pages). Send the new page order.\nExample: *3,1,2,4*")
        elif intent == "lock_pdf":
            await send_text_message(settings, sender, ErrorMessages.bilingual("password_set"))
        elif intent == "unlock_pdf":
            await send_text_message(settings, sender, ErrorMessages.bilingual("enter_password"))
        elif intent == "watermark":
            await send_text_message(settings, sender, ErrorMessages.bilingual("watermark_prompt"))
        return

    # Intents that can process immediately
    if intent == "rotate":
        angle = session.rotation_angle or 90
        await _process_pdf_tool(sender, pdf_data, filename, "rotate", settings, start_time, angle=angle)
    elif intent == "compress":
        quality = session.compress_quality or "medium"
        await _process_pdf_tool(sender, pdf_data, filename, "compress", settings, start_time, quality=quality)
    elif intent == "page_numbers":
        await _process_pdf_tool(sender, pdf_data, filename, "page_numbers", settings, start_time)
    elif intent == "sign_pdf":
        update_session(sender, pdf_data=pdf_data, pdf_filename=filename)
        await send_text_message(settings, sender, "PDF received. Now send me your signature image.")
    elif intent == "pdf_archive":
        await _process_pdf_tool(sender, pdf_data, filename, "pdf_archive", settings, start_time)
    elif intent == "ocr":
        await _process_ocr_pdf(sender, pdf_data, settings, start_time)
    elif intent == "pdf_to_word":
        await _process_conversion(sender, pdf_data, filename, "pdf_to_word", settings, start_time)
    elif intent == "pdf_to_image":
        await _process_conversion(sender, pdf_data, filename, "pdf_to_image", settings, start_time)
    elif intent == "pdf_to_ppt":
        await _process_conversion(sender, pdf_data, filename, "pdf_to_ppt", settings, start_time)
    elif intent == "pdf_to_excel":
        await _process_conversion(sender, pdf_data, filename, "pdf_to_excel", settings, start_time)
    else:
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))


async def _handle_office_input(sender: str, file_data: bytes, filename: str, mime_type: str, settings: dict, start_time: float) -> None:
    """Convert Office document to PDF."""
    from utils.pdf_converter import office_to_pdf

    conversion_id = str(uuid.uuid4())
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "docx"

    try:
        log_conversion(conversion_id, sender, "pending", len(file_data), feature="office_to_pdf", input_type=ext)
        await send_text_message(settings, sender, f"Converting {filename} to PDF...")

        pdf_data = office_to_pdf(file_data, ext)
        elapsed = int((time.time() - start_time) * 1000)

        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")
        out_name = filename.rsplit(".", 1)[0] + ".pdf"
        await send_document_message(settings, sender, pdf_media_id, filename=out_name, caption="Here's your PDF!")

        log_conversion(conversion_id, sender, "success", len(file_data),
                       feature="office_to_pdf", input_type=ext, output_type="pdf",
                       processing_time_ms=elapsed, output_file_size=len(pdf_data))
        clear_session(sender)

    except Exception as e:
        logger.error(f"Office to PDF failed: {e}")
        log_conversion(conversion_id, sender, "failed", len(file_data),
                       feature="office_to_pdf", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("conversion_failed"))
        clear_session(sender)


# ── Interactive message handler ───────────────────────────────────

async def _handle_interactive(message: dict, sender: str, settings: dict) -> None:
    interactive = message.get("interactive", {})

    # Handle list replies
    list_reply = interactive.get("list_reply", {})
    if list_reply:
        list_id = list_reply.get("id", "")
        intent = detect_intent_from_list(list_id)
        if intent != Intent.UNKNOWN:
            # Re-dispatch as text intent
            await _dispatch_intent(sender, intent, settings)
            return

    # Handle button replies
    button_reply = interactive.get("button_reply", {})
    if button_reply:
        button_id = button_reply.get("id", "")
        await _handle_button_reply(sender, button_id, settings)
        return

    await send_text_message(settings, sender, HELP_TEXT)


async def _handle_button_reply(sender: str, button_id: str, settings: dict) -> None:
    session = get_session(sender)

    # Rotation angle buttons
    if button_id.startswith("btn_rotate_"):
        angle = int(button_id.replace("btn_rotate_", ""))
        update_session(sender, intent="rotate", rotation_angle=angle)
        await send_text_message(settings, sender, f"Rotation set to {angle}°. Now send me the PDF.")
        return

    # Compression quality buttons
    if button_id.startswith("btn_quality_"):
        quality = button_id.replace("btn_quality_", "")
        update_session(sender, intent="compress", compress_quality=quality)
        await send_text_message(settings, sender, f"Quality set to {quality}. Now send me the PDF or image.")
        return

    # Standard button intents
    intent = detect_intent_from_button(button_id)
    await _dispatch_intent(sender, intent, settings)


async def _dispatch_intent(sender: str, intent: Intent, settings: dict) -> None:
    """Dispatch an intent from button/list reply to the appropriate handler."""
    if intent == Intent.CONVERT:
        update_session(sender, intent="convert")
        await send_text_message(settings, sender, "Send me the image to convert to PDF.")
    elif intent == Intent.COMPRESS:
        update_session(sender, state="idle", intent="compress", images=[])
        await send_text_message(settings, sender, COMPRESS_READY_TEXT)
    elif intent == Intent.MERGE:
        update_session(sender, state="collecting_images", intent="merge", images=[])
        await send_text_message(settings, sender, MERGE_STARTED_TEXT)
    elif intent == Intent.HELP:
        await send_text_message(settings, sender, HELP_TEXT)
    elif intent == Intent.UNKNOWN:
        await send_text_message(settings, sender, HELP_TEXT)
    elif intent == Intent.ROTATE:
        update_session(sender, intent="rotate")
        await send_button_message(settings, sender, "Choose rotation angle:", [
            {"id": "btn_rotate_90", "title": "90°"},
            {"id": "btn_rotate_180", "title": "180°"},
            {"id": "btn_rotate_270", "title": "270°"},
        ])
    elif intent == Intent.SPLIT:
        update_session(sender, intent="split")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.REORDER:
        update_session(sender, intent="reorder")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.LOCK_PDF:
        update_session(sender, intent="lock_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.UNLOCK_PDF:
        update_session(sender, intent="unlock_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.OCR:
        update_session(sender, intent="ocr")
        await send_text_message(settings, sender, "Send me an image or PDF to extract text from.")
    elif intent == Intent.PAGE_NUMBERS:
        update_session(sender, intent="page_numbers")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.WATERMARK:
        update_session(sender, intent="watermark")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.SIGN_PDF:
        update_session(sender, intent="sign_pdf")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent == Intent.ENHANCE:
        update_session(sender, intent="enhance")
        await send_text_message(settings, sender, ErrorMessages.bilingual("image_required"))
    elif intent == Intent.REMOVE_BG:
        update_session(sender, intent="remove_bg")
        await send_text_message(settings, sender, ErrorMessages.bilingual("image_required"))
    elif intent == Intent.PDF_ARCHIVE:
        update_session(sender, intent="pdf_archive")
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent in (Intent.PDF_TO_WORD, Intent.PDF_TO_IMAGE, Intent.PDF_TO_PPT, Intent.PDF_TO_EXCEL):
        update_session(sender, intent=intent.value)
        await send_text_message(settings, sender, ErrorMessages.bilingual("send_pdf_first"))
    elif intent in (Intent.WORD_TO_PDF, Intent.EXCEL_TO_PDF, Intent.PPT_TO_PDF):
        update_session(sender, intent=intent.value)
        await send_text_message(settings, sender, "Send me the document file to convert to PDF.")
    elif intent == Intent.GREETING:
        await _send_feature_menu(sender, settings)
    elif intent == Intent.CANCEL:
        clear_session(sender)
        await send_text_message(settings, sender, CANCEL_TEXT)
    elif intent == Intent.DONE:
        await _handle_done(sender, settings)
    elif intent == Intent.STATUS:
        await _handle_status(sender, settings)
    else:
        await send_text_message(settings, sender, FALLBACK_BODY)


# ── Awaited input handler ─────────────────────────────────────────

async def _handle_awaited_input(sender: str, text: str, settings: dict) -> None:
    """Handle text input when we're waiting for page spec, password, or watermark text."""
    session = get_session(sender)
    intent = session.intent

    # Allow cancel even while awaiting input
    if detect_intent(text) == Intent.CANCEL:
        clear_session(sender)
        await send_text_message(settings, sender, CANCEL_TEXT)
        return

    start_time = time.time()

    if intent == "split":
        update_session(sender, page_spec=text)
        await _process_pdf_tool(sender, session.pdf_data, session.pdf_filename, "split", settings, start_time, page_spec=text)

    elif intent == "reorder":
        update_session(sender, page_spec=text)
        await _process_pdf_tool(sender, session.pdf_data, session.pdf_filename, "reorder", settings, start_time, order_spec=text)

    elif intent == "lock_pdf":
        update_session(sender, pdf_password=text)
        await _process_pdf_tool(sender, session.pdf_data, session.pdf_filename, "lock_pdf", settings, start_time, password=text)

    elif intent == "unlock_pdf":
        update_session(sender, pdf_password=text)
        await _process_pdf_tool(sender, session.pdf_data, session.pdf_filename, "unlock_pdf", settings, start_time, password=text)

    elif intent == "watermark":
        update_session(sender, watermark_text=text)
        await _process_pdf_tool(sender, session.pdf_data, session.pdf_filename, "watermark", settings, start_time, watermark_text=text)

    else:
        await send_text_message(settings, sender, "I wasn't expecting text input right now. Type *cancel* to start over.")


# ── Done / Status handlers ────────────────────────────────────────

async def _handle_done(sender: str, settings: dict) -> None:
    session = get_session(sender)
    if session.state == "collecting_images" and session.image_count > 0:
        await _process_merge(sender, settings)
    elif session.state == "collecting_images":
        await send_text_message(settings, sender, "You haven't sent any files yet. Send images/PDFs first, then type *done*.")
    else:
        await send_text_message(settings, sender, "Nothing to finish right now. Send me a file or type *help*.")


async def _handle_status(sender: str, settings: dict) -> None:
    session = get_session(sender)
    if session.state == "collecting_images":
        n = session.image_count
        word = "file" if n == 1 else "files"
        await send_text_message(settings, sender, f"You've sent *{n}* {word} so far. Send more or type *done* to merge.")
    else:
        await send_text_message(settings, sender, "No active session. Send me a file or type *help* to see options.")


# ── Feature Menu ──────────────────────────────────────────────────

async def _send_feature_menu(sender: str, settings: dict) -> None:
    """Send the main feature menu as a WhatsApp list message."""
    await send_list_message(
        settings, sender,
        body_text=GREETING_BODY,
        button_text="See Features",
        sections=FEATURE_SECTIONS,
        header="DocBot",
        footer="Free & Private — nothing stored",
    )


async def _send_more_features_menu(sender: str, settings: dict) -> None:
    """Send the extended features menu."""
    await send_list_message(
        settings, sender,
        body_text="More tools available:",
        button_text="More Features",
        sections=FEATURE_SECTIONS_2,
        footer="Type any feature name or send a file",
    )


# ── Processing functions ──────────────────────────────────────────

async def _process_single_image(
    sender: str, media_id: str, mime_type: str, compress: bool, settings: dict
) -> None:
    """Download a single image, convert to PDF, and send back."""
    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_conversion(conversion_id, sender, "pending", 0, feature="compress" if compress else "convert")

        image_data = await download_media(settings, media_id)
        file_size = len(image_data)

        if file_size > MAX_FILE_SIZE:
            await send_text_message(settings, sender, ErrorMessages.bilingual("file_too_large", limit="10 MB"))
            log_conversion(conversion_id, sender, "failed", file_size, error_message="File too large")
            return

        pdf_data = convert_image_to_pdf(image_data, mime_type, compress=compress)
        elapsed = int((time.time() - start_time) * 1000)

        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")

        label = "compressed_" if compress else "converted_"
        filename = f"{label}{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        caption = "Compressed PDF" if compress else "Here's your PDF!"
        await send_document_message(settings, sender, pdf_media_id, filename=filename, caption=caption)

        log_conversion(conversion_id, sender, "success", file_size,
                       feature="compress" if compress else "convert",
                       input_type=mime_type, output_type="pdf",
                       processing_time_ms=elapsed, output_file_size=len(pdf_data))

    except Exception as e:
        logger.error(f"Error processing image for {sender}: {e}")
        elapsed = int((time.time() - start_time) * 1000)
        log_conversion(conversion_id, sender, "failed", 0, error_message=str(e), processing_time_ms=elapsed)
        try:
            await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
        except Exception:
            pass


async def _process_merge(sender: str, settings: dict) -> None:
    """Download all collected files, merge into one PDF, and send back."""
    session = get_session(sender)
    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        update_session(sender, state="processing")
        log_conversion(conversion_id, sender, "pending", 0, feature="merge")

        await send_text_message(settings, sender, f"Merging {session.image_count} files, please wait...")

        files: List[Tuple[bytes, str]] = []
        total_size = 0

        for img_ref in session.images:
            data = await download_media(settings, img_ref["media_id"])
            total_size += len(data)
            files.append((data, img_ref["mime_type"]))

        if total_size > MAX_FILE_SIZE * 5:
            await send_text_message(settings, sender, ErrorMessages.bilingual("file_too_large", limit="50 MB total"))
            log_conversion(conversion_id, sender, "failed", total_size, feature="merge", error_message="Total size too large")
            clear_session(sender)
            return

        # Check if any PDFs in the mix
        has_pdfs = any(mt == "application/pdf" for _, mt in files)

        if has_pdfs:
            from utils.pdf_converter import merge_mixed
            pdf_data = merge_mixed(files)
        else:
            image_list = [(data, mt) for data, mt in files]
            pdf_data = merge_images_to_pdf(image_list)

        elapsed = int((time.time() - start_time) * 1000)

        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")

        filename = f"merged_{len(files)}files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        caption = f"Merged PDF — {len(files)} files"
        await send_document_message(settings, sender, pdf_media_id, filename=filename, caption=caption)

        log_conversion(conversion_id, sender, "success", total_size,
                       feature="merge", output_type="pdf",
                       processing_time_ms=elapsed, output_file_size=len(pdf_data))

    except Exception as e:
        logger.error(f"Error merging for {sender}: {e}")
        elapsed = int((time.time() - start_time) * 1000)
        log_conversion(conversion_id, sender, "failed", 0, feature="merge",
                       error_message=str(e), processing_time_ms=elapsed)
        try:
            await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
        except Exception:
            pass
    finally:
        clear_session(sender)


async def _process_pdf_tool(
    sender: str, pdf_data: bytes, filename: str, tool: str,
    settings: dict, start_time: float, **kwargs
) -> None:
    """Apply a PDF tool and send the result back."""
    from utils import pdf_tools

    conversion_id = str(uuid.uuid4())

    try:
        log_conversion(conversion_id, sender, "pending", len(pdf_data), feature=tool, input_type="pdf")

        if tool == "split":
            result = pdf_tools.split_pdf(pdf_data, kwargs["page_spec"])
            out_name = f"split_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "Here are your extracted pages!"
        elif tool == "rotate":
            result = pdf_tools.rotate_pdf(pdf_data, kwargs.get("angle", 90))
            out_name = f"rotated_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = f"Rotated {kwargs.get('angle', 90)}°"
        elif tool == "reorder":
            result = pdf_tools.reorder_pdf(pdf_data, kwargs["order_spec"])
            out_name = f"reordered_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "Pages reordered!"
        elif tool == "lock_pdf":
            result = pdf_tools.protect_pdf(pdf_data, kwargs["password"])
            out_name = f"protected_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "PDF is now password-protected!"
        elif tool == "unlock_pdf":
            result = pdf_tools.unlock_pdf(pdf_data, kwargs["password"])
            out_name = f"unlocked_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "PDF unlocked!"
        elif tool == "compress":
            result = pdf_tools.compress_pdf(pdf_data, kwargs.get("quality", "medium"))
            out_name = f"compressed_{datetime.now().strftime('%H%M%S')}.pdf"
            orig_kb = len(pdf_data) // 1024
            new_kb = len(result) // 1024
            caption = f"Compressed: {orig_kb} KB → {new_kb} KB"
        elif tool == "page_numbers":
            result = pdf_tools.add_page_numbers(pdf_data)
            out_name = f"numbered_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "Page numbers added!"
        elif tool == "watermark":
            result = pdf_tools.add_watermark(pdf_data, kwargs["watermark_text"])
            out_name = f"watermarked_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "Watermark added!"
        elif tool == "pdf_archive":
            result = pdf_tools.make_pdf_archive(pdf_data)
            out_name = f"archived_{datetime.now().strftime('%H%M%S')}.pdf"
            caption = "PDF archived with metadata!"
        else:
            raise ValueError(f"Unknown tool: {tool}")

        elapsed = int((time.time() - start_time) * 1000)

        media_id = await upload_media(settings, result, "application/pdf")
        await send_document_message(settings, sender, media_id, filename=out_name, caption=caption)

        log_conversion(conversion_id, sender, "success", len(pdf_data),
                       feature=tool, input_type="pdf", output_type="pdf",
                       processing_time_ms=elapsed, output_file_size=len(result))

    except ValueError as e:
        log_conversion(conversion_id, sender, "failed", len(pdf_data),
                       feature=tool, error_message=str(e))
        await send_text_message(settings, sender, str(e))
    except Exception as e:
        logger.error(f"PDF tool '{tool}' failed for {sender}: {e}")
        log_conversion(conversion_id, sender, "failed", len(pdf_data),
                       feature=tool, error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


async def _process_conversion(
    sender: str, pdf_data: bytes, filename: str, conversion_type: str,
    settings: dict, start_time: float
) -> None:
    """Convert PDF to another format and send back."""
    from utils import pdf_converter

    conversion_id = str(uuid.uuid4())

    try:
        log_conversion(conversion_id, sender, "pending", len(pdf_data), feature=conversion_type, input_type="pdf")
        await send_text_message(settings, sender, "Converting, please wait...")

        if conversion_type == "pdf_to_word":
            result = pdf_converter.pdf_to_word(pdf_data)
            out_name = filename.rsplit(".", 1)[0] + ".docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            caption = "Here's your Word document!"

        elif conversion_type == "pdf_to_image":
            images = pdf_converter.pdf_to_images(pdf_data)
            elapsed = int((time.time() - start_time) * 1000)

            # Send each page as an image
            for img_data, img_name in images:
                img_media_id = await upload_media(settings, img_data, "image/jpeg", filename=img_name)
                await send_image_message(settings, sender, img_media_id, caption=img_name)

            log_conversion(conversion_id, sender, "success", len(pdf_data),
                           feature=conversion_type, output_type="image",
                           processing_time_ms=elapsed)
            clear_session(sender)
            return

        elif conversion_type == "pdf_to_ppt":
            result = pdf_converter.pdf_to_ppt(pdf_data)
            out_name = filename.rsplit(".", 1)[0] + ".pptx"
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            caption = "Here's your PowerPoint!"

        elif conversion_type == "pdf_to_excel":
            result = pdf_converter.pdf_to_excel(pdf_data)
            out_name = filename.rsplit(".", 1)[0] + ".xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            caption = "Here's your Excel file!"

        else:
            raise ValueError(f"Unknown conversion: {conversion_type}")

        elapsed = int((time.time() - start_time) * 1000)

        media_id = await upload_media(settings, result, mime, filename=out_name)
        await send_document_message(settings, sender, media_id, filename=out_name, caption=caption)

        log_conversion(conversion_id, sender, "success", len(pdf_data),
                       feature=conversion_type, input_type="pdf", output_type=out_name.rsplit(".", 1)[-1],
                       processing_time_ms=elapsed, output_file_size=len(result))

    except Exception as e:
        logger.error(f"Conversion '{conversion_type}' failed: {e}")
        log_conversion(conversion_id, sender, "failed", len(pdf_data),
                       feature=conversion_type, error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("conversion_failed"))
    finally:
        clear_session(sender)


async def _process_ocr_image(sender: str, media_id: str, settings: dict) -> None:
    """OCR on an image."""
    from utils.ocr import extract_text_from_image

    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_conversion(conversion_id, sender, "pending", 0, feature="ocr", input_type="image")
        image_data = await download_media(settings, media_id)

        text = extract_text_from_image(image_data)
        elapsed = int((time.time() - start_time) * 1000)

        if text:
            if len(text) > 4000:
                # Send as text file
                from utils.ocr import create_text_file
                txt_data = create_text_file(text)
                txt_media_id = await upload_media(settings, txt_data, "text/plain", filename="extracted_text.txt")
                await send_document_message(settings, sender, txt_media_id,
                                            filename="extracted_text.txt", caption=f"Extracted {len(text)} characters")
            else:
                await send_text_message(settings, sender, f"*Extracted text:*\n\n{text}")

            log_conversion(conversion_id, sender, "success", len(image_data),
                           feature="ocr", processing_time_ms=elapsed)
        else:
            await send_text_message(settings, sender, ErrorMessages.bilingual("no_text_found"))
            log_conversion(conversion_id, sender, "failed", len(image_data),
                           feature="ocr", error_message="No text found")

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        log_conversion(conversion_id, sender, "failed", 0, feature="ocr", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


async def _process_ocr_pdf(sender: str, pdf_data: bytes, settings: dict, start_time: float) -> None:
    """OCR on a PDF."""
    from utils.ocr import extract_text_from_pdf, create_text_file

    conversion_id = str(uuid.uuid4())

    try:
        log_conversion(conversion_id, sender, "pending", len(pdf_data), feature="ocr", input_type="pdf")
        await send_text_message(settings, sender, "Extracting text, please wait...")

        text = extract_text_from_pdf(pdf_data)
        elapsed = int((time.time() - start_time) * 1000)

        if text:
            if len(text) > 4000:
                txt_data = create_text_file(text)
                txt_media_id = await upload_media(settings, txt_data, "text/plain", filename="extracted_text.txt")
                await send_document_message(settings, sender, txt_media_id,
                                            filename="extracted_text.txt", caption=f"Extracted {len(text)} characters")
            else:
                await send_text_message(settings, sender, f"*Extracted text:*\n\n{text}")

            log_conversion(conversion_id, sender, "success", len(pdf_data),
                           feature="ocr", processing_time_ms=elapsed)
        else:
            await send_text_message(settings, sender, ErrorMessages.bilingual("no_text_found"))
            log_conversion(conversion_id, sender, "failed", len(pdf_data),
                           feature="ocr", error_message="No text found")

    except Exception as e:
        logger.error(f"OCR on PDF failed: {e}")
        log_conversion(conversion_id, sender, "failed", len(pdf_data),
                       feature="ocr", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


async def _process_enhance(sender: str, media_id: str, settings: dict) -> None:
    """Enhance a document image."""
    from utils.image_tools import enhance_document

    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_conversion(conversion_id, sender, "pending", 0, feature="enhance", input_type="image")
        image_data = await download_media(settings, media_id)

        enhanced = enhance_document(image_data)
        elapsed = int((time.time() - start_time) * 1000)

        img_media_id = await upload_media(settings, enhanced, "image/png", filename="enhanced.png")
        await send_image_message(settings, sender, img_media_id, caption="Enhanced image!")

        log_conversion(conversion_id, sender, "success", len(image_data),
                       feature="enhance", processing_time_ms=elapsed, output_file_size=len(enhanced))

    except Exception as e:
        logger.error(f"Enhance failed: {e}")
        log_conversion(conversion_id, sender, "failed", 0, feature="enhance", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


async def _process_remove_bg(sender: str, media_id: str, settings: dict) -> None:
    """Remove background from image."""
    from utils.image_tools import remove_background

    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_conversion(conversion_id, sender, "pending", 0, feature="remove_bg", input_type="image")
        image_data = await download_media(settings, media_id)

        result = remove_background(image_data)
        elapsed = int((time.time() - start_time) * 1000)

        img_media_id = await upload_media(settings, result, "image/png", filename="no_background.png")
        await send_image_message(settings, sender, img_media_id, caption="Background removed!")

        log_conversion(conversion_id, sender, "success", len(image_data),
                       feature="remove_bg", processing_time_ms=elapsed, output_file_size=len(result))

    except Exception as e:
        logger.error(f"Remove BG failed: {e}")
        log_conversion(conversion_id, sender, "failed", 0, feature="remove_bg", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


async def _process_sign_pdf(sender: str, sig_media_id: str, settings: dict) -> None:
    """Add signature image to the stored PDF."""
    from utils.pdf_tools import sign_pdf

    session = get_session(sender)
    conversion_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_conversion(conversion_id, sender, "pending", len(session.pdf_data), feature="sign_pdf")

        sig_data = await download_media(settings, sig_media_id)
        result = sign_pdf(session.pdf_data, sig_data)
        elapsed = int((time.time() - start_time) * 1000)

        media_id = await upload_media(settings, result, "application/pdf")
        await send_document_message(settings, sender, media_id,
                                    filename=f"signed_{datetime.now().strftime('%H%M%S')}.pdf",
                                    caption="Signature added!")

        log_conversion(conversion_id, sender, "success", len(session.pdf_data),
                       feature="sign_pdf", processing_time_ms=elapsed, output_file_size=len(result))

    except Exception as e:
        logger.error(f"Sign PDF failed: {e}")
        log_conversion(conversion_id, sender, "failed", 0, feature="sign_pdf", error_message=str(e))
        await send_text_message(settings, sender, ErrorMessages.bilingual("processing_failed"))
    finally:
        clear_session(sender)


# ── Helpers ────────────────────────────────────────────────────────

def _get_pdf_page_count(pdf_data: bytes) -> int:
    """Get page count from PDF data."""
    try:
        from utils.pdf_tools import get_pdf_info
        info = get_pdf_info(pdf_data)
        return info["pages"]
    except Exception:
        return 0
