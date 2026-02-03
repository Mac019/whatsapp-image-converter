"""
Per-user session state manager for WhatsApp conversations.
Tracks conversation context, collected images, and active intents.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Session timeout in seconds (10 minutes)
SESSION_TTL = 600


@dataclass
class Session:
    phone: str
    state: str = "idle"  # idle, collecting_images, awaiting_confirmation, processing
    intent: Optional[str] = None  # compress, merge, convert, or None
    images: list = field(default_factory=list)  # list of {"media_id": str, "mime_type": str}
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.updated_at) > SESSION_TTL

    @property
    def image_count(self) -> int:
        return len(self.images)

    def touch(self):
        """Refresh the session timestamp."""
        self.updated_at = time.time()


# In-memory session store
_sessions: Dict[str, Session] = {}


def get_session(phone: str) -> Session:
    """
    Get or create a session for a phone number.
    Expired sessions are automatically replaced with fresh ones.
    """
    session = _sessions.get(phone)

    if session is None or session.is_expired:
        if session and session.is_expired:
            logger.info(f"Session expired for {phone}, creating new one")
        session = Session(phone=phone)
        _sessions[phone] = session

    session.touch()
    return session


def update_session(phone: str, **kwargs) -> Session:
    """
    Update session fields and refresh timestamp.

    Args:
        phone: User's phone number
        **kwargs: Fields to update (state, intent, etc.)

    Returns:
        Updated session
    """
    session = get_session(phone)

    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)

    session.touch()
    return session


def add_image_to_session(phone: str, media_id: str, mime_type: str) -> Session:
    """
    Add an image reference to the session's image collection.

    Args:
        phone: User's phone number
        media_id: WhatsApp media ID
        mime_type: Image MIME type

    Returns:
        Updated session
    """
    session = get_session(phone)
    session.images.append({"media_id": media_id, "mime_type": mime_type})
    session.touch()
    logger.info(f"Added image to session for {phone}, total: {session.image_count}")
    return session


def clear_session(phone: str) -> Session:
    """
    Reset a session to idle state, clearing images and intent.

    Returns:
        Fresh session
    """
    session = get_session(phone)
    session.state = "idle"
    session.intent = None
    session.images = []
    session.touch()
    logger.info(f"Session cleared for {phone}")
    return session


def cleanup_expired() -> int:
    """
    Remove all expired sessions from memory.

    Returns:
        Number of sessions removed
    """
    expired = [phone for phone, s in _sessions.items() if s.is_expired]
    for phone in expired:
        del _sessions[phone]

    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")

    return len(expired)
