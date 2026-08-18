import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    BaseCustomException,
    custom_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.api.v1.router import api_v1_router


from app.database.session import engine
from app.models.base_model import Base
import app.models  # Ensure all SQLAlchemy models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode.")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified and initialized.")
    except Exception as e:
        logger.warning(f"Database table initialization warning: {e}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")



def create_application() -> FastAPI:
    """
    Application factory for the Women Safety Risk-Zone Backend.
    Sets up FastAPI instance, middleware, CORS, routers, static files, and exception handlers.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Women Safety Risk-Zone Prediction System - Backend API Foundation",
        version="1.0.0",
        docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    app.add_exception_handler(BaseCustomException, custom_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include Versioned API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # Mount Static Files for Interactive Leaflet Frontend Map
    static_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../static"))
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/health", summary="Health Check")
    @app.get(f"{settings.API_V1_PREFIX}/health", summary="Health Check V1")
    def health_check():
        return {
            "status": "ok",
            "service": "safeher-backend",
            "environment": settings.APP_ENV,
            "database": "ok"
        }

    return app


app = create_application()
