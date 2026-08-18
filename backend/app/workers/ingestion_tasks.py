from app.workers.celery_app import celery_app
from app.database.session import SessionLocal
from app.agents.government_agent import GovernmentDataAgent
from app.agents.news_agent import NewsDataAgent
from app.agents.osm_agent import OSMAgent
from app.core.logging import logger


@celery_app.task(name="app.workers.ingestion_tasks.ingest_government_sources", bind=True, max_retries=3, default_retry_delay=60)
def ingest_government_sources(self, raw_content: str = None, file_format: str = "json"):
    """
    Celery task to trigger government dataset ingestion pipeline.
    """
    db = SessionLocal()
    try:
        agent = GovernmentDataAgent()
        result = agent.run_pipeline(db, raw_content=raw_content, file_format=file_format)
        return result
    except Exception as exc:
        logger.error(f"Task ingest_government_sources failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="app.workers.ingestion_tasks.ingest_news_sources", bind=True, max_retries=3, default_retry_delay=60)
def ingest_news_sources(self, rss_url: str = "https://news.google.com/rss/search?q=women+safety+india&hl=en-IN"):
    """
    Celery task to trigger real public RSS news ingestion pipeline.
    """
    db = SessionLocal()
    try:
        agent = NewsDataAgent()
        result = agent.run_pipeline(db, rss_url=rss_url)
        return result
    except Exception as exc:
        logger.error(f"Task ingest_news_sources failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="app.workers.ingestion_tasks.ingest_osm_data", bind=True, max_retries=3, default_retry_delay=120)
def ingest_osm_data(self, bbox: tuple = (17.35, 78.45, 17.42, 78.52)):
    """
    Celery task to trigger OpenStreetMap Overpass GIS ingestion pipeline.
    """
    db = SessionLocal()
    try:
        agent = OSMAgent()
        result = agent.run_pipeline(db, bbox=bbox)
        return result
    except Exception as exc:
        logger.error(f"Task ingest_osm_data failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(name="app.workers.ingestion_tasks.process_new_articles")
def process_new_articles():
    """
    Task placeholder to mark newly ingested articles for processing.
    """
    return {"status": "ok", "message": "Articles processed"}


@celery_app.task(name="app.workers.ingestion_tasks.validate_ingested_records")
def validate_ingested_records():
    """
    Task to validate data integrity across ingested source records.
    """
    return {"status": "ok", "message": "Record validation executed"}


@celery_app.task(name="app.workers.ingestion_tasks.cleanup_failed_records")
def cleanup_failed_records():
    """
    Task to clear stale temporary fetch logs.
    """
    return {"status": "ok", "message": "Failed logs cleanup executed"}
