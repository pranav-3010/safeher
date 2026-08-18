from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, select, text
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID, ST_Intersects
from app.models.spatial_features import EmergencyFacility, RoadSegment
from app.models.risk import RiskEvent
from app.models.incidents import CrimeIncident


def find_nearby_emergency_facilities(
    db: Session,
    lat: float,
    lng: float,
    radius_meters: float = 1000.0,
    facility_type: str = None
) -> List[Tuple[EmergencyFacility, float]]:
    """
    Finds emergency facilities within radius_meters of a coordinate point.
    Returns tuples of (EmergencyFacility, distance_in_meters) sorted by distance.
    """
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    
    stmt = (
        select(
            EmergencyFacility,
            func.ST_Distance(EmergencyFacility.location, point).label("distance_meters")
        )
        .where(func.ST_DWithin(EmergencyFacility.location, point, radius_meters))
    )
    
    if facility_type:
        stmt = stmt.where(EmergencyFacility.facility_type == facility_type)
        
    stmt = stmt.order_by("distance_meters")
    
    results = db.execute(stmt).all()
    return [(row[0], float(row[1])) for row in results]


def find_nearby_risk_events(
    db: Session,
    lat: float,
    lng: float,
    radius_meters: float = 500.0
) -> List[Tuple[RiskEvent, float]]:
    """
    Finds active risk events within radius_meters of a coordinate point.
    Returns tuples of (RiskEvent, distance_in_meters).
    """
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    
    stmt = (
        select(
            RiskEvent,
            func.ST_Distance(RiskEvent.location, point).label("distance_meters")
        )
        .where(func.ST_DWithin(RiskEvent.location, point, radius_meters))
        .order_by("distance_meters")
    )
    
    results = db.execute(stmt).all()
    return [(row[0], float(row[1])) for row in results]


def find_nearby_crime_incidents(
    db: Session,
    lat: float,
    lng: float,
    radius_meters: float = 500.0
) -> List[Tuple[CrimeIncident, float]]:
    """
    Finds crime incidents within radius_meters of a coordinate point.
    """
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    
    stmt = (
        select(
            CrimeIncident,
            func.ST_Distance(CrimeIncident.location, point).label("distance_meters")
        )
        .where(func.ST_DWithin(CrimeIncident.location, point, radius_meters))
        .order_by("distance_meters")
    )
    
    results = db.execute(stmt).all()
    return [(row[0], float(row[1])) for row in results]


def find_road_segments_near_point(
    db: Session,
    lat: float,
    lng: float,
    radius_meters: float = 100.0
) -> List[Tuple[RoadSegment, float]]:
    """
    Finds road segments intersecting or within radius_meters of a coordinate point.
    """
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    
    stmt = (
        select(
            RoadSegment,
            func.ST_Distance(RoadSegment.geometry, point).label("distance_meters")
        )
        .where(func.ST_DWithin(RoadSegment.geometry, point, radius_meters))
        .order_by("distance_meters")
    )
    
    results = db.execute(stmt).all()
    return [(row[0], float(row[1])) for row in results]
