"""
Structured logging configuration for the application.
"""
import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup structured logging configuration."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }
    
    # Add file handler if log file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
        config["root"]["handlers"].append("file")
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(f"app.{name}")

class LogContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        # Store old context and set new context
        for key, value in self.context.items():
            if hasattr(self.logger, key):
                self.old_context[key] = getattr(self.logger, key)
            setattr(self.logger, key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for key in self.context.keys():
            if key in self.old_context:
                setattr(self.logger, key, self.old_context[key])
            else:
                delattr(self.logger, key)

def log_api_call(logger: logging.Logger, method: str, endpoint: str, 
                status_code: int, duration_ms: float, user_id: str = None):
    """Log API call with structured data."""
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'duration': duration_ms
    }
    if user_id:
        extra['user_id'] = user_id
    
    level = logging.INFO
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    
    logger.log(level, f"{method} {endpoint} - {status_code} ({duration_ms:.2f}ms)", extra=extra)

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with structured context."""
    extra = {
        'error_type': type(error).__name__
    }
    if context:
        extra.update(context)
    
    logger.error(f"Error occurred: {str(error)}", extra=extra, exc_info=True)