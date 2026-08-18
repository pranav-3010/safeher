import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.sos import SOSEvent, SOSLocationUpdate, EmergencyContact
from app.services.data_processing import validate_coordinates, clean_text_string
from app.core.config import settings
from app.core.logging import logger


class SOSService:
    """
    Phase 11 Emergency SOS Service.
    Handles SOS lifecycle state machine, location tracking, duplicate protection,
    notification provider integration (reporting NOT_CONFIGURED when unconfigured),
    cancellation flow, and protected emergency operator querying.
    """

    @staticmethod
    def create_sos(
        db: Session,
        user_reference: str = "anonymous_user",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Creates a new emergency SOS event.
        Guarantees duplicate SOS protection if an active event already exists.
        """
        user_ref = clean_text_string(user_reference) or "anonymous_user"

        # 1. Duplicate Protection Check
        existing_active = db.query(SOSEvent).filter(
            SOSEvent.user_reference == user_ref,
            SOSEvent.status.in_(["CREATED", "ACTIVE", "ACKNOWLEDGED"])
        ).first()

        if existing_active:
            return {
                "success": False,
                "already_active": True,
                "message": "An SOS request is already active.",
                "sos_id": str(existing_active.id),
                "status": existing_active.status,
                "created_at": existing_active.created_at.isoformat() if existing_active.created_at else None
            }

        # 2. Location Validation
        has_valid_coords = validate_coordinates(latitude, longitude)
        lat = float(latitude) if has_valid_coords else None
        lng = float(longitude) if has_valid_coords else None

        # 3. Notification Provider Config Check (No fake notifications!)
        # Check if Twilio / SMS provider key is configured
        twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        twilio_auth = getattr(settings, "TWILIO_AUTH_TOKEN", None)

        if twilio_sid and twilio_auth:
            notification_status = "PENDING"
            notification_provider = "twilio_sms"
        else:
            notification_status = "NOT_CONFIGURED"
            notification_provider = "none"

        now_utc = datetime.now(timezone.utc)

        sos_event = SOSEvent(
            user_reference=user_ref,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy,
            status="ACTIVE",
            notification_status=notification_status,
            notification_provider=notification_provider,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(sos_event)
        db.flush()

        # Update PostGIS Point Geometry if coordinates valid
        if lat is not None and lng is not None:
            db.execute(text(
                "UPDATE sos_events SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
            ), {"lng": lng, "lat": lat, "id": sos_event.id})

        db.commit()
        db.refresh(sos_event)

        logger.info(f"[SafeHer SOS] Activated emergency SOS #{sos_event.id} for user '{user_ref}' (Location: {lat}, {lng})")

        return {
            "success": True,
            "already_active": False,
            "sos_id": str(sos_event.id),
            "status": sos_event.status,
            "created_at": sos_event.created_at.isoformat(),
            "location": {
                "available": has_valid_coords,
                "latitude": lat,
                "longitude": lng,
                "accuracy": accuracy,
                "status_text": "AVAILABLE ✓" if has_valid_coords else "Location unavailable"
            },
            "notification": {
                "status": sos_event.notification_status,
                "provider": sos_event.notification_provider,
                "message": "Emergency notification service is not configured." if notification_status == "NOT_CONFIGURED" else "Emergency notification pending dispatch."
            },
            "scientific_disclaimer": "Emergency request created. System never falsely claims emergency services were contacted unless verified."
        }

    @staticmethod
    def get_sos_status(db: Session, sos_id: str, user_reference: str = "anonymous_user") -> Optional[Dict[str, Any]]:
        """
        Retrieves status and tracking history for an SOS event.
        """
        try:
            sos_uuid = uuid.UUID(sos_id)
        except ValueError:
            return None

        event = db.query(SOSEvent).filter(SOSEvent.id == sos_uuid).first()
        if not event:
            return None

        # Fetch position update history
        history_records = db.query(SOSLocationUpdate).filter(
            SOSLocationUpdate.sos_id == sos_uuid
        ).order_by(SOSLocationUpdate.recorded_at.desc()).limit(50).all()

        location_history = [
            {
                "id": str(h.id),
                "recorded_at": h.recorded_at.isoformat(),
                "latitude": h.latitude,
                "longitude": h.longitude,
                "accuracy": h.accuracy
            }
            for h in history_records
        ]

        has_coords = validate_coordinates(event.latitude, event.longitude)

        return {
            "success": True,
            "sos_id": str(event.id),
            "user_reference": event.user_reference,
            "status": event.status,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "acknowledged_at": event.acknowledged_at.isoformat() if event.acknowledged_at else None,
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
            "cancelled_at": event.cancelled_at.isoformat() if event.cancelled_at else None,
            "cancel_reason": event.cancel_reason,
            "location": {
                "available": has_coords,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "accuracy": event.accuracy,
                "status_text": "AVAILABLE ✓" if has_coords else "Location unavailable"
            },
            "notification": {
                "status": event.notification_status,
                "provider": event.notification_provider
            },
            "location_history_count": len(location_history),
            "location_history": location_history
        }

    @staticmethod
    def cancel_sos(db: Session, sos_id: str, user_reference: str = "anonymous_user", cancel_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancels an active SOS request with optional reason.
        """
        try:
            sos_uuid = uuid.UUID(sos_id)
        except ValueError:
            return {"success": False, "message": "Invalid SOS ID format."}

        event = db.query(SOSEvent).filter(SOSEvent.id == sos_uuid).first()
        if not event:
            return {"success": False, "message": "SOS event not found."}

        if event.status in ["CANCELLED", "RESOLVED"]:
            return {
                "success": True,
                "message": f"SOS event was already {event.status.lower()}.",
                "sos_id": str(event.id),
                "status": event.status
            }

        now_utc = datetime.now(timezone.utc)
        event.status = "CANCELLED"
        event.cancelled_at = now_utc
        event.cancel_reason = clean_text_string(cancel_reason) or "User cancelled emergency SOS request"
        event.updated_at = now_utc

        db.commit()

        logger.info(f"[SafeHer SOS] Cancelled SOS #{event.id} by user '{user_reference}' (Reason: {event.cancel_reason})")

        return {
            "success": True,
            "message": "SOS request cancelled successfully.",
            "sos_id": str(event.id),
            "status": "CANCELLED",
            "cancelled_at": now_utc.isoformat(),
            "cancel_reason": event.cancel_reason
        }

    @staticmethod
    def add_location_update(
        db: Session,
        sos_id: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Appends periodic position update to active SOS history.
        """
        try:
            sos_uuid = uuid.UUID(sos_id)
        except ValueError:
            return {"success": False, "message": "Invalid SOS ID format."}

        event = db.query(SOSEvent).filter(SOSEvent.id == sos_uuid).first()
        if not event:
            return {"success": False, "message": "SOS event not found."}

        if event.status not in ["CREATED", "ACTIVE", "ACKNOWLEDGED"]:
            return {"success": False, "message": f"Cannot update location for inactive SOS event in state '{event.status}'."}

        if not validate_coordinates(latitude, longitude):
            return {"success": False, "message": "Invalid latitude/longitude coordinates."}

        lat = float(latitude)
        lng = float(longitude)
        now_utc = datetime.now(timezone.utc)

        # Update current event position
        event.latitude = lat
        event.longitude = lng
        event.accuracy = accuracy
        event.updated_at = now_utc

        # PostGIS geometry update for main event
        db.execute(text(
            "UPDATE sos_events SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
        ), {"lng": lng, "lat": lat, "id": event.id})

        # Insert history tracking record
        loc_update = SOSLocationUpdate(
            sos_id=event.id,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy,
            recorded_at=now_utc
        )
        db.add(loc_update)
        db.flush()

        db.execute(text(
            "UPDATE sos_location_updates SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography WHERE id = :id"
        ), {"lng": lng, "lat": lat, "id": loc_update.id})

        db.commit()

        return {
            "success": True,
            "sos_id": str(event.id),
            "update_id": str(loc_update.id),
            "recorded_at": now_utc.isoformat(),
            "latitude": lat,
            "longitude": lng,
            "accuracy": accuracy
        }

    @staticmethod
    def get_active_sos_events(db: Session) -> List[Dict[str, Any]]:
        """
        Protected query returning all active SOS alerts for emergency operators.
        """
        active_events = db.query(SOSEvent).filter(
            SOSEvent.status.in_(["CREATED", "ACTIVE", "ACKNOWLEDGED"])
        ).order_by(SOSEvent.created_at.desc()).all()

        results = []
        for evt in active_events:
            has_coords = validate_coordinates(evt.latitude, evt.longitude)
            results.append({
                "sos_id": str(evt.id),
                "user_reference": evt.user_reference,
                "status": evt.status,
                "created_at": evt.created_at.isoformat() if evt.created_at else None,
                "updated_at": evt.updated_at.isoformat() if evt.updated_at else None,
                "notification_status": evt.notification_status,
                "notification_provider": evt.notification_provider,
                "latitude": evt.latitude if has_coords else None,
                "longitude": evt.longitude if has_coords else None,
                "accuracy": evt.accuracy,
                "location_text": f"{evt.latitude:.4f}, {evt.longitude:.4f}" if has_coords else "LOCATION_UNAVAILABLE"
            })
        return results

    @staticmethod
    def get_emergency_contacts(db: Session, user_reference: str = "anonymous_user") -> List[Dict[str, Any]]:
        """
        Fetches configured emergency contacts for user.
        """
        contacts = db.query(EmergencyContact).filter(
            EmergencyContact.user_reference == clean_text_string(user_reference) or "anonymous_user"
        ).all()

        return [
            {
                "id": str(c.id),
                "name": c.name,
                "phone_number": c.phone_number,
                "relationship": c.relationship,
                "is_primary": c.is_primary
            }
            for c in contacts
        ]

    @staticmethod
    def create_emergency_contact(
        db: Session,
        user_reference: str,
        name: str,
        phone_number: str,
        relationship: Optional[str] = "Trusted Contact",
        is_primary: bool = False
    ) -> Dict[str, Any]:
        """
        Adds a trusted emergency contact for user.
        """
        c_name = clean_text_string(name)
        c_phone = clean_text_string(phone_number)

        if not c_name or not c_phone:
            return {"success": False, "message": "Name and phone number are required."}

        user_ref = clean_text_string(user_reference) or "anonymous_user"

        if is_primary:
            db.query(EmergencyContact).filter(
                EmergencyContact.user_reference == user_ref
            ).update({"is_primary": False})

        contact = EmergencyContact(
            user_reference=user_ref,
            name=c_name,
            phone_number=c_phone,
            relationship=clean_text_string(relationship) or "Trusted Contact",
            is_primary=is_primary
        )
        db.add(contact)
        db.commit()

        return {
            "success": True,
            "id": str(contact.id),
            "name": contact.name,
            "phone_number": contact.phone_number,
            "relationship": contact.relationship,
            "is_primary": contact.is_primary
        }
