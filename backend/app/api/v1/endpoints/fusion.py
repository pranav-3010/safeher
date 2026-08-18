from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.database.session import get_db
from app.services.fusion_engine import FusionEngine

router = APIRouter()

class FusionRiskRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Target latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Target longitude")
    timestamp: Optional[str] = Field(default=None, description="Target ISO timestamp")
    radius_meters: Optional[float] = Field(default=2000.0, ge=100.0, le=10000.0, description="Analysis radius in meters")

@router.post("/fusion", summary="Evaluate Phase 8 AI + ML + LLM Fusion Risk")
def evaluate_fusion_risk(
    payload: FusionRiskRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluates Phase 8 Fusion Risk by combining Phase 4 Geographic Intelligence,
    Phase 6 Historical ML, Phase 7 Dynamic Risk, and Phase 5 Grounded LLM Explanation.
    """
    req_dt = None
    if payload.timestamp:
        try:
            req_dt = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except Exception:
            req_dt = datetime.now(timezone.utc)

    result = FusionEngine.evaluate_fusion_risk(
        db=db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        request_timestamp=req_dt,
        radius_meters=payload.radius_meters or 2000.0
    )

    return result
