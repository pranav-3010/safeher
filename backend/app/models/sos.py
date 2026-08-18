import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from app.models.base_model import UUIDBaseModel


class SOSEvent(UUIDBaseModel):
    """
    Emergency SOS event records with PostGIS Point geography and state machine tracking.
    Statuses: CREATED -> ACTIVE -> ACKNOWLEDGED -> RESOLVED | CANCELLED | FAILED
    Notification Statuses: NOT_CONFIGURED, PENDING, SENT, DELIVERED, FAILED
    """
    __tablename__ = "sos_events"

    user_reference: Mapped[str] = mapped_column(String(255), default="anonymous_user", nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False, index=True)
    notification_status: Mapped[str] = mapped_column(String(50), default="NOT_CONFIGURED", nullable=False, index=True)
    notification_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="none")
    
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    location_updates = relationship("SOSLocationUpdate", back_populates="sos_event", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="check_sos_valid_latitude"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="check_sos_valid_longitude"),
    )


class SOSLocationUpdate(UUIDBaseModel):
    """
    Periodic position updates captured during an ACTIVE SOS session.
    """
    __tablename__ = "sos_location_updates"

    sos_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    sos_event = relationship("SOSEvent", back_populates="location_updates")

    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_sos_update_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_sos_update_longitude"),
    )



class EmergencyContact(UUIDBaseModel):
    """
    User configured trusted emergency contacts.
    """
    __tablename__ = "emergency_contacts"

    user_reference: Mapped[str] = mapped_column(String(255), default="anonymous_user", nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="Trusted Contact")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
