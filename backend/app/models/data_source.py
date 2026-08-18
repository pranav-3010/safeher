import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_model import UUIDBaseModel


class DataSource(UUIDBaseModel):
    """
    Registry for external and internal data providers (e.g. government, police, OSM, news).
    """
    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # government, police, osm, news, etc.
    official_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geographic_coverage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    terms_of_use: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    access_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    update_frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    historical_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    historical_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    geographic_precision: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    fetches: Mapped[List["SourceFetch"]] = relationship("SourceFetch", back_populates="data_source", cascade="all, delete-orphan")


class SourceFetch(UUIDBaseModel):
    """
    Logs data ingestion execution runs for auditing and monitoring.
    """
    __tablename__ = "source_fetches"

    data_source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    records_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="fetches")
