"""
WhatsApp Image to PDF Converter - FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.whatsapp import (
    verify_webhook_token,
    download_media,
    upload_media,
    send_document_message,
    send_text_message,
)
from utils.converter import convert_image_to_pdf
from utils.storage import (
    save_settings,
    get_settings,
    log_conversion,
    get_stats,
    get_conversions,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Image to PDF Converter")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SettingsModel(BaseModel):
    whatsapp_business_account_id: str
    phone_number_id: str
    access_token: str
    webhook_verify_token: str
    admin_password: Optional[str] = None


# ============== WEBHOOK ENDPOINTS ==============

@app.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Webhook verification endpoint for Meta WhatsApp Cloud API.
    Meta sends a GET request to verify the webhook URL.
    """
    settings = get_settings()
    verify_token = settings.get("webhook_verify_token", "")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning(f"Webhook verification failed. Mode: {hub_mode}, Token match: {hub_verify_token == verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/whatsapp")
async def receive_message(request: Request):
    """
    Receive incoming messages from WhatsApp.
    Processes images and converts them to PDF.
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")
        
        # Extract message data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "no messages"}
        
        message = messages[0]
        sender = message.get("from")
        message_type = message.get("type")
        
        settings = get_settings()
        
        if message_type == "image":
            await process_image_message(message, sender, settings)
        else:
            # Send helpful message for non-image messages
            await send_text_message(
                settings,
                sender,
                "👋 Hi! Send me an image and I'll convert it to PDF for you!"
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


async def process_image_message(message: dict, sender: str, settings: dict):
    """Process an incoming image and convert it to PDF."""
    conversion_id = str(uuid.uuid4())
    
    try:
        # Log pending conversion
        log_conversion(conversion_id, sender, "pending", 0)
        
        # Get image info
        image = message.get("image", {})
        media_id = image.get("id")
        mime_type = image.get("mime_type", "image/jpeg")
        
        if not media_id:
            raise ValueError("No media ID in message")
        
        logger.info(f"Processing image {media_id} from {sender}")
        
        # Download image from Meta
        image_data = await download_media(settings, media_id)
        file_size = len(image_data)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            await send_text_message(
                settings, sender,
                "❌ Image too large! Please send an image under 10MB."
            )
            log_conversion(conversion_id, sender, "failed", file_size)
            return
        
        # Convert to PDF
        pdf_data = convert_image_to_pdf(image_data, mime_type)
        
        # Upload PDF to Meta
        pdf_media_id = await upload_media(settings, pdf_data, "application/pdf")
        
        # Send PDF back
        await send_document_message(
            settings, sender, pdf_media_id,
            filename=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        # Log successful conversion
        log_conversion(conversion_id, sender, "success", file_size)
        logger.info(f"Successfully converted image for {sender}")
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        log_conversion(conversion_id, sender, "failed", 0)
        
        # Send error message to user
        try:
            await send_text_message(
                settings, sender,
                "❌ Sorry, I couldn't convert your image. Please try again with a JPG or PNG image."
            )
        except:
            pass


# ============== ADMIN API ENDPOINTS ==============

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Get conversion statistics for the dashboard."""
    return get_stats()


@app.get("/api/admin/conversions")
async def get_admin_conversions():
    """Get list of recent conversions."""
    return get_conversions()


@app.get("/api/admin/settings")
async def get_admin_settings():
    """Get current settings (tokens masked)."""
    settings = get_settings()
    # Mask sensitive data
    if settings.get("access_token"):
        token = settings["access_token"]
        settings["access_token"] = token[:10] + "..." + token[-4:] if len(token) > 14 else "***"
    return settings


@app.post("/api/admin/settings")
async def save_admin_settings(settings: SettingsModel):
    """Save Meta WhatsApp API settings."""
    try:
        save_settings(settings.model_dump())
        return {"status": "success", "message": "Settings saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== HEALTH CHECK ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
