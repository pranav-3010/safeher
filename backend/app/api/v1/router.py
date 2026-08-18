from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.endpoints.data_sources import router as data_sources_router
from app.api.v1.endpoints.map import router as map_router

api_v1_router = APIRouter()

# Include version 1 endpoint routers
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(data_sources_router, prefix="/data", tags=["Data Sources & Quality"])
api_v1_router.include_router(map_router, prefix="/map", tags=["Maps & Geographic Intelligence"])
