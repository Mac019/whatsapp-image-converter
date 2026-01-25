"""
Simple file-based storage for settings and conversion logs.
In production, replace with a proper database.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / "data"
SETTINGS_FILE = STORAGE_DIR / "settings.json"
CONVERSIONS_FILE = STORAGE_DIR / "conversions.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to file."""
    # Don't overwrite existing token if new one is masked
    existing = get_settings()
    
    if settings.get("access_token", "").startswith("EAA") or not existing.get("access_token"):
        # New valid token or no existing token
        pass
    elif "..." in settings.get("access_token", ""):
        # Masked token, keep existing
        settings["access_token"] = existing.get("access_token", "")
    
    # Remove password from stored settings (just used for validation)
    settings.pop("admin_password", None)
    
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    
    logger.info("Settings saved successfully")


def get_settings() -> Dict[str, Any]:
    """Load settings from file."""
    if not SETTINGS_FILE.exists():
        return {}
    
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return {}


def log_conversion(
    conversion_id: str,
    phone_number: str,
    status: str,
    file_size: int
) -> None:
    """Log a conversion to the conversions file."""
    conversions = _load_conversions()
    
    # Find existing or create new
    existing = next((c for c in conversions if c["id"] == conversion_id), None)
    
    if existing:
        existing["status"] = status
        existing["file_size"] = file_size
        existing["updated_at"] = datetime.now().isoformat()
    else:
        conversions.append({
            "id": conversion_id,
            "phone_number": phone_number,
            "status": status,
            "file_size": file_size,
            "timestamp": datetime.now().isoformat(),
        })
    
    # Keep only last 1000 conversions
    conversions = conversions[-1000:]
    
    _save_conversions(conversions)


def get_stats() -> Dict[str, Any]:
    """Get conversion statistics."""
    conversions = _load_conversions()
    
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    
    total = len(conversions)
    today = sum(
        1 for c in conversions
        if datetime.fromisoformat(c["timestamp"]) >= today_start
    )
    success = sum(1 for c in conversions if c["status"] == "success")
    pending = sum(1 for c in conversions if c["status"] == "pending")
    
    success_rate = round((success / total * 100) if total > 0 else 0, 1)
    
    return {
        "total_conversions": total,
        "today_conversions": today,
        "success_rate": success_rate,
        "pending": pending,
    }


def get_conversions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent conversions."""
    conversions = _load_conversions()
    # Return most recent first
    return sorted(
        conversions,
        key=lambda x: x["timestamp"],
        reverse=True
    )[:limit]


def _load_conversions() -> List[Dict[str, Any]]:
    """Load conversions from file."""
    if not CONVERSIONS_FILE.exists():
        return []
    
    try:
        with open(CONVERSIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading conversions: {e}")
        return []


def _save_conversions(conversions: List[Dict[str, Any]]) -> None:
    """Save conversions to file."""
    with open(CONVERSIONS_FILE, "w") as f:
        json.dump(conversions, f, indent=2)
