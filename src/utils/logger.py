import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pythonjsonlogger.jsonlogger as jsonlogger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName

def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File Handler with rotation
    file_handler = RotatingFileHandler(
        os.getenv('LOG_FILE_PATH', 'logs/app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Format handlers based on LOG_FORMAT env variable
    if os.getenv('LOG_FORMAT', 'json').lower() == 'json':
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(module)s %(function)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Create a default logger instance
logger = setup_logger()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name (str): Name for the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return setup_logger(name)

# Example usage:
# from utils.logger import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message")
# logger.error("This is an error message", extra={"context": "additional info"}) 