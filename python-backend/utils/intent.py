"""
Keyword-based intent detection for WhatsApp messages.
Detects user intent from text messages using pattern matching.
Supports English and Hindi keywords for all features.
"""

from enum import Enum
from typing import List, Optional, Tuple


class Intent(Enum):
    # Original intents
    CONVERT = "convert"
    COMPRESS = "compress"
    MERGE = "merge"
    GREETING = "greeting"
    HELP = "help"
    STATUS = "status"
    CANCEL = "cancel"
    DONE = "done"

    # PDF tools
    SPLIT = "split"
    ROTATE = "rotate"
    REORDER = "reorder"
    LOCK_PDF = "lock_pdf"
    UNLOCK_PDF = "unlock_pdf"
    OCR = "ocr"

    # Conversions
    PDF_TO_WORD = "pdf_to_word"
    PDF_TO_IMAGE = "pdf_to_image"
    PDF_TO_PPT = "pdf_to_ppt"
    PDF_TO_EXCEL = "pdf_to_excel"
    WORD_TO_PDF = "word_to_pdf"
    EXCEL_TO_PDF = "excel_to_pdf"
    PPT_TO_PDF = "ppt_to_pdf"

    # Advanced
    PAGE_NUMBERS = "page_numbers"
    WATERMARK = "watermark"
    ENHANCE = "enhance"
    SIGN_PDF = "sign_pdf"
    REMOVE_BG = "remove_bg"
    PDF_ARCHIVE = "pdf_archive"

    UNKNOWN = "unknown"


# Keyword mappings — order matters (first match wins)
# More specific patterns should come before general ones
INTENT_KEYWORDS: List[Tuple[Intent, List[str]]] = [
    (Intent.CANCEL, [
        "cancel", "reset", "stop", "clear", "start over", "nevermind",
        "never mind", "abort", "band karo", "ruko",
    ]),
    (Intent.DONE, [
        "done", "finish", "that's all", "thats all", "send it",
        "send them", "go ahead", "ready", "bas", "ho gaya",
    ]),

    # PDF to other formats (check before generic "pdf")
    (Intent.PDF_TO_WORD, [
        "pdf to word", "pdf to doc", "pdf to docx", "convert to word",
        "pdf se word", "word mein badlo",
    ]),
    (Intent.PDF_TO_IMAGE, [
        "pdf to image", "pdf to jpg", "pdf to jpeg", "pdf to png",
        "pdf to photo", "pdf se image", "pdf se photo",
    ]),
    (Intent.PDF_TO_PPT, [
        "pdf to ppt", "pdf to powerpoint", "pdf to presentation",
        "pdf to slide", "pdf se ppt", "pdf se slide",
    ]),
    (Intent.PDF_TO_EXCEL, [
        "pdf to excel", "pdf to xlsx", "pdf to spreadsheet",
        "pdf to csv", "pdf se excel",
    ]),

    # Other formats to PDF
    (Intent.WORD_TO_PDF, [
        "word to pdf", "doc to pdf", "docx to pdf",
        "word se pdf", "document to pdf",
    ]),
    (Intent.EXCEL_TO_PDF, [
        "excel to pdf", "xlsx to pdf", "spreadsheet to pdf",
        "excel se pdf",
    ]),
    (Intent.PPT_TO_PDF, [
        "ppt to pdf", "powerpoint to pdf", "presentation to pdf",
        "slide to pdf", "ppt se pdf",
    ]),

    # PDF tools
    (Intent.SPLIT, [
        "split", "extract pages", "cut pages", "page extract",
        "split pdf", "pages nikalo", "page alag karo",
    ]),
    (Intent.ROTATE, [
        "rotate", "turn", "flip", "ghumao", "rotate pdf",
    ]),
    (Intent.REORDER, [
        "reorder", "rearrange", "change order", "page order",
        "reorder pages", "order badlo",
    ]),
    (Intent.UNLOCK_PDF, [
        "unlock", "remove password", "decrypt", "unprotect",
        "unlock pdf", "password hatao",
    ]),
    (Intent.LOCK_PDF, [
        "lock", "protect", "password protect", "encrypt",
        "lock pdf", "pdf lock", "password lagao",
    ]),
    (Intent.OCR, [
        "ocr", "extract text", "read text", "text extract",
        "scan text", "text nikalo", "padhke batao",
    ]),
    (Intent.COMPRESS, [
        "compress", "compressed", "small", "smaller", "reduce",
        "low quality", "lightweight", "light weight", "compact",
        "shrink", "tiny", "chhota", "compress pdf",
    ]),
    (Intent.MERGE, [
        "merge", "combine", "join", "multiple", "together",
        "one pdf", "single pdf", "all in one", "ek pdf",
    ]),

    # Advanced features
    (Intent.PAGE_NUMBERS, [
        "page number", "page numbers", "add numbers",
        "number pages", "page no", "page numbering",
    ]),
    (Intent.WATERMARK, [
        "watermark", "stamp", "mark", "watermark add",
        "watermark lagao",
    ]),
    (Intent.ENHANCE, [
        "enhance", "improve", "clean", "sharpen", "brighten",
        "fix image", "sudhar", "saaf karo",
    ]),
    (Intent.SIGN_PDF, [
        "sign", "signature", "add signature", "sign pdf",
        "hastakshar", "dastkhat",
    ]),
    (Intent.REMOVE_BG, [
        "remove bg", "remove background", "background remove",
        "no background", "transparent", "bg hatao",
    ]),
    (Intent.PDF_ARCHIVE, [
        "archive", "pdf/a", "pdfa", "archival",
        "long term", "preserve",
    ]),

    # Generic intents (last — less specific)
    (Intent.STATUS, [
        "status", "how many", "count", "kitne",
    ]),
    (Intent.GREETING, [
        "hi", "hello", "hey", "hii", "hiii", "namaste",
        "start", "hola", "sup",
    ]),
    (Intent.HELP, [
        "help", "menu", "commands", "what can you do",
        "options", "kya kar sakte", "features",
    ]),
    (Intent.CONVERT, [
        "convert", "pdf", "make pdf", "image to pdf",
    ]),
]


