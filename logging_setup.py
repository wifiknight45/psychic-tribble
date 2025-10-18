"""
Enhanced logging configuration for Psychic Tribble API.

Provides structured logging with:
- JSON formatting for production
- Colored console output for development
- Request correlation via request IDs
- File rotation
- Different log levels per environment
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import json_log_formatter
    JSON_FORMATTER_AVAILABLE = True
except ImportError:
    JSON_FORMATTER_AVAILABLE = False


class RequestIDFilter(logging.Filter):
    """Add request ID to log records if available."""
    
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        return True


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', 'N/A'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'request_id']:
                log_data[key] = value
        
        return json_log_formatter.dumps(log_data) if JSON_FORMATTER_AVAILABLE else str(log_data)


def configure_logging(settings):
    """
    Configure application logging based on environment settings.
    
    Args:
        settings: Application settings object with logging configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Choose formatter based on environment
    if settings.ENV == "production":
        formatter_class = 'psychic_tribble.core.logging_setup.JSONFormatter'
        console_format = '%(message)s'
    else:
        formatter_class = 'psychic_tribble.core.logging_setup.ColoredFormatter'
        console_format = (
            '%(asctime)s | %(levelname)-8s | [%(request_id)s] | '
            '%(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
    
    # Logging configuration dictionary
    config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'request_id': {
                '()': 'psychic_tribble.core.logging_setup.RequestIDFilter'
            }
        },
        'formatters': {
            'default': {
                '()': formatter_class,
                'format': console_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s | %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'default',
                'filters': ['request_id'],
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'default',
                'filters': ['request_id'],
                'filename': log_dir / 'psychic_tribble.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'default',
                'filters': ['request_id'],
                'filename': log_dir / 'errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'psychic_tribble': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING' if settings.ENV == 'production' else 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file']
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured for environment: {settings.ENV}",
        extra={'environment': settings.ENV, 'log_level': settings.LOG_LEVEL}
    )
    
    return logger
