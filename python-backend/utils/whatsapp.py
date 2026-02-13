"""
WhatsApp Cloud API utility functions.
Handles all communication with Meta's WhatsApp Business API.
All outbound API calls use exponential backoff retry.
"""

import httpx
import logging
from typing import Dict, List, Optional

from utils.retry import retry

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v18.0"


async def verify_webhook_token(received_token: str, expected_token: str) -> bool:
    """Verify the webhook token matches."""
    return received_token == expected_token


@retry(retries=3, base_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_typing_indicator(settings: dict, recipient: str, message_id: str) -> None:
    """
    Mark a message as read (blue ticks) and show a typing indicator.
    """
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BASE_URL}/{phone_number_id}/messages",
                headers=headers,
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                    "typing_indicator": {
                        "type": "text",
                    },
                },
                timeout=10.0,
            )
        logger.info(f"Sent typing indicator to {recipient}")
    except Exception as e:
        logger.warning(f"Failed to send typing indicator: {e}")


@retry(retries=3, base_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def download_media(settings: dict, media_id: str) -> bytes:
    """
    Download media from WhatsApp using the media ID.
    First gets the media URL, then downloads the actual file.
    """
    access_token = settings.get("access_token")

    if not access_token:
        raise ValueError("Access token not configured")

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        # Step 1: Get media URL
        url_response = await client.get(
            f"{BASE_URL}/{media_id}",
            headers=headers,
            timeout=30.0
        )
        url_response.raise_for_status()
        media_url = url_response.json().get("url")

        if not media_url:
            raise ValueError("Could not get media URL")

        logger.info(f"Downloading media from: {media_url[:50]}...")

        # Step 2: Download the actual file
        file_response = await client.get(
            media_url,
            headers=headers,
            timeout=60.0
        )
        file_response.raise_for_status()

        return file_response.content


@retry(retries=3, base_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def upload_media(settings: dict, file_data: bytes, mime_type: str, filename: str = "document.pdf") -> str:
    """
    Upload media to WhatsApp and return the media ID.
    """
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/media",
            headers=headers,
            files={
                "file": (filename, file_data, mime_type),
            },
            data={
                "messaging_product": "whatsapp",
                "type": mime_type,
            },
            timeout=60.0
        )
        response.raise_for_status()

        media_id = response.json().get("id")
        logger.info(f"Uploaded media with ID: {media_id}")

        return media_id


@retry(retries=2, base_delay=0.5, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_document_message(
    settings: dict,
    recipient: str,
    media_id: str,
    filename: str = "document.pdf",
    caption: Optional[str] = None
):
    """Send a document (PDF, Word, etc.) to a WhatsApp user."""
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename,
        }
    }

    if caption:
        payload["document"]["caption"] = caption

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/messages",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()

        logger.info(f"Sent document to {recipient}")
        return response.json()


@retry(retries=2, base_delay=0.5, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_button_message(
    settings: dict,
    recipient: str,
    body_text: str,
    buttons: List[Dict],
):
    """
    Send an interactive button message (max 3 buttons).
    """
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"]},
                    }
                    for btn in buttons[:3]
                ]
            },
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/messages",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()

        logger.info(f"Sent button message to {recipient}")
        return response.json()


@retry(retries=2, base_delay=0.5, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_list_message(
    settings: dict,
    recipient: str,
    body_text: str,
    button_text: str,
    sections: List[Dict],
    header: Optional[str] = None,
    footer: Optional[str] = None,
):
    """
    Send an interactive list message to a WhatsApp user.
    Supports up to 10 items across sections.

    Args:
        settings: API settings dict
        recipient: Phone number to send to
        body_text: Message body text
        button_text: Text on the button that opens the list (max 20 chars)
        sections: List of {"title": str, "rows": [{"id": str, "title": str, "description": str}]}
        header: Optional header text
        footer: Optional footer text
    """
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    interactive = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_text[:20],
            "sections": sections,
        },
    }

    if header:
        interactive["header"] = {"type": "text", "text": header}
    if footer:
        interactive["footer"] = {"text": footer}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "interactive",
        "interactive": interactive,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/messages",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()

        logger.info(f"Sent list message to {recipient}")
        return response.json()


@retry(retries=2, base_delay=0.5, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_text_message(settings: dict, recipient: str, text: str):
    """Send a text message to a WhatsApp user."""
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/messages",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()

        logger.info(f"Sent text message to {recipient}")
        return response.json()


@retry(retries=2, base_delay=0.5, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def send_image_message(settings: dict, recipient: str, media_id: str, caption: Optional[str] = None):
    """Send an image message to a WhatsApp user."""
    access_token = settings.get("access_token")
    phone_number_id = settings.get("phone_number_id")

    if not access_token or not phone_number_id:
        raise ValueError("Access token or phone number ID not configured")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    image_payload = {"id": media_id}
    if caption:
        image_payload["caption"] = caption

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "image",
        "image": image_payload,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{phone_number_id}/messages",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()

        logger.info(f"Sent image message to {recipient}")
        return response.json()
