from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.database.session import get_db
from app.services.safe_route_engine import SafeRouteEngine

router = APIRouter()

class LocationPoint(BaseModel):
    name: str = Field(default="Location", description="Display name of location")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")

class RouteAnalyzeRequest(BaseModel):
    source: LocationPoint
    destination: LocationPoint

@router.post("/analyze", summary="Analyze Phase 9 Safe Routes")
def analyze_routes(
    payload: RouteAnalyzeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluates real road network routes via OSRM, calculates segment Phase 8 safety scores,
    and returns Safest, Balanced, and Fastest route alternatives.
    """
    try:
        result = SafeRouteEngine.analyze_safe_routes(
            db=db,
            source=payload.source.model_dump(),
            destination=payload.destination.model_dump()
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to calculate safe routes: {str(e)}"
        )
