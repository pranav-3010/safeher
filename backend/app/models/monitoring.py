import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_model import UUIDBaseModel


class SystemMetric(UUIDBaseModel):
    """
    Latency and performance metrics for API, Database, ML, LLM, and Routing operations.
    """
    __tablename__ = "system_metrics"

    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class SystemAlert(UUIDBaseModel):
    """
    System warning and critical alert logs (e.g. database down, data source stale, SOS failure).
    """
    __tablename__ = "system_alerts"

    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    alert_level: Mapped[str] = mapped_column(String(20), default="WARNING", nullable=False, index=True) # CRITICAL, WARNING, INFO
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class RouteFeedback(UUIDBaseModel):
    """
    User route feedback submissions for continuous safety model evaluation.
    """
    __tablename__ = "route_feedback"

    route_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    route_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # SAFEST, BALANCED, FASTEST
    is_useful: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_reference: Mapped[str] = mapped_column(String(255), default="anonymous_user", nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class ModelDriftMetric(UUIDBaseModel):
    """
    Historical ML model version, baseline feature distribution, and drift metric logs.
    """
    __tablename__ = "model_drift_metrics"

    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False, index=True)
    prediction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    feature_drift_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
