"""Logging setup for Oura MCP Server."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .config import LoggingConfig


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(config: LoggingConfig) -> None:
    """
    Configure logging based on config.
    
    Args:
        config: Logging configuration
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create handler based on output type
    if config.output == "file":
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path)
    elif config.output == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if config.format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
