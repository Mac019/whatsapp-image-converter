"""
WhatsApp Image to PDF Converter - FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""

import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.flow import handle_message
from utils.session import cleanup_expired
from utils.storage import (
    save_settings,
    get_settings,
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
    Delegates all message handling to the flow controller.
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

        # Periodically clean up expired sessions
        cleanup_expired()

        # Extract message data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no messages"}

        message = messages[0]
        sender = message.get("from")
        settings = get_settings()

        await handle_message(message, sender, settings)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


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
