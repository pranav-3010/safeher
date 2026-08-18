import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography
from app.models.base_model import UUIDBaseModel


class RouteAnalysis(UUIDBaseModel):
    """
    Audit log of route evaluation requests, safety costs, risk statistics, and provider response.
    """
    __tablename__ = "route_analyses"

    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    source_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    destination_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    departure_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    route_provider: Mapped[str] = mapped_column(String(50), nullable=False) # osrm, mapbox, etc.
    route_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    selected_route: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    safety_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maximum_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high_risk_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_route_analyses_source_location", "source_location", postgresql_using="gist"),
        Index("idx_route_analyses_dest_location", "destination_location", postgresql_using="gist"),
    )


class EmergencyEvent(UUIDBaseModel):
    """
    Emergency SOS alerts (manual_sos, voice_sos) prepared for Supabase RLS security.
    """
    __tablename__ = "emergency_events"

    event_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # manual_sos, voice_sos, shake_sos
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True) # ACTIVE, RESOLVED, CANCELLED, TEST
    notification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    notification_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_emergency_events_location", "location", postgresql_using="gist"),
    )


class SystemLog(UUIDBaseModel):
    """
    Centralized system audit logs without sensitive credentials.
    """
    __tablename__ = "system_logs"

    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
