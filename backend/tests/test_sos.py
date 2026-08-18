import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import get_db
from app.services.sos_service import SOSService

client = TestClient(app)


def test_sos_service_create_and_cancel_flow():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Test creating SOS with valid coordinates
    res = SOSService.create_sos(
        db=mock_db,
        user_reference="user_pytest_1",
        latitude=17.4435,
        longitude=78.3772,
        accuracy=10.0
    )

    assert res["success"] is True
    assert res["already_active"] is False
    assert res["status"] == "ACTIVE"
    assert res["location"]["available"] is True
    assert res["location"]["latitude"] == 17.4435
    assert res["notification"]["status"] == "NOT_CONFIGURED"
    assert "scientific_disclaimer" in res


def test_sos_service_duplicate_protection():
    mock_db = MagicMock()
    mock_event = MagicMock()
    mock_event.id = "11111111-2222-3333-4444-555555555555"
    mock_event.status = "ACTIVE"
    mock_event.created_at = None

    mock_db.query.return_value.filter.return_value.first.return_value = mock_event

    res = SOSService.create_sos(
        db=mock_db,
        user_reference="user_pytest_duplicate",
        latitude=17.4435,
        longitude=78.3772
    )

    assert res["success"] is False
    assert res["already_active"] is True
    assert "already active" in res["message"]
    assert res["sos_id"] == "11111111-2222-3333-4444-555555555555"


def test_sos_service_location_unavailable_handling():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    res = SOSService.create_sos(
        db=mock_db,
        user_reference="user_pytest_noloc",
        latitude=None,
        longitude=None
    )

    assert res["success"] is True
    assert res["location"]["available"] is False
    assert res["location"]["latitude"] is None
    assert res["location"]["status_text"] == "Location unavailable"


def test_sos_api_trigger_endpoint():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.post("/api/v1/sos", json={
            "latitude": 17.4435,
            "longitude": 78.3772,
            "accuracy": 5.0,
            "user_reference": "user_api_test"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "ACTIVE"
        assert "sos_id" in data
    finally:
        app.dependency_overrides.clear()


def test_sos_api_cancel_endpoint():
    mock_db = MagicMock()
    mock_event = MagicMock()
    mock_event.id = "11111111-2222-3333-4444-555555555555"
    mock_event.status = "ACTIVE"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_event

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res = client.post("/api/v1/sos/11111111-2222-3333-4444-555555555555/cancel", json={
            "reason": "Pytest cancel test",
            "user_reference": "user_api_test"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "CANCELLED"
    finally:
        app.dependency_overrides.clear()


def test_emergency_contacts_api_endpoints():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        res_list = client.get("/api/v1/sos/contacts/list?user_reference=user_api_test")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["success"] is True
        assert "contacts" in data_list

        res_add = client.post("/api/v1/sos/contacts/add", json={
            "name": "Emergency Test Contact",
            "phone_number": "+91 99999 88888",
            "relationship": "Parent",
            "is_primary": True,
            "user_reference": "user_api_test"
        })
        assert res_add.status_code == 201
        data_add = res_add.json()
        assert data_add["success"] is True
        assert data_add["name"] == "Emergency Test Contact"
    finally:
        app.dependency_overrides.clear()
