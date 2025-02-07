import logging
import sys
from .config import settings

# Create logger
logger = logging.getLogger("pharmacy_ocr")
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

# Create formatter
formatter = logging.Formatter(settings.LOG_FORMAT)
console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)

def get_logger():
    return logger 