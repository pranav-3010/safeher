import csv
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.agents.base_agent import DataSourceAgent
from app.models.incidents import CrimeIncident
from app.services.data_processing import validate_coordinates, clean_text_string, normalize_utc_timestamp
from app.core.logging import logger


class GovernmentDataAgent(DataSourceAgent):
    """
    Ingestion Agent for Open Government Data (CSV, JSON, GeoJSON, API).
    Preserves geographic granularity (e.g. state/district level) without inventing fake point coordinates.
    """

    def __init__(self, source_name: str = "NCRB Open Crime Data Portal"):
        super().__init__(source_name=source_name, source_type="government")

    def fetch(self, raw_content: str = None, file_format: str = "json") -> List[Dict[str, Any]]:
        """
        Parses government dataset content (JSON or CSV format).
        """
        if not raw_content:
            return []

        records = []
        if file_format.lower() == "csv":
            reader = csv.DictReader(raw_content.splitlines())
            for row in reader:
                records.append(dict(row))
        elif file_format.lower() == "json":
            parsed = json.loads(raw_content)
            records = parsed if isinstance(parsed, list) else parsed.get("records", [])
        return records

    def validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Validates government records against schema constraints.
        Rejects malformed records without required incident_type.
        """
        valid_records = []
        rejected_count = 0

        for r in raw_records:
            incident_type = clean_text_string(r.get("incident_type") or r.get("offense_type") or r.get("category"))
            if not incident_type:
                rejected_count += 1
                continue

            lat = r.get("latitude")
            lng = r.get("longitude")
            has_valid_coords = validate_coordinates(lat, lng)

            valid_records.append({
                "external_source_id": clean_text_string(r.get("external_id") or r.get("id")),
                "incident_type": incident_type,
                "description": clean_text_string(r.get("description")),
                "occurred_at": r.get("occurred_at") or r.get("year"),
                "latitude": float(lat) if has_valid_coords else None,
                "longitude": float(lng) if has_valid_coords else None,
                "severity": float(r.get("severity", 0.5)) if r.get("severity") else 0.5,
                "source_reference": clean_text_string(r.get("source_ref")),
                "raw_data": r
            })

        return valid_records, rejected_count

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes timestamp and category fields.
        """
        normalized = []
        for r in validated_records:
            occ_at = r["occurred_at"]
            parsed_dt = None
            if isinstance(occ_at, str):
                try:
                    parsed_dt = datetime.fromisoformat(occ_at)
                except ValueError:
                    parsed_dt = datetime.now(timezone.utc)
            elif isinstance(occ_at, int):
                # Yearly statistic (e.g. 2024)
                parsed_dt = datetime(occ_at, 1, 1, tzinfo=timezone.utc)

            r["occurred_at"] = normalize_utc_timestamp(parsed_dt)
            normalized.append(r)
        return normalized

    def deduplicate(self, db: Session, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates records based on external_source_id and incident_type.
        """
        deduped = []
        for r in normalized_records:
            ext_id = r["external_source_id"]
            if ext_id:
                exists = db.query(CrimeIncident).filter(CrimeIncident.external_source_id == ext_id).first()
                if exists:
                    continue
            deduped.append(r)
        return deduped

    def store(self, db: Session, data_source_id: Any, records: List[Dict[str, Any]]) -> int:
        """
        Bulk inserts validated government crime incidents into crime_incidents table.
        Uses ST_SetSRID(ST_MakePoint(lng, lat), 4326) for valid coordinates.
        """
        if not records:
            return 0

        inserted_count = 0
        for r in records:
            incident = CrimeIncident(
                data_source_id=data_source_id,
                external_source_id=r["external_source_id"],
                incident_type=r["incident_type"],
                description=r["description"],
                occurred_at=r["occurred_at"],
                latitude=r["latitude"],
                longitude=r["longitude"],
                severity=r["severity"],
                source_reference=r["source_reference"],
                verification_status="VERIFIED" if r["external_source_id"] else "UNVERIFIED",
                raw_data=r["raw_data"]
            )
            db.add(incident)
            db.flush()

            # Execute PostGIS Point assignment if valid coordinates exist
            if r["latitude"] is not None and r["longitude"] is not None:
                db.execute(text(
                    "UPDATE crime_incidents SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
                ), {"lng": r["longitude"], "lat": r["latitude"], "id": incident.id})

            inserted_count += 1

        db.commit()
        return inserted_count
