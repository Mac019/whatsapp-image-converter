"""
User-facing error messages in English and Hindi.
Maps internal error codes to friendly messages sent back via WhatsApp.
"""


class ErrorMessages:
    """Bilingual user-facing error messages."""

    MESSAGES = {
        "file_too_large": {
            "en": "File too large. Please send a file under {limit}.",
            "hi": "File bahut badi hai. Kripya {limit} se chhoti file bhejein.",
        },
        "unsupported_format": {
            "en": "Unsupported file format. Please send a {expected}.",
            "hi": "Yeh format support nahi hai. Kripya {expected} bhejein.",
        },
        "processing_failed": {
            "en": "Sorry, processing failed. Please try again.",
            "hi": "Maaf kijiye, processing fail ho gayi. Dobara try karein.",
        },
        "no_text_found": {
            "en": "No text found in the document.",
            "hi": "Document mein koi text nahi mila.",
        },
        "invalid_pages": {
            "en": "Invalid page range. Example: 1-3,5 or 1,2,3",
            "hi": "Galat page range. Udaharan: 1-3,5 ya 1,2,3",
        },
        "wrong_password": {
            "en": "Wrong password. Please try again.",
            "hi": "Galat password. Dobara try karein.",
        },
        "pdf_required": {
            "en": "Please send a PDF file for this operation.",
            "hi": "Kripya is kaam ke liye PDF file bhejein.",
        },
        "image_required": {
            "en": "Please send an image for this operation.",
            "hi": "Kripya is kaam ke liye ek image bhejein.",
        },
        "no_images": {
            "en": "No images collected yet. Send images first.",
            "hi": "Abhi tak koi image nahi aayi. Pehle images bhejein.",
        },
        "send_pdf_first": {
            "en": "Please send the PDF file first.",
            "hi": "Pehle PDF file bhejein.",
        },
        "timeout": {
            "en": "Processing took too long. Try a smaller file.",
            "hi": "Processing mein bahut samay laga. Chhoti file try karein.",
        },
        "network_error": {
            "en": "Network error. Please try again in a moment.",
            "hi": "Network mein dikkat. Thodi der baad try karein.",
        },
        "conversion_failed": {
            "en": "Conversion failed. The file may be corrupted or protected.",
            "hi": "Conversion fail. File kharab ya protected ho sakti hai.",
        },
        "password_set": {
            "en": "Please send the password you want to set.",
            "hi": "Kripya password bhejein jo aap set karna chahte hain.",
        },
        "enter_password": {
            "en": "This PDF is password-protected. Please send the password.",
            "hi": "Yeh PDF password-protected hai. Kripya password bhejein.",
        },
        "merge_minimum": {
            "en": "Need at least 2 files to merge. Send more files.",
            "hi": "Merge ke liye kam se kam 2 files chahiye. Aur files bhejein.",
        },
        "watermark_prompt": {
            "en": "Send the text you want as a watermark.",
            "hi": "Watermark ke liye text bhejein.",
        },
        "page_order_prompt": {
            "en": "Send the page order. Example: 3,1,2,4",
            "hi": "Page order bhejein. Udaharan: 3,1,2,4",
        },
        "rotation_prompt": {
            "en": "Choose rotation angle:",
            "hi": "Rotation angle chunein:",
        },
        "compress_quality_prompt": {
            "en": "Choose compression quality:",
            "hi": "Compression quality chunein:",
        },
        "feature_ready": {
            "en": "Ready! Now send me the file.",
            "hi": "Taiyar! Ab mujhe file bhejein.",
        },
    }

    @classmethod
    def get(cls, key: str, lang: str = "en", **kwargs) -> str:
        """
        Get a user-facing message.

        Args:
            key: Message key from MESSAGES dict
            lang: Language code ("en" or "hi")
            **kwargs: Format string substitutions

        Returns:
            Formatted message string
        """
        msg_dict = cls.MESSAGES.get(key, {})
        msg = msg_dict.get(lang, msg_dict.get("en", "An error occurred."))
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg

    @classmethod
    def bilingual(cls, key: str, **kwargs) -> str:
        """Get message in both English and Hindi."""
        en = cls.get(key, "en", **kwargs)
        hi = cls.get(key, "hi", **kwargs)
        if en == hi:
            return en
        return f"{en}\n{hi}"
