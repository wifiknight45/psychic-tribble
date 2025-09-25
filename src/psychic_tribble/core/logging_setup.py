"""Enhanced logging configuration with structured logging."""
import logging
import logging.config
import sys
from typing import Dict, Any, Optional
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info",
                "exc_text", "stack_info", "message"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


def configure_logging(settings) -> None:
    """Configure enhanced application logging with structured output."""
    
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    
    # Enhanced logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": (
                    "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d "
                    "[%(request_id)s] %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "structured": {
                "()": StructuredFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured" if settings.ENV == "production" else "detailed",
                "stream": sys.stdout,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "structured",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            } if settings.ENV == "production" else None,
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"] + (["error_file"] if settings.ENV == "production" else []),
                "level": log_level,
                "propagate": False,
            },
            "psychic_tribble": {
                "handlers": ["console"] + (["error_file"] if settings.ENV == "production" else []),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING" if not settings.DEBUG else "INFO",
                "propagate": False,
            },
            "slowapi": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # Remove None handlers
    config["handlers"] = {k: v for k, v in config["handlers"].items() if v is not None}
    
    # Create logs directory if in production
    if settings.ENV == "production":
        import os
        os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(config)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(
        f"Enhanced logging configured for environment: {settings.ENV}",
        extra={"environment": settings.ENV, "log_level": log_level}
    )
    logger.info(
        f"Log level set to: {log_level}",
        extra={"log_level": log_level}
    )