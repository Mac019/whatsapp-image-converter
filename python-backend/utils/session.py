"""
Per-user session state manager for WhatsApp conversations.
Tracks conversation context, collected images/documents, and active intents.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Session timeout in seconds (10 minutes)
SESSION_TTL = 600


@dataclass
class Session:
    phone: str
    state: str = "idle"  # idle, collecting_images, awaiting_confirmation, processing, awaiting_input
    intent: Optional[str] = None
    images: list = field(default_factory=list)  # list of {"media_id": str, "mime_type": str}
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # PDF data for tools that need to hold a PDF between messages
    pdf_data: Optional[bytes] = None
    pdf_media_id: Optional[str] = None
    pdf_filename: Optional[str] = None

    # Tool-specific parameters
    watermark_text: Optional[str] = None
    pdf_password: Optional[str] = None
    signature_image: Optional[bytes] = None
    compress_quality: Optional[str] = None  # "low", "medium", "high"
    rotation_angle: Optional[int] = None  # 90, 180, 270
    page_spec: Optional[str] = None  # "1-3,5" for split or "3,1,2" for reorder

    # Document files (Word/Excel/PPT received for conversion)
    document_data: Optional[bytes] = None
    document_mime_type: Optional[str] = None
    document_filename: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.updated_at) > SESSION_TTL

    @property
    def image_count(self) -> int:
        return len(self.images)

    @property
    def has_pdf(self) -> bool:
        return self.pdf_data is not None

    @property
    def has_document(self) -> bool:
        return self.document_data is not None

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
    """
    session = get_session(phone)

    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)

    session.touch()
    return session


def add_image_to_session(phone: str, media_id: str, mime_type: str) -> Session:
    """Add an image reference to the session's image collection."""
    session = get_session(phone)
    session.images.append({"media_id": media_id, "mime_type": mime_type})
    session.touch()
    logger.info(f"Added image to session for {phone}, total: {session.image_count}")
    return session


def clear_session(phone: str) -> Session:
    """Reset a session to idle state, clearing all collected data."""
    session = get_session(phone)
    session.state = "idle"
    session.intent = None
    session.images = []
    session.pdf_data = None
    session.pdf_media_id = None
    session.pdf_filename = None
    session.watermark_text = None
    session.pdf_password = None
    session.signature_image = None
    session.compress_quality = None
    session.rotation_angle = None
    session.page_spec = None
    session.document_data = None
    session.document_mime_type = None
    session.document_filename = None
    session.touch()
    logger.info(f"Session cleared for {phone}")
    return session


def get_active_session_count() -> int:
    """Return count of non-expired sessions."""
    return sum(1 for s in _sessions.values() if not s.is_expired)


def get_all_phones() -> List[str]:
    """Return all phone numbers that have ever had a session."""
    return list(_sessions.keys())


def cleanup_expired() -> int:
    """Remove all expired sessions from memory."""
    expired = [phone for phone, s in _sessions.items() if s.is_expired]
    for phone in expired:
        del _sessions[phone]

    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")

    return len(expired)
