"""
Conversation flow controller.
Routes incoming WhatsApp messages through intent detection and session state
to determine the appropriate action.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Tuple

from utils.intent import Intent, detect_intent, detect_intent_from_caption, detect_intent_from_button
from utils.session import get_session, update_session, add_image_to_session, clear_session
from utils.converter import convert_image_to_pdf, merge_images_to_pdf
from utils.whatsapp import (
    download_media,
    upload_media,
    send_document_message,
    send_text_message,
    send_button_message,
    send_typing_indicator,
)
from utils.storage import log_conversion

logger = logging.getLogger(__name__)

# ── Message templates ──────────────────────────────────────────────

HELP_TEXT = (
    "*Here's what I can do:*\n\n"
    "*Convert to PDF* — Just send me any image\n"
    "*Compress PDF* — Type *compress* then send image\n"
    "*Merge PDFs* — Type *merge*, send multiple images, then *done*\n"
    "*Cancel* — Type *cancel* to start over\n\n"
    "Or just send an image and I'll convert it right away."
)

MERGE_STARTED_TEXT = "Send me the images you want to combine into one PDF.\nType *done* when you're ready."

COMPRESS_READY_TEXT = "Send me an image and I'll create a smaller, compressed PDF."

CANCEL_TEXT = "Cancelled. Send me an image or type *help* to see options."

GREETING_BODY = (
    "Hi! I'm your *PDF Bot*.\n"
    "What would you like to do?"
)

GREETING_BUTTONS = [
    {"id": "btn_convert", "title": "Convert to PDF"},
    {"id": "btn_compress", "title": "Compress PDF"},
    {"id": "btn_merge", "title": "Merge Images"},
]

FALLBACK_BODY = (
    "I didn't understand that.\n"
    "Pick an option below or send me an image directly:"
)

FALLBACK_BUTTONS = [
    {"id": "btn_convert", "title": "Convert to PDF"},
    {"id": "btn_compress", "title": "Compress PDF"},
    {"id": "btn_merge", "title": "Merge Images"},
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Main entry point ───────────────────────────────────────────────

async def handle_message(message: dict, sender: str, settings: dict) -> None:
    """
    Main message handler. Routes a WhatsApp message to the correct action
    based on message type, detected intent, and current session state.
    """
    # Show typing indicator + blue ticks immediately
    message_id = message.get("id")
    if message_id:
        await send_typing_indicator(settings, sender, message_id)

    message_type = message.get("type")

    if message_type == "text":
        text = message.get("text", {}).get("body", "")
        await _handle_text(sender, text, settings)

    elif message_type == "image":
        await _handle_image(message, sender, settings)

    elif message_type == "interactive":
        await _handle_interactive(message, sender, settings)

    else:
        # Stickers, audio, video, location, etc. → show options
        await send_button_message(
            settings, sender,
            "I can only work with images and text.\nPick an option:",
            FALLBACK_BUTTONS,
        )


# ── Text message handler ──────────────────────────────────────────

async def _handle_text(sender: str, text: str, settings: dict) -> None:
    intent = detect_intent(text)
    session = get_session(sender)

    if intent == Intent.GREETING:
        await send_button_message(settings, sender, GREETING_BODY, GREETING_BUTTONS)

    elif intent == Intent.HELP:
        await send_text_message(settings, sender, HELP_TEXT)

    elif intent == Intent.CANCEL:
        clear_session(sender)
        await send_text_message(settings, sender, CANCEL_TEXT)

    elif intent == Intent.COMPRESS:
        update_session(sender, state="idle", intent="compress", images=[])
        await send_text_message(settings, sender, COMPRESS_READY_TEXT)

    elif intent == Intent.MERGE:
        update_session(sender, state="collecting_images", intent="merge", images=[])
        await send_text_message(settings, sender, MERGE_STARTED_TEXT)

    elif intent == Intent.DONE:
        if session.state == "collecting_images" and session.image_count > 0:
            await _process_merge(sender, settings)
        elif session.state == "collecting_images":
            await send_text_message(
                settings, sender,
                "You haven't sent any images yet. Send images first, then type *done*."
            )
        else:
            await send_text_message(
                settings, sender,
                "Nothing to finish right now. Send me an image or type *help*."
            )

    elif intent == Intent.STATUS:
        if session.state == "collecting_images":
            n = session.image_count
            word = "image" if n == 1 else "images"
            await send_text_message(
                settings, sender,
                f"You've sent *{n}* {word} so far. Send more or type *done* to merge."
            )
        else:
            await send_text_message(
                settings, sender,
                "No active session. Send me an image or type *help* to see options."
            )

    elif intent == Intent.CONVERT:
        # User said "convert" / "pdf" without an image — prompt them
        update_session(sender, intent="convert")
        await send_text_message(
            settings, sender,
            "Sure! Send me the image you'd like to convert to PDF."
        )

    else:
        # UNKNOWN intent → show interactive buttons
        await send_button_message(settings, sender, FALLBACK_BODY, FALLBACK_BUTTONS)


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

    # Check caption for intent overrides
    caption_intent = detect_intent_from_caption(caption)

    # If caption says "merge" and we're not yet collecting, start merge mode with this image
    if caption_intent == Intent.MERGE and session.state != "collecting_images":
        update_session(sender, state="collecting_images", intent="merge", images=[])
        add_image_to_session(sender, media_id, mime_type)
        await send_text_message(
            settings, sender,
            "Image 1 added. Send more images, then type *done* to merge."
        )
        return

    # If we're in merge/collecting mode, add image to collection
    if session.state == "collecting_images":
        add_image_to_session(sender, media_id, mime_type)
        n = session.image_count
        await send_text_message(
            settings, sender,
            f"Image {n} added. Send more or type *done* to merge them into one PDF."
        )
        return

    # Determine if compress mode (from session or caption)
    compress = (
        session.intent == "compress"
        or caption_intent == Intent.COMPRESS
    )

    # Single image → convert (or compress) to PDF immediately
    await _process_single_image(sender, media_id, mime_type, compress, settings)

    # Reset session after processing
    clear_session(sender)


# ── Interactive button reply handler ───────────────────────────────

async def _handle_interactive(message: dict, sender: str, settings: dict) -> None:
    interactive = message.get("interactive", {})
    button_reply = interactive.get("button_reply", {})
    button_id = button_reply.get("id", "")

    intent = detect_intent_from_button(button_id)

    if intent == Intent.CONVERT:
        update_session(sender, intent="convert")
        await send_text_message(
            settings, sender,
            "Send me the image you'd like to convert to PDF."
        )

    elif intent == Intent.COMPRESS:
        update_session(sender, state="idle", intent="compress", images=[])
        await send_text_message(settings, sender, COMPRESS_READY_TEXT)

    elif intent == Intent.MERGE:
        update_session(sender, state="collecting_images", intent="merge", images=[])
        await send_text_message(settings, sender, MERGE_STARTED_TEXT)

    elif intent == Intent.HELP:
        await send_text_message(settings, sender, HELP_TEXT)

    else:
        await send_text_message(settings, sender, HELP_TEXT)


# ── Processing functions ──────────────────────────────────────────

async def _process_single_image(
    sender: str, media_id: str, mime_type: str, compress: bool, settings: dict
) -> None:
    """Download a single image, convert to PDF, and send back."""
    conversion_id = str(uuid.uuid4())

    try:
        log_conversion(conversion_id, sender, "pending", 0)

        image_data = await download_media(settings, media_id)
        file_size = len(image_data)

        if file_size > MAX_FILE_SIZE:
            await send_text_message(
                settings, sender,
                "Image too large. Please send an image under 10 MB."
            )
            log_conversion(conversion_id, sender, "failed", file_size)
            return

        pdf_data = convert_image_to_pdf(image_data, mime_type, compress=compress)

        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")

        label = "compressed_" if compress else "converted_"
        filename = f"{label}{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        caption = "Compressed PDF" if compress else "Here's your PDF!"
        await send_document_message(settings, sender, pdf_media_id, filename=filename, caption=caption)

        log_conversion(conversion_id, sender, "success", file_size)
        logger.info(f"Processed single image for {sender} (compress={compress})")

    except Exception as e:
        logger.error(f"Error processing image for {sender}: {e}")
        log_conversion(conversion_id, sender, "failed", 0)
        try:
            await send_text_message(
                settings, sender,
                "Sorry, I couldn't process that image. Please try again with a JPG or PNG."
            )
        except Exception:
            pass


async def _process_merge(sender: str, settings: dict) -> None:
    """Download all collected images, merge into one PDF, and send back."""
    session = get_session(sender)
    conversion_id = str(uuid.uuid4())

    try:
        update_session(sender, state="processing")
        log_conversion(conversion_id, sender, "pending", 0)

        await send_text_message(
            settings, sender,
            f"Merging {session.image_count} images into one PDF, please wait..."
        )

        # Download all images
        image_list: List[Tuple[bytes, str]] = []
        total_size = 0

        for img_ref in session.images:
            data = await download_media(settings, img_ref["media_id"])
            total_size += len(data)
            image_list.append((data, img_ref["mime_type"]))

        if total_size > MAX_FILE_SIZE * 5:  # 50 MB total limit for merges
            await send_text_message(
                settings, sender,
                "Total image size is too large. Try with fewer or smaller images."
            )
            log_conversion(conversion_id, sender, "failed", total_size)
            clear_session(sender)
            return

        pdf_data = merge_images_to_pdf(image_list)

        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")

        filename = f"merged_{len(image_list)}pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        caption = f"Merged PDF — {len(image_list)} pages"
        await send_document_message(settings, sender, pdf_media_id, filename=filename, caption=caption)

        log_conversion(conversion_id, sender, "success", total_size)
        logger.info(f"Merged {len(image_list)} images for {sender}")

    except Exception as e:
        logger.error(f"Error merging images for {sender}: {e}")
        log_conversion(conversion_id, sender, "failed", 0)
        try:
            await send_text_message(
                settings, sender,
                "Sorry, something went wrong while merging. Please try again."
            )
        except Exception:
            pass

    finally:
        clear_session(sender)
