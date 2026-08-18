from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.endpoints.data_sources import router as data_sources_router
from app.api.v1.endpoints.map import router as map_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.journey import router as journey_router
from app.api.v1.endpoints.ml import router as ml_router
from app.api.v1.endpoints.dynamic_risk import router as dynamic_risk_router
from app.api.v1.endpoints.fusion import router as fusion_router

api_v1_router = APIRouter()

# Include version 1 endpoint routers
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(data_sources_router, prefix="/data", tags=["Data Sources & Quality"])
api_v1_router.include_router(map_router, prefix="/map", tags=["Maps & Geographic Intelligence"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["LLM AI Intelligence Layer"])
api_v1_router.include_router(journey_router, prefix="/journey", tags=["Journey Safety Context"])
api_v1_router.include_router(ml_router, prefix="/ml", tags=["Phase 6 Historical ML Pipeline"])
api_v1_router.include_router(dynamic_risk_router, prefix="/risk", tags=["Phase 7 Dynamic Risk Engine"])
api_v1_router.include_router(fusion_router, prefix="/risk", tags=["Phase 8 AI + ML + LLM Fusion"])




