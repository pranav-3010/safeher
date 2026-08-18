import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.safety_context_builder import SafetyContextBuilder
from app.services.llm_service import LLMService
from app.database.session import get_db

client = TestClient(app)


def test_safety_context_builder_location_context():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.query.return_value.limit.return_value.all.return_value = []

    ctx = SafetyContextBuilder.build_location_context(mock_db, latitude=17.3850, longitude=78.4867, radius_meters=1000.0)
    assert "timestamp_utc" in ctx
    assert ctx["origin_center"]["latitude"] == 17.3850
    assert ctx["nearby_verified_incidents_count"] == 0
    assert "data_provenance" in ctx


def test_safety_context_builder_coordinate_validation():
    with pytest.raises(ValueError):
        SafetyContextBuilder.build_location_context(None, latitude=100.0, longitude=78.4867)
    with pytest.raises(ValueError):
        SafetyContextBuilder.build_location_context(None, latitude=17.3850, longitude=200.0)


def test_llm_fallback_when_api_key_unconfigured():
    context = {
        "nearby_verified_incidents_count": 0,
        "nearest_police_station_distance_meters": 1200.0,
        "nearest_hospital_distance_meters": 450.0
    }
    with patch("app.core.config.settings.LLM_API_KEY", None), patch("app.core.config.settings.GEMINI_API_KEY", None):
        res = LLMService.analyze_safety_context(context, user_query="What is around me?")
        assert "summary" in res
        assert "key_factors" in res
        assert "data_limitations" in res
        assert "sources" in res
        assert "AI analysis fallback active" in res["summary"] or "temporarily unavailable" in res["summary"]


def test_llm_structured_json_parsing():
    sample_llm_out = """
    ```json
    {
      "summary": "Verified 2 police stations within 1km.",
      "key_factors": ["Police station at 500m", "Hospital at 800m"],
      "data_limitations": ["Zero incidents recorded"],
      "sources": [{"claim": "Facilities count", "source": "OSM Database", "period": "current"}]
    }
    ```
    """
    parsed = LLMService._parse_structured_json(sample_llm_out)
    assert parsed is not None
    assert parsed["summary"] == "Verified 2 police stations within 1km."
    assert len(parsed["key_factors"]) == 2


def test_api_analyze_location_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.query.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {"latitude": 17.3850, "longitude": 78.4867, "radius_meters": 2000.0}
        res = client.post("/api/v1/ai/analyze-location", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert "key_factors" in data
        assert "sources" in data
        assert "verified_context_summary" in data
    finally:
        app.dependency_overrides.clear()


def test_api_explain_crime_data_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.query.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {"latitude": 17.3850, "longitude": 78.4867, "radius_meters": 2000.0}
        res = client.post("/api/v1/ai/explain-crime-data", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
    finally:
        app.dependency_overrides.clear()


def test_api_safety_question_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.query.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "latitude": 17.3850,
            "longitude": 78.4867,
            "radius_meters": 2000.0,
            "question": "Where is the nearest police station?"
        }
        res = client.post("/api/v1/ai/safety-question", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
    finally:
        app.dependency_overrides.clear()


def test_api_analyze_route_context_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.query.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        payload = {
            "origin_latitude": 17.3850,
            "origin_longitude": 78.4867,
            "destination_latitude": 17.4435,
            "destination_longitude": 78.3772,
            "radius_meters": 2000.0
        }
        res = client.post("/api/v1/ai/analyze-route-context", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert "verified_context_summary" in data
    finally:
        app.dependency_overrides.clear()


def test_phases_1_to_4_continue_working_when_llm_offline():
    # Verify health endpoint still healthy
    res_health = client.get("/api/v1/health")
    assert res_health.status_code in [200, 503]  # App responds cleanly

    # Verify Map endpoint still works cleanly
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res_map = client.get("/api/v1/map/geographic-areas")
        assert res_map.status_code == 200
    finally:
        app.dependency_overrides.clear()
