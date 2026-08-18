from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.services.geographic_engine import GeographicEngine
from app.models.incidents import CrimeStatistic
from app.services.data_processing import validate_coordinates
from app.core.logging import logger


class SafetyContextBuilder:
    """
    Backend Safety Context Builder for LLM Intelligence Layer.
    Aggregates verified PostGIS spatial features, nearby facilities, crime incidents,
    and historical NCRB statistics into a token-efficient, privacy-safe context payload.
    """

    @staticmethod
    def build_location_context(
        db: Session,
        latitude: float,
        longitude: float,
        radius_meters: float = 2000.0,
        destination_lat: Optional[float] = None,
        destination_lng: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds comprehensive verified geographic and safety context around target coordinates.
        """
        if not validate_coordinates(latitude, longitude):
            raise ValueError("Invalid origin latitude or longitude coordinates")
        if destination_lat is not None and destination_lng is not None:
            if not validate_coordinates(destination_lat, destination_lng):
                raise ValueError("Invalid destination latitude or longitude coordinates")

        # 1. Nearby crime incidents (verified records only)
        nearby_incidents_data = GeographicEngine.get_nearby_incidents(db, lat=latitude, lng=longitude, radius_meters=radius_meters)
        incidents_summary = []
        for inc in nearby_incidents_data.get("incidents", [])[:10]:  # Limit top 10 for context window
            incidents_summary.append({
                "type": inc["incident_type"],
                "description": inc.get("description"),
                "severity": inc.get("severity"),
                "occurred_at": str(inc.get("occurred_at")) if inc.get("occurred_at") else None,
                "distance_meters": inc.get("distance_meters"),
                "source": inc.get("source_reference", "Official Database")
            })

        # 2. Nearby Police Stations
        police_data = GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius_meters, facility_type="police")
        police_stations = [
            {
                "name": p["name"],
                "distance_meters": p["distance_meters"],
                "address": p.get("address"),
                "is_24_hours": p.get("is_24_hours", True)
            }
            for p in police_data.get("facilities", [])[:5]
        ]

        # 3. Nearby Hospitals
        hospital_data = GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius_meters, facility_type="hospital")
        hospitals = [
            {
                "name": h["name"],
                "distance_meters": h["distance_meters"],
                "address": h.get("address")
            }
            for h in hospital_data.get("facilities", [])[:5]
        ]

        # 4. Nearby Emergency Facilities (Metro & Petrol Stations)
        emergency_data = GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius_meters)
        emergency_facilities = [
            {
                "name": f["name"],
                "facility_type": f["facility_type"],
                "distance_meters": f["distance_meters"]
            }
            for f in emergency_data.get("facilities", [])[:5]
            if f["facility_type"] not in ["police", "hospital"]
        ]

        # 5. Spatial Crime Density & Signals
        signals = GeographicEngine.get_crime_density_and_signals(db, lat=latitude, lng=longitude, radius_meters=radius_meters)

        # 6. Historical NCRB Crime Statistics
        ncrb_stats = db.query(CrimeStatistic).limit(5).all()
        ncrb_summary = [
            {
                "year": s.year,
                "state": s.state,
                "district_or_city": s.district_or_city,
                "crime_type": s.crime_type,
                "case_count": s.case_count,
                "crime_rate": s.crime_rate
            }
            for s in ncrb_stats
        ]

        # 7. Jurisdiction Polygons
        areas = GeographicEngine.get_geographic_areas(db, lat=latitude, lng=longitude, radius_meters=radius_meters)
        jurisdiction_summary = [
            {
                "name": a["name"],
                "district": a.get("district"),
                "risk_index": a.get("risk_index")
            }
            for a in areas[:3]
        ]

        # Destination context if supplied
        destination_context = None
        if destination_lat is not None and destination_lng is not None:
            dest_police = GeographicEngine.get_nearest_facility(db, destination_lat, destination_lng, "police")
            dest_hosp = GeographicEngine.get_nearest_facility(db, destination_lat, destination_lng, "hospital")
            dest_incidents = GeographicEngine.get_nearby_incidents(db, lat=destination_lat, lng=destination_lng, radius_meters=radius_meters)
            destination_context = {
                "destination_center": {"latitude": destination_lat, "longitude": destination_lng},
                "destination_nearby_incidents_count": dest_incidents.get("count", 0),
                "nearest_police_to_destination_meters": dest_police["distance_meters"] if dest_police else None,
                "nearest_hospital_to_destination_meters": dest_hosp["distance_meters"] if dest_hosp else None
            }

        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "origin_center": {"latitude": latitude, "longitude": longitude},
            "search_radius_meters": radius_meters,
            "nearby_verified_incidents_count": len(incidents_summary),
            "incidents": incidents_summary,
            "nearest_police_station_distance_meters": signals.get("distance_to_nearest_police_station_meters"),
            "police_stations": police_stations,
            "nearest_hospital_distance_meters": signals.get("distance_to_nearest_hospital_meters"),
            "hospitals": hospitals,
            "other_emergency_facilities": emergency_facilities,
            "spatial_crime_density_per_sq_km": signals.get("crime_density_per_sq_km", 0.0),
            "jurisdiction_areas": jurisdiction_summary,
            "historical_ncrb_statistics": ncrb_summary,
            "destination_context": destination_context,
            "data_provenance": {
                "verified_database_source": "Supabase PostgreSQL + PostGIS",
                "osm_gis_source": "Official OpenStreetMap v0.6 API",
                "ncrb_source": "National Crime Records Bureau Open Data"
            }
        }
