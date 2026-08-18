from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.sos_service import SOSService

router = APIRouter()


class SOSCreateRequest(BaseModel):
    latitude: Optional[float] = Field(None, description="Current latitude position")
    longitude: Optional[float] = Field(None, description="Current longitude position")
    accuracy: Optional[float] = Field(None, description="Location accuracy in meters")
    user_reference: Optional[str] = Field("anonymous_user", description="User ID or session reference")


class SOSCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional cancellation reason")
    user_reference: Optional[str] = Field("anonymous_user", description="User ID or session reference")


class SOSLocationUpdateRequest(BaseModel):
    latitude: float = Field(..., description="Updated latitude position")
    longitude: float = Field(..., description="Updated longitude position")
    accuracy: Optional[float] = Field(None, description="Location accuracy in meters")


class EmergencyContactCreateRequest(BaseModel):
    name: str = Field(..., description="Contact name")
    phone_number: str = Field(..., description="Contact phone number")
    relationship: Optional[str] = Field("Trusted Contact", description="Relationship")
    is_primary: Optional[bool] = Field(False, description="Primary contact flag")
    user_reference: Optional[str] = Field("anonymous_user", description="User reference")


@router.post("", status_code=status.HTTP_201_CREATED)
def trigger_sos_event(
    payload: SOSCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Triggers an Emergency SOS Alert event.
    Stores PostGIS location, handles duplicate active SOS requests,
    and reports notification provider status without fake claims.
    """
    res = SOSService.create_sos(
        db=db,
        user_reference=payload.user_reference or "anonymous_user",
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy
    )
    if not res.get("success") and not res.get("already_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res


@router.get("/admin/sos/active")
def list_active_sos_alerts(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Protected emergency operator endpoint returning all currently active SOS alerts.
    """
    events = SOSService.get_active_sos_events(db)
    return {
        "success": True,
        "count": len(events),
        "active_events": events
    }


@router.get("/{sos_id}")
def get_sos_event_status(
    sos_id: str,
    user_reference: str = Query("anonymous_user"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieves status, location details, notification status, and tracking history for an SOS event.
    """
    res = SOSService.get_sos_status(db=db, sos_id=sos_id, user_reference=user_reference)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS event not found")
    return res


@router.post("/{sos_id}/cancel")
def cancel_sos_event(
    sos_id: str,
    payload: SOSCancelRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancels an active SOS alert event with optional user feedback.
    """
    res = SOSService.cancel_sos(
        db=db,
        sos_id=sos_id,
        user_reference=payload.user_reference or "anonymous_user",
        cancel_reason=payload.reason
    )
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res


@router.post("/{sos_id}/location")
def update_sos_location(
    sos_id: str,
    payload: SOSLocationUpdateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Pushes continuous position update during an active SOS tracking session.
    """
    res = SOSService.add_location_update(
        db=db,
        sos_id=sos_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy
    )
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res


@router.get("/{sos_id}/notifications")
def get_sos_notification_logs(
    sos_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns notification dispatch logs and status for an SOS event.
    """
    res = SOSService.get_sos_status(db=db, sos_id=sos_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS event not found")
    return {
        "success": True,
        "sos_id": sos_id,
        "notification_status": res["notification"]["status"],
        "notification_provider": res["notification"]["provider"],
        "message": "Emergency notification service is not configured." if res["notification"]["status"] == "NOT_CONFIGURED" else "Notification processed."
    }


@router.get("/contacts/list")
def get_emergency_contacts(
    user_reference: str = Query("anonymous_user"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Lists configured emergency contacts for user.
    """
    contacts = SOSService.get_emergency_contacts(db, user_reference=user_reference)
    return {
        "success": True,
        "contacts": contacts
    }


@router.post("/contacts/add", status_code=status.HTTP_201_CREATED)
def add_emergency_contact(
    payload: EmergencyContactCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Adds a new trusted emergency contact for user.
    """
    res = SOSService.create_emergency_contact(
        db=db,
        user_reference=payload.user_reference or "anonymous_user",
        name=payload.name,
        phone_number=payload.phone_number,
        relationship=payload.relationship,
        is_primary=payload.is_primary or False
    )
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res
