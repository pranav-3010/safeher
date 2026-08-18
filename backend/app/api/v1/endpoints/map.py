from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.geographic_engine import GeographicEngine

router = APIRouter()


@router.get("/incidents", summary="List Geocoded Crime Incidents")
def get_map_incidents(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Returns verified geocoded crime incidents for map display.
    """
    return GeographicEngine.get_nearby_incidents(db, lat=17.3850, lng=78.4867, radius_meters=50000.0, limit=limit)


@router.get("/incidents/nearby", summary="Get Nearby Crime Incidents Within Radius")
def get_nearby_incidents(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    radius: float = Query(1000.0, gt=0.0, le=50000.0, description="Search radius in meters"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Returns PostGIS spatial search for crime incidents within target radius.
    """
    try:
        return GeographicEngine.get_nearby_incidents(db, lat=latitude, lng=longitude, radius_meters=radius, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/police-stations/nearby", summary="Get Nearby Police Stations")
def get_nearby_police_stations(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius: float = Query(3000.0, gt=0.0, le=50000.0),
    db: Session = Depends(get_db)
):
    """
    Returns police station locations and distances using PostGIS ST_Distance.
    """
    try:
        return GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius, facility_type="police")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hospitals/nearby", summary="Get Nearby Hospitals & Healthcare Safe Havens")
def get_nearby_hospitals(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius: float = Query(3000.0, gt=0.0, le=50000.0),
    db: Session = Depends(get_db)
):
    """
    Returns hospital and medical facility locations using PostGIS ST_Distance.
    """
    try:
        return GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius, facility_type="hospital")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/emergency-services/nearby", summary="Get All Nearby Emergency Services")
def get_nearby_emergency_services(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius: float = Query(3000.0, gt=0.0, le=50000.0),
    facility_type: Optional[str] = Query(None, description="Optional filter: police, hospital, petrol_station, metro"),
    db: Session = Depends(get_db)
):
    """
    Returns emergency service facilities (Police, Hospital, Metro, Petrol Station) within radius.
    """
    try:
        return GeographicEngine.get_nearby_facilities(db, lat=latitude, lng=longitude, radius_meters=radius, facility_type=facility_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/crime-density", summary="Calculate Crime Density & Geographic Signals")
def get_crime_density(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius: float = Query(1000.0, gt=0.0, le=50000.0),
    db: Session = Depends(get_db)
):
    """
    Calculates PostGIS spatial crime density per sq km and distance to nearest police station & hospital.
    """
    try:
        return GeographicEngine.get_crime_density_and_signals(db, lat=latitude, lng=longitude, radius_meters=radius)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/geographic-areas", summary="Get GIS Police Station Jurisdiction Polygons")
def get_geographic_areas(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    radius: float = Query(5000.0, gt=0.0, le=50000.0),
    db: Session = Depends(get_db)
):
    """
    Returns real GIS police station jurisdiction polygon boundaries.
    """
    try:
        areas = GeographicEngine.get_geographic_areas(db, lat=latitude, lng=longitude, radius_meters=radius)
        return {
            "count": len(areas),
            "geographic_areas": areas
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
