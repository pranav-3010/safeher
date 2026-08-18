import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.geographic_engine import GeographicEngine
from app.database.session import get_db

client = TestClient(app)


def test_invalid_coordinates_validation_handling():
    with pytest.raises(ValueError):
        GeographicEngine.get_nearby_incidents(None, lat=100.0, lng=78.4867, radius_meters=1000)
    with pytest.raises(ValueError):
        GeographicEngine.get_nearby_incidents(None, lat=17.3850, lng=200.0, radius_meters=1000)


def test_invalid_radius_validation_handling():
    with pytest.raises(ValueError):
        GeographicEngine.get_nearby_incidents(None, lat=17.3850, lng=78.4867, radius_meters=-500)
    with pytest.raises(ValueError):
        GeographicEngine.get_nearby_incidents(None, lat=17.3850, lng=78.4867, radius_meters=60000)


def test_api_nearby_incidents_validation():
    # Invalid lat > 90
    res = client.get("/api/v1/map/incidents/nearby?latitude=100.0&longitude=78.4867&radius=1000")
    assert res.status_code == 422  # Unprocessable Entity via Pydantic Query validation

    # Invalid radius > 50000
    res = client.get("/api/v1/map/incidents/nearby?latitude=17.3850&longitude=78.4867&radius=60000")
    assert res.status_code == 422


def test_api_nearby_incidents_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/map/incidents/nearby?latitude=17.3850&longitude=78.4867&radius=1000")
        assert res.status_code == 200
        data = res.json()
        assert "center" in data
        assert "radius_meters" in data
        assert data["radius_meters"] == 1000.0
        assert "incidents" in data
    finally:
        app.dependency_overrides.clear()


def test_api_police_stations_nearby_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/map/police-stations/nearby?latitude=17.3850&longitude=78.4867&radius=3000")
        assert res.status_code == 200
        data = res.json()
        assert "facilities" in data
    finally:
        app.dependency_overrides.clear()


def test_api_hospitals_nearby_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/map/hospitals/nearby?latitude=17.3850&longitude=78.4867&radius=3000")
        assert res.status_code == 200
        data = res.json()
        assert "facilities" in data
    finally:
        app.dependency_overrides.clear()


def test_api_crime_density_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.execute.return_value.mappings.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/map/crime-density?latitude=17.3850&longitude=78.4867&radius=1000")
        assert res.status_code == 200
        data = res.json()
        assert "nearby_incident_count" in data
        assert "crime_density_per_sq_km" in data
        assert "distance_to_nearest_police_station_meters" in data
        assert "distance_to_nearest_hospital_meters" in data
    finally:
        app.dependency_overrides.clear()


def test_api_geographic_areas_endpoint():
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.get("/api/v1/map/geographic-areas")
        assert res.status_code == 200
        data = res.json()
        assert "count" in data
        assert "geographic_areas" in data
    finally:
        app.dependency_overrides.clear()


def test_static_map_frontend_serving():
    res = client.get("/static/")
    assert res.status_code == 200
    assert "SafeHer — Maps & Geographic Intelligence" in res.text
