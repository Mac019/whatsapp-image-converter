"""
File-based storage for settings and conversion logs.
Enhanced with feature tracking, processing time, and error logging.
"""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / "data"
SETTINGS_FILE = STORAGE_DIR / "settings.json"
CONVERSIONS_FILE = STORAGE_DIR / "conversions.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)


# ── Settings ───────────────────────────────────────────────────────

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to file."""
    existing = get_settings()

    if settings.get("access_token", "").startswith("EAA") or not existing.get("access_token"):
        pass
    elif "..." in settings.get("access_token", ""):
        settings["access_token"] = existing.get("access_token", "")

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


# ── Conversion Logging ─────────────────────────────────────────────

def log_conversion(
    conversion_id: str,
    phone_number: str,
    status: str,
    file_size: int,
    feature: str = "convert",
    input_type: str = "",
    output_type: str = "",
    processing_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    output_file_size: Optional[int] = None,
) -> None:
    """Log a conversion with extended fields."""
    conversions = _load_conversions()

    existing = next((c for c in conversions if c["id"] == conversion_id), None)

    if existing:
        existing["status"] = status
        existing["file_size"] = file_size
        existing["updated_at"] = datetime.now().isoformat()
        if feature:
            existing["feature"] = feature
        if input_type:
            existing["input_type"] = input_type
        if output_type:
            existing["output_type"] = output_type
        if processing_time_ms is not None:
            existing["processing_time_ms"] = processing_time_ms
        if error_message:
            existing["error_message"] = error_message
        if output_file_size is not None:
            existing["output_file_size"] = output_file_size
    else:
        conversions.append({
            "id": conversion_id,
            "phone_number": phone_number,
            "status": status,
            "file_size": file_size,
            "feature": feature,
            "input_type": input_type,
            "output_type": output_type,
            "processing_time_ms": processing_time_ms,
            "error_message": error_message,
            "output_file_size": output_file_size,
            "timestamp": datetime.now().isoformat(),
        })

    conversions = conversions[-1000:]
    _save_conversions(conversions)


# ── Stats ──────────────────────────────────────────────────────────

def get_stats() -> Dict[str, Any]:
    """Get conversion statistics with extended metrics."""
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
    failed = sum(1 for c in conversions if c["status"] == "failed")

    success_rate = round((success / total * 100) if total > 0 else 0, 1)

    # Unique users
    phones = set(c["phone_number"] for c in conversions)
    active_users = len(phones)

    # Average processing time
    times = [c.get("processing_time_ms") for c in conversions if c.get("processing_time_ms")]
    avg_time = round(sum(times) / len(times)) if times else 0

    # Top feature
    features = [c.get("feature", "convert") for c in conversions if c["status"] == "success"]
    feature_counts = Counter(features)
    top_feature = feature_counts.most_common(1)[0][0] if feature_counts else "—"

    # Total bandwidth
    total_bytes = sum(c.get("file_size", 0) for c in conversions)
    total_bandwidth_mb = round(total_bytes / (1024 * 1024), 2)

    return {
        "total_conversions": total,
        "today_conversions": today,
        "success_rate": success_rate,
        "pending": pending,
        "active_users": active_users,
        "avg_processing_time_ms": avg_time,
        "top_feature": top_feature,
        "total_bandwidth_mb": total_bandwidth_mb,
    }


def get_conversions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent conversions."""
    conversions = _load_conversions()
    return sorted(
        conversions,
        key=lambda x: x["timestamp"],
        reverse=True
    )[:limit]


# ── Analytics ──────────────────────────────────────────────────────

def get_timeseries(days: int = 30) -> List[Dict[str, Any]]:
    """Get conversion counts by date for the last N days."""
    conversions = _load_conversions()
    cutoff = datetime.now() - timedelta(days=days)

    # Initialize all days
    result = {}
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result[date] = {"date": date, "conversions": 0, "successes": 0, "failures": 0}

    for c in conversions:
        try:
            ts = datetime.fromisoformat(c["timestamp"])
            if ts >= cutoff:
                date = ts.strftime("%Y-%m-%d")
                if date in result:
                    result[date]["conversions"] += 1
                    if c["status"] == "success":
                        result[date]["successes"] += 1
                    elif c["status"] == "failed":
                        result[date]["failures"] += 1
        except (ValueError, KeyError):
            continue

    return list(result.values())


