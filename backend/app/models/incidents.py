import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from app.models.base_model import UUIDBaseModel


class CrimeIncident(UUIDBaseModel):
    """
    Official and verified crime incident records with PostGIS Point Geography.
    """
    __tablename__ = "crime_incidents"

    external_source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    severity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", nullable=False, index=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="check_valid_latitude"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="check_valid_longitude"),
        CheckConstraint("severity IS NULL OR (severity >= 0.0 AND severity <= 1.0)", name="check_valid_severity"),
        CheckConstraint("source_confidence IS NULL OR (source_confidence >= 0.0 AND source_confidence <= 1.0)", name="check_valid_confidence"),
        Index("idx_crime_incidents_location", "location", postgresql_using="gist"),
    )


class NewsArticle(UUIDBaseModel):
    """
    Ingested news articles and media posts referencing safety and incidents.
    """
    __tablename__ = "news_articles"

    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    external_article_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    llm_processed: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    extracted_incidents: Mapped[list["NewsIncident"]] = relationship("NewsIncident", back_populates="article", cascade="all, delete-orphan")


class NewsIncident(UUIDBaseModel):
    """
    Structured incident events extracted from news articles using LLM NLP analysis.
    """
    __tablename__ = "news_incidents"

    news_article_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    severity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", nullable=False, index=True)
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    article: Mapped["NewsArticle"] = relationship("NewsArticle", back_populates="extracted_incidents")

    __table_args__ = (
        CheckConstraint("valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from", name="check_valid_news_incident_dates"),
        Index("idx_news_incidents_location", "location", postgresql_using="gist"),
    )


class CommunityReport(UUIDBaseModel):
    """
    Crowdsourced safety reports submitted by users (prepared for Supabase RLS).
    """
    __tablename__ = "community_reports"

    user_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", nullable=False, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    __table_args__ = (
        Index("idx_community_reports_location", "location", postgresql_using="gist"),
    )
