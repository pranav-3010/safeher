import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.services.geographic_engine import GeographicEngine
from app.models.incidents import CrimeIncident
from app.core.logging import logger

class DynamicRiskEngine:
    """
    Phase 7 Dynamic Risk Engine.
    Measures current safety risk based strictly on verified recent incidents, PostGIS spatial queries,
    time decay, distance decay, and data freshness tracking.
    """

    # Configurable Decay & Risk Parameters
    LAMBDA_TIME_DECAY = 0.05       # Time decay coefficient per hour
    MU_DISTANCE_DECAY = 0.8        # Distance decay coefficient per kilometer
    DEFAULT_RADIUS_METERS = 2000.0 # Analysis radius
    DEFAULT_WINDOW_HOURS = 24.0    # Recency window

    @staticmethod
    def calculate_data_freshness(latest_timestamp: Optional[datetime], current_time: datetime) -> Dict[str, Any]:
        """
        Calculates data age in minutes and classifies freshness status.
        Status: CURRENT (<= 60 mins), RECENT (<= 24 hours), STALE (> 24 hours), UNAVAILABLE (no timestamp).
        """
        if not latest_timestamp:
            return {
                "last_updated": None,
                "age_minutes": None,
                "status": "UNAVAILABLE"
            }

        # Ensure tz-aware datetimes
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        age_seconds = (current_time - latest_timestamp).total_seconds()
        age_minutes = max(0.0, round(age_seconds / 60.0, 1))

        if age_minutes <= 60.0:
            status = "CURRENT"
        elif age_minutes <= 1440.0: # 24 hours
            status = "RECENT"
        else:
            status = "STALE"

        return {
            "last_updated": latest_timestamp.isoformat(),
            "age_minutes": age_minutes,
            "status": status
        }

    @staticmethod
    def evaluate_dynamic_risk(
        db: Session,
        latitude: float,
        longitude: float,
        request_timestamp: Optional[datetime] = None,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        window_hours: float = DEFAULT_WINDOW_HOURS
    ) -> Dict[str, Any]:
        """
        Evaluates dynamic risk score for a target location.
        Queries PostGIS for recent verified incidents, applies time & distance decay, and tracks data freshness.
        """
        start_eval_time = datetime.now(timezone.utc)
        ref_time = request_timestamp or start_eval_time
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        # 1. PostGIS Spatial & Recency Query
        spatial_result = GeographicEngine.get_nearby_incidents(
            db, lat=latitude, lng=longitude, radius_meters=radius_meters, limit=100
        )
        raw_incidents = spatial_result.get("incidents", [])

        if not raw_incidents:
            latest_inc = db.query(CrimeIncident).order_by(CrimeIncident.occurred_at.desc()).first()
            latest_ts = latest_inc.occurred_at if latest_inc else None
            freshness = DynamicRiskEngine.calculate_data_freshness(latest_ts, ref_time)

            return {
                "success": True,
                "dynamic_risk": None,
                "status": "INSUFFICIENT_CURRENT_DATA",
                "message": "Current dynamic risk unavailable because no verified incidents were found within the analysis radius.",
                "recent_incidents": {
                    "count": 0,
                    "window_hours": window_hours,
                    "radius_meters": radius_meters,
                    "list": []
                },
                "data_freshness": freshness,
                "factors": ["No verified recent incidents found within search radius."],
                "sources": ["Supabase PostgreSQL + PostGIS"],
                "scientific_disclaimer": "Calculated dynamic risk based strictly on available verified recent data. Not a guarantee of personal safety."
            }

        # 2. Process Incidents with Time Decay & Distance Decay
        total_risk_accumulator = 0.0
        processed_incidents: List[Dict[str, Any]] = []
        latest_incident_time: Optional[datetime] = None

        for inc in raw_incidents:
            # Parse timestamp
            occ_str = inc.get("occurred_at")
            if isinstance(occ_str, str):
                occ_dt = datetime.fromisoformat(occ_str.replace("Z", "+00:00"))
            elif isinstance(occ_str, datetime):
                occ_dt = occ_str
            else:
                occ_dt = ref_time

            if occ_dt.tzinfo is None:
                occ_dt = occ_dt.replace(tzinfo=timezone.utc)

            if latest_incident_time is None or occ_dt > latest_incident_time:
                latest_incident_time = occ_dt

            # Time Decay: exp(-lambda * delta_t_hours)
            delta_t_hours = max(0.0, (ref_time - occ_dt).total_seconds() / 3600.0)
            time_decay = math.exp(-DynamicRiskEngine.LAMBDA_TIME_DECAY * delta_t_hours)

            # Distance Decay: exp(-mu * dist_km)
            dist_meters = inc.get("distance_meters", 1000.0)
            dist_km = dist_meters / 1000.0
            distance_decay = math.exp(-DynamicRiskEngine.MU_DISTANCE_DECAY * dist_km)

            # Severity
            severity = inc.get("severity", 0.5)

            # Risk Contribution = severity * time_decay * distance_decay
            contribution = severity * time_decay * distance_decay
            total_risk_accumulator += contribution

            processed_incidents.append({
                "id": inc.get("id"),
                "type": inc.get("incident_type"),
                "occurred_at": occ_dt.isoformat(),
                "latitude": inc.get("latitude"),
                "longitude": inc.get("longitude"),
                "severity": severity,
                "distance_meters": round(dist_meters, 1),
                "time_decay": round(time_decay, 4),
                "distance_decay": round(distance_decay, 4),
                "risk_contribution": round(contribution, 4)
            })

        # Calculate final deterministic Dynamic Risk Score bounded [0.0, 1.0]
        dynamic_score = round(min(1.0, total_risk_accumulator), 4)

        # Map Risk Level
        if dynamic_score >= 0.60:
            risk_level = "High"
        elif dynamic_score >= 0.25:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

        # Calculate Data Freshness
        freshness = DynamicRiskEngine.calculate_data_freshness(latest_incident_time, ref_time)

        # Generate factual explanation factors
        nearest_inc = min(processed_incidents, key=lambda x: x["distance_meters"])
        factors = [
            f"{len(processed_incidents)} verified incidents recorded within {radius_meters/1000.0:.1f}km search radius.",
            f"Nearest recorded incident: {nearest_inc['type']} ({nearest_inc['distance_meters']}m away).",
            f"Calculated spatial-temporal decay risk contribution: {total_risk_accumulator:.2f}."
        ]

        processing_ms = round((datetime.now(timezone.utc) - start_eval_time).total_seconds() * 1000.0, 2)
        logger.info(
            f"Dynamic Risk Evaluation Complete: loc=({latitude},{longitude}), count={len(processed_incidents)}, "
            f"score={dynamic_score}, level={risk_level}, time_ms={processing_ms}"
        )

        return {
            "success": True,
            "dynamic_risk": {
                "score": dynamic_score,
                "level": risk_level,
                "confidence": None  # Omitted/null per scientific specification
            },
            "recent_incidents": {
                "count": len(processed_incidents),
                "radius_meters": radius_meters,
                "window_hours": window_hours,
                "list": processed_incidents
            },
            "data_freshness": freshness,
            "factors": factors,
            "sources": ["Supabase PostgreSQL + PostGIS"],
            "scientific_disclaimer": "Calculated dynamic risk based strictly on available verified recent data. Not a guarantee of personal safety."
        }
