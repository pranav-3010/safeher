from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.data_source import DataSource, SourceFetch
from app.core.logging import logger


class DataSourceAgent(ABC):
    """
    Abstract Base Class for Real-World Data Ingestion Agents.
    Enforces standardized lifecycle: fetch() -> validate() -> normalize() -> deduplicate() -> store().
    """

    def __init__(self, source_name: str, source_type: str):
        self.source_name = source_name
        self.source_type = source_type

    def get_or_create_source_record(self, db: Session) -> DataSource:
        """
        Retrieves or registers the data source record in data_sources table.
        """
        ds = db.query(DataSource).filter(DataSource.name == self.source_name).first()
        if not ds:
            ds = DataSource(
                name=self.source_name,
                source_type=self.source_type,
                is_active=True,
                is_verified=True
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)
        return ds

    def create_fetch_log(self, db: Session, data_source_id: Any) -> SourceFetch:
        """
        Creates a new fetch execution log record in source_fetches table.
        """
        fetch_log = SourceFetch(
            data_source_id=data_source_id,
            started_at=datetime.now(timezone.utc),
            status="IN_PROGRESS"
        )
        db.add(fetch_log)
        db.commit()
        db.refresh(fetch_log)
        return fetch_log

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch raw data from external source."""
        pass

    @abstractmethod
    def validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Validate raw records against schema and coordinate/timestamp rules."""
        pass

    @abstractmethod
    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize attributes, categories, UTC dates, and PostGIS geometries."""
        pass

    @abstractmethod
    def deduplicate(self, db: Session, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate records using content hashes, external IDs, or OSM IDs."""
        pass

    @abstractmethod
    def store(self, db: Session, data_source_id: Any, records: List[Dict[str, Any]]) -> int:
        """Persist normalized records to target database tables in batch."""
        pass

    def run_pipeline(self, db: Session, **kwargs) -> Dict[str, Any]:
        """
        Executes the full standardized ingestion pipeline lifecycle:
        FETCH -> VALIDATE -> NORMALIZE -> DEDUPLICATE -> STORE -> LOG.
        """
        source_rec = self.get_or_create_source_record(db)
        fetch_log = self.create_fetch_log(db, source_rec.id)
        
        try:
            logger.info(f"Starting ingestion pipeline for agent: [{self.source_name}]")
            raw_data = self.fetch(**kwargs)
            fetch_log.records_fetched = len(raw_data)
            
            valid_data, rejected_count = self.validate(raw_data)
            fetch_log.records_rejected = rejected_count
            
            normalized_data = self.normalize(valid_data)
            deduped_data = self.deduplicate(db, normalized_data)
            
            inserted_count = self.store(db, source_rec.id, deduped_data)
            fetch_log.records_inserted = inserted_count
            fetch_log.completed_at = datetime.now(timezone.utc)
            fetch_log.status = "COMPLETED"
            db.commit()
            
            logger.info(f"Successfully completed ingestion for [{self.source_name}]: {inserted_count} inserted, {rejected_count} rejected.")
            return {
                "status": "COMPLETED",
                "source": self.source_name,
                "records_fetched": len(raw_data),
                "records_inserted": inserted_count,
                "records_rejected": rejected_count
            }
        except Exception as e:
            logger.error(f"Ingestion pipeline failed for [{self.source_name}]: {str(e)}", exc_info=True)
            fetch_log.completed_at = datetime.now(timezone.utc)
            fetch_log.status = "FAILED"
            fetch_log.error_message = str(e)
            db.commit()
            return {
                "status": "FAILED",
                "source": self.source_name,
                "error": str(e)
            }
