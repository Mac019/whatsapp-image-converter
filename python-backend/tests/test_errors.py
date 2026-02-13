"""Tests for error messages."""

from utils.errors import ErrorMessages


class TestErrorMessages:
    def test_get_english(self):
        msg = ErrorMessages.get("processing_failed", "en")
        assert "processing failed" in msg.lower()

    def test_get_hindi(self):
        msg = ErrorMessages.get("processing_failed", "hi")
        assert "Maaf" in msg or "processing" in msg

    def test_get_with_format(self):
        msg = ErrorMessages.get("file_too_large", "en", limit="10 MB")
        assert "10 MB" in msg

    def test_get_unknown_key(self):
        msg = ErrorMessages.get("nonexistent_key", "en")
        assert "error" in msg.lower()

    def test_bilingual(self):
        msg = ErrorMessages.bilingual("processing_failed")
        assert "\n" in msg  # Should have both languages

    def test_bilingual_with_format(self):
        msg = ErrorMessages.bilingual("file_too_large", limit="5 MB")
        assert "5 MB" in msg

    def test_all_keys_have_en(self):
        for key in ErrorMessages.MESSAGES:
            assert "en" in ErrorMessages.MESSAGES[key], f"Missing 'en' for key: {key}"

    def test_all_keys_have_hi(self):
        for key in ErrorMessages.MESSAGES:
            assert "hi" in ErrorMessages.MESSAGES[key], f"Missing 'hi' for key: {key}"
