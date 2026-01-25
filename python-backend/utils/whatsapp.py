"""
WhatsApp Cloud API utility functions.
Handles all communication with Meta's WhatsApp Business API.
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v18.0"


async def verify_webhook_token(received_token: str, expected_token: str) -> bool:
    """Verify the webhook token matches."""
    return received_token == expected_token


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


async def upload_media(settings: dict, file_data: bytes, mime_type: str) -> str:
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
                "file": ("document.pdf", file_data, mime_type),
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


async def send_document_message(
    settings: dict,
    recipient: str,
    media_id: str,
    filename: str = "document.pdf",
    caption: Optional[str] = None
):
    """
    Send a document (PDF) to a WhatsApp user.
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


async def send_text_message(settings: dict, recipient: str, text: str):
    """
    Send a text message to a WhatsApp user.
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
