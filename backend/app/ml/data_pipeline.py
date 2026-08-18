from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models.incidents import CrimeIncident, CrimeStatistic
from app.services.data_processing import validate_coordinates
from app.core.logging import logger

class HistoricalDataPipeline:
    """
    Data Quality & Ingestion Pipeline for Phase 6 Historical ML Model.
    Queries verified records from PostgreSQL/PostGIS database and validates spatial/temporal fields.
    """

    @staticmethod
    def load_and_validate_dataset(db: Session) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Loads raw historical records from database and returns valid observations with data quality metrics.
        """
        incidents = db.query(CrimeIncident).all()
        total_records = len(incidents)

        valid_records: List[Dict[str, Any]] = []
        invalid_records_count = 0
        missing_coords_count = 0
        missing_timestamps_count = 0
        duplicate_count = 0

        seen_hashes = set()

        for inc in incidents:
            if inc.latitude is None or inc.longitude is None:
                missing_coords_count += 1
                invalid_records_count += 1
                continue

            if not validate_coordinates(inc.latitude, inc.longitude):
                invalid_records_count += 1
                continue

            if inc.occurred_at is None:
                missing_timestamps_count += 1
                invalid_records_count += 1
                continue

            # Deduplication key based on lat, lng, timestamp
            dedup_key = f"{round(inc.latitude, 4)}_{round(inc.longitude, 4)}_{inc.occurred_at.isoformat()}"
            if dedup_key in seen_hashes:
                duplicate_count += 1
                continue

            seen_hashes.add(dedup_key)

            valid_records.append({
                "id": str(inc.id),
                "incident_type": inc.incident_type,
                "occurred_at": inc.occurred_at,
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "severity": float(inc.severity) if inc.severity is not None else 0.5,
                "source_reference": inc.source_reference or "Verified Record"
            })

        quality_report = {
            "total_records": total_records,
            "valid_records": len(valid_records),
            "invalid_records": invalid_records_count,
            "missing_coordinates": missing_coords_count,
            "missing_timestamps": missing_timestamps_count,
            "duplicate_records": duplicate_count,
        }

        logger.info(f"Historical Data Pipeline Quality Report: {quality_report}")
        return valid_records, quality_report
