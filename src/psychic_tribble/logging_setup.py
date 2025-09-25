"""Logging configuration for the application."""
import logging
import logging.config
import sys
from typing import Dict, Any


def configure_logging(settings) -> None:
    """Configure application logging."""
    
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed" if settings.DEBUG else "standard",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(config)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for environment: {settings.ENV}")
    logger.info(f"Log level set to: {log_level}")