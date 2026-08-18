from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.monitoring_service import MonitoringService

router = APIRouter()


class RouteFeedbackCreateRequest(BaseModel):
    route_id: str = Field(..., description="Route option ID")
    route_type: str = Field("SAFEST", description="Route type (SAFEST, BALANCED, FASTEST)")
    is_useful: bool = Field(..., description="Was this route useful?")
    comments: Optional[str] = Field(None, description="Optional user improvement comments")
    user_reference: Optional[str] = Field("anonymous_user", description="User ID or session reference")


@router.get("/health-dashboard")
def get_monitoring_health_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns live health status matrix across all 9 core subsystems.
    """
    return MonitoringService.get_health_matrix(db)


@router.get("/metrics")
def get_performance_latency_metrics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns Average, Median, and 95th Percentile (P95) latency performance metrics for API, DB, ML, LLM, and Routing.
    """
    return MonitoringService.get_performance_latency_stats(db)


@router.get("/model-drift")
def get_model_drift_analysis(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns historical ML model version, baseline feature distribution, and drift metric analysis.
    """
    return MonitoringService.check_model_drift(db)


@router.get("/alerts")
def get_system_alerts_feed(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns active and historical system warning/critical alerts.
    """
    alerts = MonitoringService.get_system_alerts(db)
    return {
        "success": True,
        "count": len(alerts),
        "alerts": alerts
    }


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_route_feedback(
    payload: RouteFeedbackCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submits user route usefulness feedback ("Was this route useful? [ YES ] [ NO ]").
    """
    return MonitoringService.record_route_feedback(
        db=db,
        route_id=payload.route_id,
        route_type=payload.route_type,
        is_useful=payload.is_useful,
        comments=payload.comments,
        user_reference=payload.user_reference or "anonymous_user"
    )


@router.get("/feedback")
def get_route_feedback_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns summary statistics of user route feedback.
    """
    return MonitoringService.get_route_feedback_summary(db)


@router.get("/backup-verify")
def get_backup_verification_status() -> Dict[str, Any]:
    """
    Verifies PostgreSQL/PostGIS database backup script and backup files availability.
    """
    return MonitoringService.verify_backup_status()
