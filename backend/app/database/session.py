from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
from app.core.config import settings
from app.core.logging import logger

# SQLAlchemy 2.x Engine connected to Supabase PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG
)

# Session Factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session.
    Ensures connection closing after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Verifies PostgreSQL database reachability in Supabase.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Supabase PostgreSQL database connection check failed: {e}")
        return False


def check_postgis_version() -> Optional[str]:
    """
    Executes SELECT PostGIS_Version() to verify PostGIS geospatial functionality in Supabase.
    Returns the version string if available, or None if failed.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT PostGIS_Version();"))
            row = result.fetchone()
            if row:
                version_str = str(row[0])
                logger.info(f"PostGIS Version detected: {version_str}")
                return version_str
        return None
    except Exception as e:
        logger.warning(f"PostGIS version check failed: {e}")
        return None
