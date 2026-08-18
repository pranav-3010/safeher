from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.database.session import check_database_connection, check_postgis_version
from app.services.redis_service import check_redis_connection
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Infrastructure Health Check")
def get_system_health():
    """
    Upgraded health endpoint verifying:
    - FastAPI readiness
    - Supabase PostgreSQL database reachability
    - PostGIS version availability via SELECT PostGIS_Version()
    - Redis cache/broker reachability
    - Celery configuration status
    """
    db_ok = check_database_connection()
    postgis_version = check_postgis_version()
    postgis_ok = postgis_version is not None
    redis_ok = check_redis_connection()
    celery_configured = bool(settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND)

    is_healthy = db_ok and postgis_ok and redis_ok

    services_status = {
        "api": "ok",
        "database": "ok" if db_ok else "unreachable",
        "postgis": "ok" if postgis_ok else "unreachable",
        "redis": "ok" if redis_ok else "unreachable",
        "celery": "configured" if celery_configured else "not_configured"
    }

    response_payload = {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "services": services_status
    }

    if postgis_version:
        response_payload["postgis_version"] = postgis_version

    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=status_code, content=response_payload)