def get_feature_usage() -> List[Dict[str, Any]]:
    """Get breakdown of feature usage."""
    conversions = _load_conversions()
    features = [c.get("feature", "convert") for c in conversions]
    counts = Counter(features)
    total = sum(counts.values())

    return sorted(
        [
            {
                "feature": feat,
                "count": cnt,
                "percentage": round(cnt / total * 100, 1) if total > 0 else 0,
            }
            for feat, cnt in counts.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )


def get_user_analytics() -> Dict[str, Any]:
    """Get user-level analytics."""
    conversions = _load_conversions()
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)

    phone_data: Dict[str, Dict] = {}
    for c in conversions:
        phone = c["phone_number"]
        if phone not in phone_data:
            phone_data[phone] = {"count": 0, "last_active": c["timestamp"]}
        phone_data[phone]["count"] += 1
        if c["timestamp"] > phone_data[phone]["last_active"]:
            phone_data[phone]["last_active"] = c["timestamp"]

    total_unique = len(phone_data)
    repeat_users = sum(1 for d in phone_data.values() if d["count"] > 1)

    # New users today
    new_today = sum(
        1 for phone, d in phone_data.items()
        if d["count"] == 1
        and datetime.fromisoformat(d["last_active"]) >= today_start
    )

    # Top users (masked phone)
    top_users = sorted(phone_data.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    top_users_list = [
        {
            "phone": _mask_phone(phone),
            "count": data["count"],
            "last_active": data["last_active"],
        }
        for phone, data in top_users
    ]

    # Country distribution from phone prefixes
    country_dist = _get_country_distribution(list(phone_data.keys()))

    return {
        "total_unique_users": total_unique,
        "repeat_users": repeat_users,
        "new_users_today": new_today,
        "top_users": top_users_list,
        "country_distribution": country_dist,
    }


def get_error_tracking() -> Dict[str, Any]:
    """Get error analytics."""
    conversions = _load_conversions()
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)

    failed = [c for c in conversions if c["status"] == "failed"]
    total = len(conversions)

    errors_today = sum(
        1 for c in failed
        if datetime.fromisoformat(c["timestamp"]) >= today_start
    )

    # Error types
    error_msgs = [c.get("error_message", "Unknown error") for c in failed]
    error_counts = Counter(error_msgs)
    error_types = [
        {
            "type": msg,
            "count": cnt,
            "last_occurred": max(
                c["timestamp"] for c in failed
                if c.get("error_message", "Unknown error") == msg
            ),
        }
        for msg, cnt in error_counts.most_common(10)
    ]

    # Recent errors
    recent_errors = sorted(failed, key=lambda x: x["timestamp"], reverse=True)[:20]
    recent_list = [
        {
            "id": e["id"],
            "timestamp": e["timestamp"],
            "feature": e.get("feature", "unknown"),
            "message": e.get("error_message", "Unknown"),
        }
        for e in recent_errors
    ]

    return {
        "total_errors": len(failed),
        "error_rate": round(len(failed) / total * 100, 1) if total > 0 else 0,
        "errors_today": errors_today,
        "error_types": error_types,
        "recent_errors": recent_list,
    }


def export_conversions_csv() -> str:
    """Export all conversions as CSV string."""
    conversions = _load_conversions()
    headers = [
        "id", "timestamp", "phone_number", "status", "feature",
        "file_size", "output_file_size", "processing_time_ms",
        "input_type", "output_type", "error_message",
    ]

    lines = [",".join(headers)]
    for c in sorted(conversions, key=lambda x: x["timestamp"], reverse=True):
        row = []
        for h in headers:
            val = c.get(h, "")
            val = str(val) if val is not None else ""
            # Escape commas and quotes in CSV
            if "," in val or '"' in val:
                val = '"' + val.replace('"', '""') + '"'
            row.append(val)
        lines.append(",".join(row))

    return "\n".join(lines)


# ── Internal helpers ───────────────────────────────────────────────

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


def _mask_phone(phone: str) -> str:
    """Mask phone number for privacy."""
    if len(phone) > 6:
        return phone[:4] + "****" + phone[-4:]
    return phone


# Country code prefix mapping (common ones)
COUNTRY_PREFIXES = {
    "1": ("United States", "US"),
    "91": ("India", "IN"),
    "44": ("United Kingdom", "GB"),
    "61": ("Australia", "AU"),
    "81": ("Japan", "JP"),
    "49": ("Germany", "DE"),
    "33": ("France", "FR"),
    "86": ("China", "CN"),
    "7": ("Russia", "RU"),
    "55": ("Brazil", "BR"),
    "234": ("Nigeria", "NG"),
    "27": ("South Africa", "ZA"),
    "971": ("UAE", "AE"),
    "966": ("Saudi Arabia", "SA"),
    "92": ("Pakistan", "PK"),
    "880": ("Bangladesh", "BD"),
    "62": ("Indonesia", "ID"),
    "60": ("Malaysia", "MY"),
    "63": ("Philippines", "PH"),
    "84": ("Vietnam", "VN"),
    "254": ("Kenya", "KE"),
    "20": ("Egypt", "EG"),
    "52": ("Mexico", "MX"),
    "39": ("Italy", "IT"),
    "34": ("Spain", "ES"),
    "31": ("Netherlands", "NL"),
    "82": ("South Korea", "KR"),
    "90": ("Turkey", "TR"),
    "48": ("Poland", "PL"),
    "46": ("Sweden", "SE"),
}


def _get_country_distribution(phones: List[str]) -> List[Dict[str, Any]]:
    """Get country distribution from phone number prefixes."""
    countries: Dict[str, int] = {}

    for phone in phones:
        matched = False
        # Try 3-digit, 2-digit, then 1-digit prefix
        for length in (3, 2, 1):
            prefix = phone[:length]
            if prefix in COUNTRY_PREFIXES:
                name, code = COUNTRY_PREFIXES[prefix]
                countries[name] = countries.get(name, 0) + 1
                matched = True
                break

        if not matched:
            countries["Other"] = countries.get("Other", 0) + 1

    return sorted(
        [
            {"country": name, "code": _get_code(name), "count": count}
            for name, count in countries.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )


def _get_code(country_name: str) -> str:
    """Get country code from name."""
    for _, (name, code) in COUNTRY_PREFIXES.items():
        if name == country_name:
            return code
    return "XX"
