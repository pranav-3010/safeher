from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    BaseCustomException,
    custom_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.api.v1.router import api_v1_router


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")


def create_application() -> FastAPI:
    """
    Application factory for the Women Safety Risk-Zone Backend.
    Sets up FastAPI instance, middleware, CORS, routers, and exception handlers.
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

    return app



app = create_application()
