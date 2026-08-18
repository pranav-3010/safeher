import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base_model import Base


class MLModelMetadata(Base):
    __tablename__ = "ml_model_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False, index=True)
    algorithm = Column(String(100), nullable=False)
    training_start = Column(DateTime(timezone=True), nullable=True)
    training_end = Column(DateTime(timezone=True), nullable=True)
    dataset_size = Column(Integer, nullable=False, default=0)
    target_definition = Column(String(255), nullable=True)
    metrics = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="INSUFFICIENT_DATA")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "model_version": self.model_version,
            "algorithm": self.algorithm,
            "training_start": self.training_start.isoformat() if self.training_start else None,
            "training_end": self.training_end.isoformat() if self.training_end else None,
            "dataset_size": self.dataset_size,
            "target_definition": self.target_definition,
            "metrics": self.metrics,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
