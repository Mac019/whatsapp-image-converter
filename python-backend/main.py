"""
DocBot — WhatsApp Document Tool
Free alternative to Adobe Scan & iLovePDF via WhatsApp.
Run with: uvicorn main:app --reload --port 8000
"""

import json
import sys
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from utils.flow import handle_message
from utils.session import cleanup_expired, get_active_session_count
from utils.storage import (
    save_settings,
    get_settings,
    get_stats,
    get_conversions,
    get_timeseries,
    get_feature_usage,
    get_user_analytics,
    get_error_tracking,
    export_conversions_csv,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DocBot — WhatsApp Document Tool")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_start_time = datetime.now()


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
    """Webhook verification endpoint for Meta WhatsApp Cloud API."""
    settings = get_settings()
    verify_token = settings.get("webhook_verify_token", "")

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)

    logger.warning(f"Webhook verification failed. Mode: {hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/whatsapp")
async def receive_message(request: Request):
    """Receive incoming messages from WhatsApp."""
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

        cleanup_expired()

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


# ============== ANALYTICS ENDPOINTS ==============

@app.get("/api/admin/analytics/timeseries")
async def get_analytics_timeseries(days: int = Query(30, ge=1, le=365)):
    """Get conversion counts by date for the last N days."""
    return get_timeseries(days)


@app.get("/api/admin/analytics/features")
async def get_analytics_features():
    """Get feature usage breakdown."""
    return get_feature_usage()


@app.get("/api/admin/analytics/users")
async def get_analytics_users():
    """Get user-level analytics."""
    return get_user_analytics()


@app.get("/api/admin/analytics/errors")
async def get_analytics_errors():
    """Get error tracking data."""
    return get_error_tracking()


# ============== SYSTEM HEALTH ==============

@app.get("/api/admin/system/health")
async def get_system_health():
    """Get system resource usage."""
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = (datetime.now() - _start_time).total_seconds()

        return {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": round(mem.used / (1024 * 1024)),
            "memory_total_mb": round(mem.total / (1024 * 1024)),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "uptime_seconds": int(uptime),
            "python_version": sys.version.split()[0],
            "active_sessions": get_active_session_count(),
        }
    except ImportError:
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 0,
            "disk_percent": 0,
            "disk_used_gb": 0,
            "disk_total_gb": 0,
            "uptime_seconds": int((datetime.now() - _start_time).total_seconds()),
            "python_version": sys.version.split()[0],
            "active_sessions": get_active_session_count(),
        }


# ============== EXPORT ==============

@app.get("/api/admin/conversions/export")
async def export_conversions():
    """Export all conversions as CSV."""
    csv_data = export_conversions_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=conversions.csv"},
    )


# ============== HEALTH CHECK ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
