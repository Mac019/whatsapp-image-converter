"""Tests for session management."""

import time
import pytest
from utils.session import (
    get_session, update_session, add_image_to_session,
    clear_session, get_active_session_count, cleanup_expired,
    _sessions, SESSION_TTL,
)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Clear all sessions before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


class TestGetSession:
    def test_creates_new_session(self):
        session = get_session("1234567890")
        assert session.phone == "1234567890"
        assert session.state == "idle"
        assert session.intent is None
        assert session.images == []

    def test_returns_existing_session(self):
        s1 = get_session("1234567890")
        s1.intent = "convert"
        s2 = get_session("1234567890")
        assert s2.intent == "convert"
        assert s1 is s2

    def test_replaces_expired_session(self):
        s1 = get_session("1234567890")
        s1.intent = "merge"
        s1.updated_at = time.time() - SESSION_TTL - 1
        s2 = get_session("1234567890")
        assert s2.intent is None  # Fresh session
        assert s1 is not s2


class TestUpdateSession:
    def test_updates_fields(self):
        get_session("111")
        session = update_session("111", state="collecting_images", intent="merge")
        assert session.state == "collecting_images"
        assert session.intent == "merge"

    def test_ignores_invalid_fields(self):
        get_session("111")
        session = update_session("111", nonexistent_field="value")
        assert not hasattr(session, "nonexistent_field")

    def test_touches_timestamp(self):
        session = get_session("111")
        old_time = session.updated_at
        time.sleep(0.01)
        update_session("111", intent="compress")
        assert session.updated_at >= old_time


class TestAddImageToSession:
    def test_adds_image(self):
        get_session("111")
        session = add_image_to_session("111", "media_123", "image/jpeg")
        assert session.image_count == 1
        assert session.images[0] == {"media_id": "media_123", "mime_type": "image/jpeg"}

    def test_adds_multiple_images(self):
        get_session("111")
        add_image_to_session("111", "m1", "image/jpeg")
        add_image_to_session("111", "m2", "image/png")
        session = add_image_to_session("111", "m3", "image/webp")
        assert session.image_count == 3


class TestClearSession:
    def test_resets_everything(self):
        session = get_session("111")
        session.state = "processing"
        session.intent = "merge"
        session.images = [{"media_id": "x", "mime_type": "image/jpeg"}]
        session.pdf_data = b"fake"
        session.watermark_text = "DRAFT"
        session.rotation_angle = 90

        cleared = clear_session("111")
        assert cleared.state == "idle"
        assert cleared.intent is None
        assert cleared.images == []
        assert cleared.pdf_data is None
        assert cleared.watermark_text is None
        assert cleared.rotation_angle is None


class TestSessionProperties:
    def test_is_expired(self):
        session = get_session("111")
        assert not session.is_expired
        session.updated_at = time.time() - SESSION_TTL - 1
        assert session.is_expired

    def test_image_count(self):
        session = get_session("111")
        assert session.image_count == 0
        add_image_to_session("111", "m1", "image/jpeg")
        assert session.image_count == 1

    def test_has_pdf(self):
        session = get_session("111")
        assert not session.has_pdf
        session.pdf_data = b"fake pdf"
        assert session.has_pdf


class TestCleanupExpired:
    def test_removes_expired(self):
        s1 = get_session("111")
        s2 = get_session("222")
        s1.updated_at = time.time() - SESSION_TTL - 1
        removed = cleanup_expired()
        assert removed == 1
        assert "111" not in _sessions
        assert "222" in _sessions

    def test_no_expired(self):
        get_session("111")
        removed = cleanup_expired()
        assert removed == 0


class TestGetActiveSessionCount:
    def test_counts_active(self):
        get_session("111")
        get_session("222")
        assert get_active_session_count() == 2

    def test_excludes_expired(self):
        get_session("111")
        s2 = get_session("222")
        s2.updated_at = time.time() - SESSION_TTL - 1
        assert get_active_session_count() == 1
