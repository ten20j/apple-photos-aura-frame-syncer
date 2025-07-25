import logging
import sys

# Configure logging format
LOGGING_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name, level=logging.INFO):
    """
    Set up a logger with consistent formatting and handlers.
    
    Args:
        name (str): The name of the logger (usually __name__ from the calling module)
        level (int): The logging level (default: logging.INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handlers if the logger doesn't have any
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT, DATE_FORMAT))
        
        logger.addHandler(console_handler)
        logger.setLevel(level)
        
        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False
    
    return logger 