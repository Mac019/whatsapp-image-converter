"""
Keyword-based intent detection for WhatsApp messages.
Detects user intent from text messages using pattern matching.
"""

from enum import Enum
from typing import List, Optional, Tuple


class Intent(Enum):
    CONVERT = "convert"
    COMPRESS = "compress"
    MERGE = "merge"
    GREETING = "greeting"
    HELP = "help"
    STATUS = "status"
    CANCEL = "cancel"
    DONE = "done"
    UNKNOWN = "unknown"


# Keyword mappings — order matters (first match wins)
# More specific patterns should come before general ones
INTENT_KEYWORDS: List[Tuple[Intent, List[str]]] = [
    (Intent.CANCEL, [
        "cancel", "reset", "stop", "clear", "start over", "nevermind",
        "never mind", "abort",
    ]),
    (Intent.DONE, [
        "done", "finish", "that's all", "thats all", "send it",
        "send them", "go ahead", "ready", "bas", "ho gaya",
    ]),
    (Intent.COMPRESS, [
        "compress", "compressed", "small", "smaller", "reduce",
        "low quality", "lightweight", "light weight", "compact",
        "shrink", "tiny", "chhota",
    ]),
    (Intent.MERGE, [
        "merge", "combine", "join", "multiple", "together",
        "one pdf", "single pdf", "all in one", "ek pdf",
    ]),
    (Intent.STATUS, [
        "status", "how many", "count", "kitne",
    ]),
    (Intent.GREETING, [
        "hi", "hello", "hey", "hii", "hiii", "namaste",
        "start", "hola", "sup", "yo",
    ]),
    (Intent.HELP, [
        "help", "menu", "commands", "what can you do",
        "options", "kya kar sakte",
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
    Detect intent from an image caption.
    Only returns COMPRESS or MERGE intents (the ones relevant to images).
    Returns None if no actionable intent found in caption.

    Args:
        caption: The image caption text

    Returns:
        Intent if actionable keyword found, None otherwise
    """
    if not caption:
        return None

    intent = detect_intent(caption)

    if intent in (Intent.COMPRESS, Intent.MERGE):
        return intent

    return None


def detect_intent_from_button(button_id: str) -> Intent:
    """
    Map a WhatsApp interactive button ID to an intent.

    Args:
        button_id: The button reply ID (e.g., "btn_convert")

    Returns:
        Mapped Intent enum value
    """
    button_map = {
        "btn_convert": Intent.CONVERT,
        "btn_compress": Intent.COMPRESS,
        "btn_merge": Intent.MERGE,
        "btn_help": Intent.HELP,
    }
    return button_map.get(button_id, Intent.UNKNOWN)
