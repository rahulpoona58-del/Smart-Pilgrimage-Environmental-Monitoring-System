# backend/app/core/logging_config.py
# Logging System: Configures robust console and file log outputs for audits.

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_system_logging(log_level: int = logging.INFO):
    """Establishes unified formatters and file logging rotation rules."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 1. Define standard glowing formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 2. Console stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 3. Rotating file handler (rotates every 5MB, keeps up to 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "spems_backend.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 4. Bootstrap root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Prune existing handlers to prevent duplicate logging
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Mute third-party noise (SQLAlchemy / Uvicorn verbosity controls)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    logging.info("SPEMS System Logging successfully initialized.")

# Run setup
setup_system_logging()
