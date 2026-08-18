import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import get_db
from app.services.monitoring_service import MonitoringService

client = TestClient(app)


def test_monitoring_service_health_matrix():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [MagicMock()]
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    res = MonitoringService.get_health_matrix(mock_db)

    assert res["success"] is True
    assert "overall_status" in res
    assert "subsystems" in res
    assert len(res["subsystems"]) == 9
    assert res["subsystems"]["frontend"]["status"] == "HEALTHY"
    assert res["subsystems"]["backend"]["status"] == "HEALTHY"


def test_monitoring_service_performance_latency_stats():
    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

    res = MonitoringService.get_performance_latency_stats(mock_db)

    assert res["success"] is True
    assert "performance_metrics" in res
    metrics = res["performance_metrics"]
    assert "api" in metrics
    assert "p95_ms" in metrics["api"]
    assert "median_ms" in metrics["api"]
    assert "average_ms" in metrics["api"]


def test_monitoring_service_model_drift_check():
    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.first.return_value = None

    res = MonitoringService.check_model_drift(mock_db)

    assert res["success"] is True
    assert res["model_version"] == "1.0.0"
    assert res["drift_detected"] is False
    assert "feature_drift_score" in res


def test_route_feedback_submission_flow():
    mock_db = MagicMock()

    res = MonitoringService.record_route_feedback(
        db=mock_db,
        route_id="route_pytest_123",
        route_type="SAFEST",
        is_useful=True,
        comments="Pytest feedback comment",
        user_reference="user_pytest"
    )

    assert res["success"] is True
    assert res["route_id"] == "route_pytest_123"
    assert res["is_useful"] is True


def test_monitoring_api_endpoints():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Test GET /api/v1/monitoring/health-dashboard
        res_h = client.get("/api/v1/monitoring/health-dashboard")
        assert res_h.status_code == 200
        data_h = res_h.json()
        assert data_h["success"] is True
        assert "subsystems" in data_h

        # Test GET /api/v1/monitoring/metrics
        res_m = client.get("/api/v1/monitoring/metrics")
        assert res_m.status_code == 200
        data_m = res_m.json()
        assert data_m["success"] is True

        # Test GET /api/v1/monitoring/model-drift
        res_d = client.get("/api/v1/monitoring/model-drift")
        assert res_d.status_code == 200
        data_d = res_d.json()
        assert data_d["success"] is True

        # Test POST /api/v1/monitoring/feedback
        res_f = client.post("/api/v1/monitoring/feedback", json={
            "route_id": "route_api_test",
            "route_type": "SAFEST",
            "is_useful": True,
            "comments": "API route feedback test"
        })
        assert res_f.status_code == 201
        data_f = res_f.json()
        assert data_f["success"] is True

        # Test GET /api/v1/monitoring/backup-verify
        res_b = client.get("/api/v1/monitoring/backup-verify")
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["success"] is True
        assert data_b["backup_script_configured"] is True
    finally:
        app.dependency_overrides.clear()
