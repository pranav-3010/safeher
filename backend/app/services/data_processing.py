import hashlib
import re
from datetime import datetime, timezone
from typing import Optional, Tuple


def validate_coordinates(lat: Optional[float], lng: Optional[float]) -> bool:
    """
    Validates latitude (-90 to 90) and longitude (-180 to 180).
    Returns False if coordinates are invalid or None.
    """
    if lat is None or lng is None:
        return False
    try:
        lat_f, lng_f = float(lat), float(lng)
        if -90.0 <= lat_f <= 90.0 and -180.0 <= lng_f <= 180.0:
            return True
        return False
    except (ValueError, TypeError):
        return False


def generate_content_hash(publisher: str, title: str, url: Optional[str] = None) -> str:
    """
    Generates a deterministic SHA-256 hash for news article deduplication.
    Combines publisher + title + url to uniquely identify articles.
    """
    raw_str = f"{publisher.strip().lower()}|{title.strip().lower()}|{(url or '').strip().lower()}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()


def normalize_utc_timestamp(dt: Optional[datetime]) -> datetime:
    """
    Normalizes any datetime instance into a timezone-aware UTC datetime.
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clean_text_string(text: Optional[str]) -> Optional[str]:
    """
    Normalizes whitespace and cleans invalid control characters from string content.
    """
    if not text:
        return None
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if cleaned else None
