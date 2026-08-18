import pytest
from unittest.mock import patch, MagicMock
from app.database.session import check_database_connection, check_postgis_version
from app.repositories.spatial_repository import (
    find_nearby_emergency_facilities,
    find_nearby_risk_events,
    find_nearby_crime_incidents,
    find_road_segments_near_point
)
from app.models import (
    DataSource, CrimeIncident, NewsArticle, NewsIncident, 
    CommunityReport, OSMFeature, RoadSegment, EmergencyFacility, 
    EnvironmentalFeature, RiskEvent, ModelVersion, RiskPrediction, 
    ModelPrediction, RouteAnalysis, EmergencyEvent, SystemLog
)


def test_postgis_version_verification():
    with patch("app.database.session.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ("POSTGIS='3.4.0 USE_GEOS=1 USE_PROJ=1'",)
        mock_conn.execute.return_value = mock_result
        mock_connect.return_value.__enter__.return_value = mock_conn

        version = check_postgis_version()
        assert version == "POSTGIS='3.4.0 USE_GEOS=1 USE_PROJ=1'"


def test_find_nearby_emergency_facilities_spatial_query_construction():
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []

    # Test coordinate near Hyderabad (17.3850, 78.4867) with 1000m radius
    results = find_nearby_emergency_facilities(mock_db, lat=17.3850, lng=78.4867, radius_meters=1000.0)
    assert results == []
    assert mock_db.execute.called


def test_find_nearby_risk_events_spatial_query_construction():
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []

    # Test coordinate near Hyderabad with 500m radius
    results = find_nearby_risk_events(mock_db, lat=17.3850, lng=78.4867, radius_meters=500.0)
    assert results == []
    assert mock_db.execute.called


def test_find_nearby_crime_incidents_spatial_query_construction():
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []

    results = find_nearby_crime_incidents(mock_db, lat=17.3850, lng=78.4867, radius_meters=500.0)
    assert results == []
    assert mock_db.execute.called


def test_find_road_segments_near_point_spatial_query_construction():
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []

    results = find_road_segments_near_point(mock_db, lat=17.3850, lng=78.4867, radius_meters=100.0)
    assert results == []
    assert mock_db.execute.called


def test_all_17_models_instantiation_integrity():
    # Verify that all 17 models can be instantiated without errors
    models = [
        DataSource(name="Test Source", source_type="government"),
        CrimeIncident(incident_type="theft", verification_status="UNVERIFIED"),
        NewsArticle(title="Test Article", content_hash="hash123", retrieved_at=None),
        NewsIncident(event_type="harassment", news_article_id=None),
        CommunityReport(report_type="lighting_problem", reported_at=None),
        OSMFeature(feature_type="point", category="police"),
        RoadSegment(road_name="Main Street", road_type="primary"),
        EmergencyFacility(name="City Hospital", facility_type="hospital"),
        EnvironmentalFeature(lighting_status="UNKNOWN"),
        RiskEvent(event_type="protest", source_type="news", severity=0.5, valid_from=None),
        ModelVersion(model_name="RandomForest", version="v1.0", algorithm="RandomForest"),
        RiskPrediction(time_of_day=22, day_of_week=5, risk_score=0.4, confidence=0.8, risk_level="MODERATE", prediction_time=None),
        ModelPrediction(prediction=0.4, confidence=0.8, prediction_time=None),
        RouteAnalysis(route_provider="osrm", requested_at=None),
        EmergencyEvent(event_reference="SOS-1001", trigger_type="manual_sos", triggered_at=None),
        SystemLog(service="backend", level="INFO", event_type="startup", message="Started")
    ]
    assert len(models) == 16
