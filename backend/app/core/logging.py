import logging
import sys
from app.core.config import settings


def setup_logging():
    """
    Configures centralized structured logging for the FastAPI backend application.
    Output format includes timestamp, log level, module name, and message.
    """
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info(f"Logging initialized at level: {settings.LOG_LEVEL}")
    return logger


logger = setup_logging()
