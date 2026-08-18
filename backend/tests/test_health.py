from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.database.session import check_database_connection, check_postgis_version
from app.services.redis_service import check_redis_connection
from app.services.supabase_client import check_supabase_client_init, SupabaseService
from app.workers.celery_app import celery_app, health_check_task

client = TestClient(app)


def test_fastapi_app_starts_and_health_endpoint_healthy():
    with patch("app.api.v1.health.check_database_connection", return_value=True), \
         patch("app.api.v1.health.check_postgis_version", return_value="POSTGIS='3.4.0'"), \
         patch("app.api.v1.health.check_redis_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "women-safety-backend"
        assert data["services"]["api"] == "ok"
        assert data["services"]["database"] == "ok"
        assert data["services"]["postgis"] == "ok"
        assert data["services"]["redis"] == "ok"
        assert data["services"]["celery"] == "configured"
        assert data["postgis_version"] == "POSTGIS='3.4.0'"


def test_health_endpoint_degraded_when_database_unreachable():
    with patch("app.api.v1.health.check_database_connection", return_value=False), \
         patch("app.api.v1.health.check_postgis_version", return_value="POSTGIS='3.4.0'"), \
         patch("app.api.v1.health.check_redis_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] == "unreachable"


def test_health_endpoint_degraded_when_postgis_unreachable():
    with patch("app.api.v1.health.check_database_connection", return_value=True), \
         patch("app.api.v1.health.check_postgis_version", return_value=None), \
         patch("app.api.v1.health.check_redis_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["postgis"] == "unreachable"


def test_postgis_version_check_handles_exception():
    with patch("app.database.session.engine.connect", side_effect=Exception("PostGIS Error")):
        result = check_postgis_version()
        assert result is None


def test_database_connectivity_check_handles_exception():
    with patch("app.database.session.engine.connect", side_effect=Exception("DB Error")):
        result = check_database_connection()
        assert result is False


def test_redis_connectivity_check_handles_exception():
    with patch("app.services.redis_service.redis.Redis.from_url", side_effect=Exception("Redis Error")):
        result = check_redis_connection()
        assert result is False


def test_supabase_client_initialization():
    with patch("app.services.supabase_client.create_client", return_value=MagicMock()):
        assert check_supabase_client_init() is True


def test_celery_application_initializes():
    assert celery_app.main == "women_safety_workers"
    assert celery_app.conf.task_serializer == "json"


def test_celery_health_check_task_returns_ok():
    result = health_check_task()
    assert result == {"status": "ok"}