def detect_intent(text: Optional[str]) -> Intent:
    """
    Detect user intent from a text message.

    Args:
        text: The user's text message

    Returns:
        Detected Intent enum value
    """
    if not text:
        return Intent.UNKNOWN

    text_lower = text.strip().lower()

    if not text_lower:
        return Intent.UNKNOWN

    for intent, keywords in INTENT_KEYWORDS:
        for keyword in keywords:
            if keyword in text_lower:
                return intent

    return Intent.UNKNOWN


def detect_intent_from_caption(caption: Optional[str]) -> Optional[Intent]:
    """
    Detect intent from an image/document caption.
    Only returns intents relevant to file operations.
    Returns None if no actionable intent found.
    """
    if not caption:
        return None

    intent = detect_intent(caption)

    # Intents that can be triggered from a caption
    caption_intents = {
        Intent.COMPRESS, Intent.MERGE, Intent.ENHANCE,
        Intent.OCR, Intent.REMOVE_BG, Intent.SIGN_PDF,
    }

    if intent in caption_intents:
        return intent

    return None


def detect_intent_from_button(button_id: str) -> Intent:
    """
    Map a WhatsApp interactive button ID to an intent.
    """
    button_map = {
        "btn_convert": Intent.CONVERT,
        "btn_compress": Intent.COMPRESS,
        "btn_merge": Intent.MERGE,
        "btn_help": Intent.HELP,
        # Rotation angles
        "btn_rotate_90": Intent.ROTATE,
        "btn_rotate_180": Intent.ROTATE,
        "btn_rotate_270": Intent.ROTATE,
        # Compression quality
        "btn_quality_low": Intent.COMPRESS,
        "btn_quality_medium": Intent.COMPRESS,
        "btn_quality_high": Intent.COMPRESS,
    }
    return button_map.get(button_id, Intent.UNKNOWN)


def detect_intent_from_list(list_reply_id: str) -> Intent:
    """
    Map a WhatsApp list reply ID to an intent.
    Used for the feature menu list message.
    """
    list_map = {
        # Image tools
        "list_convert": Intent.CONVERT,
        "list_compress": Intent.COMPRESS,
        "list_merge": Intent.MERGE,
        "list_enhance": Intent.ENHANCE,
        "list_remove_bg": Intent.REMOVE_BG,
        # PDF tools
        "list_split": Intent.SPLIT,
        "list_rotate": Intent.ROTATE,
        "list_reorder": Intent.REORDER,
        "list_lock": Intent.LOCK_PDF,
        "list_unlock": Intent.UNLOCK_PDF,
        "list_ocr": Intent.OCR,
        "list_page_numbers": Intent.PAGE_NUMBERS,
        "list_watermark": Intent.WATERMARK,
        "list_sign": Intent.SIGN_PDF,
        "list_archive": Intent.PDF_ARCHIVE,
        # Conversions
        "list_pdf_to_word": Intent.PDF_TO_WORD,
        "list_pdf_to_image": Intent.PDF_TO_IMAGE,
        "list_pdf_to_ppt": Intent.PDF_TO_PPT,
        "list_pdf_to_excel": Intent.PDF_TO_EXCEL,
        "list_word_to_pdf": Intent.WORD_TO_PDF,
        "list_excel_to_pdf": Intent.EXCEL_TO_PDF,
        "list_ppt_to_pdf": Intent.PPT_TO_PDF,
    }
    return list_map.get(list_reply_id, Intent.UNKNOWN)
