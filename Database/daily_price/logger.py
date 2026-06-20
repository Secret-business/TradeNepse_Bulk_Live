import os
import sys
import logging

def setup_logger(log_dir: str = "logs", log_filename: str = "daily_price.log") -> logging.Logger:
    """
    Configures and returns a Logger instance that writes to both a file and standard output.
    
    The logger outputs format capturing processing details, records, and errors.
    
    Args:
        log_dir: The directory where the log file will be saved.
        log_filename: The name of the log file.
        
    Returns:
        A configured logging.Logger instance.
    """
    # Ensure logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_filename)
    
    logger = logging.getLogger("daily_price_sync")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
