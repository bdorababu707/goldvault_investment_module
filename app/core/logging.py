import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

def setup_logging() -> None:
    """Configure application logging to be event-driven and non-verbose"""
    # Get log settings from config
    log_dir = Path("./logs/investment_management/")
    log_dir.mkdir(parents=True, exist_ok=True)
    rotation_size = settings.LOG.ROTATION_SIZE_MB * 1024 * 1024
    backup_count = settings.LOG.BACKUP_COUNT
    
    # Configure root logger - use INFO as minimum level
    root_logger = logging.getLogger()
    
    # In development, use INFO; in production, use WARNING as base level
    base_level = logging.INFO if settings.is_development() else logging.WARNING
    root_logger.setLevel(base_level)
    
    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Set up formatter - clean and minimal
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    
    # Add console handler - only for application logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(base_level)
    root_logger.addHandler(console_handler)
    
    # Add file handler for important logs only
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=rotation_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(base_level)
    root_logger.addHandler(file_handler)
    
    # Add separate error file handler
    error_file_handler = RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=rotation_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)
    
    # Silence watchfiles completely - this is causing the continuous logs
    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    
    # Silence only MongoDB logs (keep FastAPI/Uvicorn logs visible)
    for logger_name in [
        "pymongo", "pymongo.connection", "pymongo.command", 
        "pymongo.serverSelection", "pymongo.topology"
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Just log startup
    logging.info(f"Application initialized in {'development' if settings.is_development() else 'production'} mode")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific component that will only log important events"""
    return logging.getLogger(name)

