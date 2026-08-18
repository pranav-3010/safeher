from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.data_source import DataSource, SourceFetch
from app.models.incidents import CrimeIncident, NewsArticle, CommunityReport
from app.models.spatial_features import OSMFeature, RoadSegment, EmergencyFacility

router = APIRouter()


@router.get("/sources", summary="List All Data Sources")
def get_data_sources(db: Session = Depends(get_db)):
    """
    Returns registered data sources and active status.
    """
    sources = db.query(DataSource).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "organization": s.organization,
            "source_type": s.source_type,
            "official_url": s.official_url,
            "geographic_coverage": s.geographic_coverage,
            "is_active": s.is_active,
            "is_verified": s.is_verified,
            "created_at": s.created_at
        }
        for s in sources
    ]


@router.get("/sources/{source_id}", summary="Get Data Source Details & Fetch History")
def get_data_source_detail(source_id: UUID, db: Session = Depends(get_db)):
    """
    Returns specific data source details and recent fetch logs.
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

    fetches = db.query(SourceFetch).filter(SourceFetch.data_source_id == source_id).order_by(SourceFetch.started_at.desc()).limit(10).all()

    return {
        "id": str(source.id),
        "name": source.name,
        "source_type": source.source_type,
        "official_url": source.official_url,
        "is_active": source.is_active,
        "recent_fetches": [
            {
                "fetch_id": str(f.id),
                "started_at": f.started_at,
                "completed_at": f.completed_at,
                "status": f.status,
                "records_fetched": f.records_fetched,
                "records_inserted": f.records_inserted,
                "records_rejected": f.records_rejected,
                "error_message": f.error_message
            }
            for f in fetches
        ]
    }


@router.get("/sources/{source_id}/health", summary="Get Data Source Ingestion Health Metrics")
def get_source_health(source_id: UUID, db: Session = Depends(get_db)):
    """
    Internal admin monitoring endpoint for data source health.
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

    last_success = db.query(SourceFetch).filter(SourceFetch.data_source_id == source_id, SourceFetch.status == "COMPLETED").order_by(SourceFetch.completed_at.desc()).first()
    last_failure = db.query(SourceFetch).filter(SourceFetch.data_source_id == source_id, SourceFetch.status == "FAILED").order_by(SourceFetch.completed_at.desc()).first()
    
    total_fetched = db.query(func.sum(SourceFetch.records_fetched)).filter(SourceFetch.data_source_id == source_id).scalar() or 0
    total_rejected = db.query(func.sum(SourceFetch.records_rejected)).filter(SourceFetch.data_source_id == source_id).scalar() or 0

    return {
        "source_id": str(source.id),
        "source_name": source.name,
        "is_active": source.is_active,
        "health_status": "HEALTHY" if last_success and (not last_failure or last_success.completed_at > last_failure.completed_at) else "DEGRADED",
        "last_successful_fetch": last_success.completed_at if last_success else None,
        "last_failed_fetch": last_failure.completed_at if last_failure else None,
        "total_records_fetched": total_fetched,
        "total_records_rejected": total_rejected
    }


@router.get("/quality", summary="Data Quality & Provenance Report")
def get_data_quality_report(db: Session = Depends(get_db)):
    """
    Returns actual ingested data statistics, missing coordinate metrics, and table record counts.
    """
    crime_count = db.query(CrimeIncident).count()
    crime_missing_coords = db.query(CrimeIncident).filter(CrimeIncident.latitude.is_(None)).count()

    news_count = db.query(NewsArticle).count()
    osm_feature_count = db.query(OSMFeature).count()
    road_segment_count = db.query(RoadSegment).count()
    facility_count = db.query(EmergencyFacility).count()
    community_count = db.query(CommunityReport).count()

    return {
        "report_generated_at": datetime.now(timezone.utc),
        "ingested_records": {
            "crime_incidents": crime_count,
            "news_articles": news_count,
            "osm_features": osm_feature_count,
            "road_segments": road_segment_count,
            "emergency_facilities": facility_count,
            "community_reports": community_count
        },
        "data_quality_metrics": {
            "crime_missing_coordinates": crime_missing_coords,
            "crime_coordinate_coverage_pct": round(((crime_count - crime_missing_coords) / max(1, crime_count)) * 100, 2)
        }
    }
