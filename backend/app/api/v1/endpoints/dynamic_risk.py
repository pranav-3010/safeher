from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.database.session import get_db
from app.services.dynamic_risk_engine import DynamicRiskEngine

router = APIRouter()

class DynamicRiskRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Target latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Target longitude")
    timestamp: Optional[str] = Field(default=None, description="Target ISO timestamp")
    radius_meters: Optional[float] = Field(default=2000.0, ge=100.0, le=10000.0, description="Search radius in meters")
    window_hours: Optional[float] = Field(default=24.0, ge=1.0, le=168.0, description="Recency window in hours")

@router.post("/dynamic", summary="Evaluate Current Dynamic Risk")
def evaluate_dynamic_risk(
    payload: DynamicRiskRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluates current dynamic risk score for target location.
    Queries PostGIS spatial incidents, applies time & distance decay, and calculates data freshness.
    """
    req_dt = None
    if payload.timestamp:
        try:
            req_dt = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except Exception:
            req_dt = datetime.now(timezone.utc)

    result = DynamicRiskEngine.evaluate_dynamic_risk(
        db=db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        request_timestamp=req_dt,
        radius_meters=payload.radius_meters or 2000.0,
        window_hours=payload.window_hours or 24.0
    )

    return result
