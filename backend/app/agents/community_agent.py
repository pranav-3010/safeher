from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.agents.base_agent import DataSourceAgent
from app.models.incidents import CommunityReport
from app.services.data_processing import validate_coordinates, clean_text_string, normalize_utc_timestamp
from app.core.logging import logger


class CommunityDataAgent(DataSourceAgent):
    """
    Ingestion & Validation Service for Crowdsourced User Community Safety Reports.
    Sets verification_status="UNVERIFIED" and review_status="PENDING" without treating reports as confirmed crimes.
    """

    def __init__(self, source_name: str = "SafeHer Mobile Community Reports"):
        super().__init__(source_name=source_name, source_type="community")

    def fetch(self, user_report_payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Receives submitted user report payload.
        """
        if not user_report_payload:
            return []
        return [user_report_payload]

    def validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Validates user report payload: coordinates (-90..90, -180..180), report_type, and description.
        """
        valid = []
        rejected = 0

        for r in raw_records:
            report_type = clean_text_string(r.get("report_type"))
            description = clean_text_string(r.get("description"))
            lat = r.get("latitude")
            lng = r.get("longitude")

            if not report_type or not validate_coordinates(lat, lng):
                rejected += 1
                continue

            if description and len(description) > 2000:
                rejected += 1
                continue

            valid.append({
                "user_reference": clean_text_string(r.get("user_reference")),
                "report_type": report_type,
                "description": description,
                "latitude": float(lat),
                "longitude": float(lng),
                "occurred_at": r.get("occurred_at")
            })

        return valid, rejected

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes timestamps to UTC.
        """
        normalized = []
        for r in validated_records:
            occ_at = r.get("occurred_at")
            parsed_dt = None
            if isinstance(occ_at, str):
                try:
                    parsed_dt = datetime.fromisoformat(occ_at)
                except ValueError:
                    parsed_dt = datetime.now(timezone.utc)

            r["reported_at"] = datetime.now(timezone.utc)
            r["occurred_at"] = normalize_utc_timestamp(parsed_dt)
            normalized.append(r)
        return normalized

    def deduplicate(self, db: Session, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Allows user reports (community reports are event-based submissions).
        """
        return normalized_records

    def store(self, db: Session, data_source_id: Any, records: List[Dict[str, Any]]) -> int:
        """
        Stores user report into community_reports table with PostGIS Geography Point.
        """
        if not records:
            return 0

        inserted_count = 0
        for r in records:
            report = CommunityReport(
                user_reference=r["user_reference"],
                report_type=r["report_type"],
                description=r["description"],
                reported_at=r["reported_at"],
                occurred_at=r["occurred_at"],
                verification_status="UNVERIFIED",
                review_status="PENDING"
            )
            db.add(report)
            db.flush()

            # Set PostGIS Geography Point
            db.execute(text(
                "UPDATE community_reports SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
            ), {"lng": r["longitude"], "lat": r["latitude"], "id": report.id})

            inserted_count += 1

        db.commit()
        return inserted_count
