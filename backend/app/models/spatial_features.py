import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from app.models.base_model import UUIDBaseModel


class OSMFeature(UUIDBaseModel):
    """
    OpenStreetMap points of interest, amenities, and geographical facilities.
    """
    __tablename__ = "osm_features"

    osm_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    feature_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # point, way, relation
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)      # shop, police, hospital, atm, etc.
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    geometry = mapped_column(Geography(geometry_type="GEOMETRY", srid=4326), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_osm_features_geometry", "geometry", postgresql_using="gist"),
        Index("idx_osm_features_location", "location", postgresql_using="gist"),
    )


class RoadSegment(UUIDBaseModel):
    """
    Critical road segment polylines with PostGIS LineString Geography and physical attributes.
    """
    __tablename__ = "road_segments"

    osm_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    road_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    road_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # primary, secondary, residential, alley
    geometry = mapped_column(Geography(geometry_type="LINESTRING", srid=4326), nullable=False)
    length_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_speed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    oneway: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_sidewalk: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_dead_end: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    intersection_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lighting_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)          # NULL allowed (UNKNOWN)
    commercial_activity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # NULL allowed (UNKNOWN)

    # Relationships
    environmental_features: Mapped[list["EnvironmentalFeature"]] = relationship("EnvironmentalFeature", back_populates="road_segment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_road_segments_geometry", "geometry", postgresql_using="gist"),
    )


class EmergencyFacility(UUIDBaseModel):
    """
    Emergency safe havens (Police, Hospitals, Metro, Petrol Pumps, Fire Stations).
    """
    __tablename__ = "emergency_facilities"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    facility_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # police, hospital, metro, petrol_station, fire_station
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_24_hours: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED", nullable=False, index=True)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_emergency_facilities_location", "location", postgresql_using="gist"),
    )


class EnvironmentalFeature(UUIDBaseModel):
    """
    Environmental and physical safety attributes bound to specific road segments.
    """
    __tablename__ = "environmental_features"

    road_segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("road_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    lighting_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)        # NULL = UNKNOWN
    lighting_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    commercial_activity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)     # NULL = UNKNOWN
    foot_traffic_indicator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # NULL = UNKNOWN
    visibility_indicator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # NULL = UNKNOWN
    road_width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    footpath_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    surveillance_indicator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    road_segment: Mapped["RoadSegment"] = relationship("RoadSegment", back_populates="environmental_features")
