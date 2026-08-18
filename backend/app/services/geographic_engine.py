import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.models.incidents import CrimeIncident, CrimeGeographicArea
from app.models.spatial_features import EmergencyFacility, RoadSegment
from app.services.data_processing import validate_coordinates
from app.core.logging import logger


class GeographicEngine:
    """
    Core Geographic Intelligence Engine utilizing PostGIS spatial queries.
    Provides spatial searching, distance calculations, nearest facility lookups, and crime density metrics.
    """

    @staticmethod
    def get_nearby_incidents(
        db: Session, lat: float, lng: float, radius_meters: float = 1000.0, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Retrieves real crime incidents within radius using PostGIS ST_DWithin and ST_Distance.
        """
        if not validate_coordinates(lat, lng):
            raise ValueError("Invalid latitude or longitude coordinates")
        if radius_meters <= 0 or radius_meters > 50000:
            raise ValueError("Radius must be between 1 and 50,000 meters")

        sql = text("""
            SELECT 
                id,
                external_source_id,
                incident_type,
                description,
                occurred_at,
                latitude,
                longitude,
                severity,
                verification_status,
                source_reference,
                ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) AS distance_meters
            FROM crime_incidents
            WHERE location IS NOT NULL
              AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :radius)
            ORDER BY distance_meters ASC
            LIMIT :limit
        """)

        result = db.execute(sql, {"lat": lat, "lng": lng, "radius": radius_meters, "limit": limit}).mappings().all()

        incidents = [
            {
                "id": str(r["id"]),
                "external_source_id": r["external_source_id"],
                "incident_type": r["incident_type"],
                "description": r["description"],
                "occurred_at": r["occurred_at"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "severity": r["severity"],
                "verification_status": r["verification_status"],
                "source_reference": r["source_reference"],
                "distance_meters": round(float(r["distance_meters"]), 2) if r["distance_meters"] is not None else None
            }
            for r in result
        ]

        return {
            "center": {"latitude": lat, "longitude": lng},
            "radius_meters": radius_meters,
            "count": len(incidents),
            "incidents": incidents
        }

    @staticmethod
    def get_nearest_facility(
        db: Session, lat: float, lng: float, facility_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Finds nearest emergency facility of specific type (police, hospital, petrol_station, metro) using PostGIS ST_Distance.
        """
        if not validate_coordinates(lat, lng):
            raise ValueError("Invalid latitude or longitude coordinates")

        sql = text("""
            SELECT 
                id,
                name,
                facility_type,
                address,
                phone,
                is_24_hours,
                source,
                source_reference,
                verification_status,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) AS distance_meters
            FROM emergency_facilities
            WHERE location IS NOT NULL
              AND (:facility_type IS NULL OR LOWER(facility_type) = LOWER(:facility_type))
            ORDER BY distance_meters ASC
            LIMIT 1
        """)

        result = db.execute(sql, {"lat": lat, "lng": lng, "facility_type": facility_type}).mappings().first()

        if not result:
            return None

        return {
            "id": str(result["id"]),
            "name": result["name"],
            "facility_type": result["facility_type"],
            "address": result["address"],
            "phone": result["phone"],
            "is_24_hours": result["is_24_hours"],
            "source": result["source"],
            "source_reference": result["source_reference"],
            "verification_status": result["verification_status"],
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "distance_meters": round(float(result["distance_meters"]), 2)
        }

    @staticmethod
    def get_nearby_facilities(
        db: Session, lat: float, lng: float, radius_meters: float = 2000.0, facility_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves emergency facilities within radius using PostGIS ST_DWithin.
        """
        if not validate_coordinates(lat, lng):
            raise ValueError("Invalid latitude or longitude coordinates")
        if radius_meters <= 0 or radius_meters > 50000:
            raise ValueError("Radius must be between 1 and 50,000 meters")

        sql = text("""
            SELECT 
                id,
                name,
                facility_type,
                address,
                phone,
                is_24_hours,
                source,
                source_reference,
                verification_status,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) AS distance_meters
            FROM emergency_facilities
            WHERE location IS NOT NULL
              AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :radius)
              AND (:facility_type IS NULL OR LOWER(facility_type) = LOWER(:facility_type))
            ORDER BY distance_meters ASC
        """)

        results = db.execute(sql, {"lat": lat, "lng": lng, "radius": radius_meters, "facility_type": facility_type}).mappings().all()

        facilities = [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "facility_type": r["facility_type"],
                "address": r["address"],
                "phone": r["phone"],
                "is_24_hours": r["is_24_hours"],
                "source": r["source"],
                "source_reference": r["source_reference"],
                "verification_status": r["verification_status"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "distance_meters": round(float(r["distance_meters"]), 2)
            }
            for r in results
        ]

        return {
            "center": {"latitude": lat, "longitude": lng},
            "radius_meters": radius_meters,
            "facility_type": facility_type,
            "count": len(facilities),
            "facilities": facilities
        }

    @staticmethod
    def get_crime_density_and_signals(
        db: Session, lat: float, lng: float, radius_meters: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Calculates PostGIS spatial crime density and geographic signals for Phase 6/7 pipeline.
        Density = incident_count / area_sq_km.
        """
        if not validate_coordinates(lat, lng):
            raise ValueError("Invalid latitude or longitude coordinates")
        if radius_meters <= 0 or radius_meters > 50000:
            raise ValueError("Radius must be between 1 and 50,000 meters")

        # 1. Nearby crime count
        sql_count = text("""
            SELECT COUNT(*) AS total_count
            FROM crime_incidents
            WHERE location IS NOT NULL
              AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :radius)
        """)
        count_res = db.execute(sql_count, {"lat": lat, "lng": lng, "radius": radius_meters}).scalar() or 0

        # 2. Nearest police station distance
        nearest_police = GeographicEngine.get_nearest_facility(db, lat, lng, "police")
        dist_police = nearest_police["distance_meters"] if nearest_police else None

        # 3. Nearest hospital distance
        nearest_hosp = GeographicEngine.get_nearest_facility(db, lat, lng, "hospital")
        dist_hosp = nearest_hosp["distance_meters"] if nearest_hosp else None

        # 4. Density per sq km
        area_sq_km = (math.pi * (radius_meters ** 2)) / 1_000_000.0
        crime_density = round(count_res / area_sq_km, 4) if area_sq_km > 0 else 0.0

        return {
            "center": {"latitude": lat, "longitude": lng},
            "radius_meters": radius_meters,
            "area_sq_km": round(area_sq_km, 4),
            "nearby_incident_count": count_res,
            "crime_density_per_sq_km": crime_density,
            "distance_to_nearest_police_station_meters": dist_police,
            "distance_to_nearest_hospital_meters": dist_hosp,
            "nearest_police_station": nearest_police,
            "nearest_hospital": nearest_hosp
        }

    @staticmethod
    def get_geographic_areas(
        db: Session, lat: Optional[float] = None, lng: Optional[float] = None, radius_meters: float = 5000.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real GIS police jurisdiction polygons and geographic area boundaries.
        Handles empty table gracefully without inventing fake polygons.
        """
        if lat is not None and lng is not None:
            if not validate_coordinates(lat, lng):
                raise ValueError("Invalid latitude or longitude coordinates")
            
            sql = text("""
                SELECT 
                    id,
                    name,
                    state,
                    district,
                    area_type,
                    risk_index,
                    source_reference,
                    ST_AsGeoJSON(boundary::geometry) AS geojson_boundary
                FROM crime_geographic_areas
                WHERE boundary IS NOT NULL
                  AND ST_DWithin(boundary, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :radius)
            """)
            results = db.execute(sql, {"lat": lat, "lng": lng, "radius": radius_meters}).mappings().all()
        else:
            sql = text("""
                SELECT 
                    id,
                    name,
                    state,
                    district,
                    area_type,
                    risk_index,
                    source_reference,
                    ST_AsGeoJSON(boundary::geometry) AS geojson_boundary
                FROM crime_geographic_areas
                WHERE boundary IS NOT NULL
            """)
            results = db.execute(sql).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "state": r["state"],
                "district": r["district"],
                "area_type": r["area_type"],
                "risk_index": r["risk_index"],
                "source_reference": r["source_reference"],
                "geojson_boundary": r["geojson_boundary"]
            }
            for r in results
        ]
