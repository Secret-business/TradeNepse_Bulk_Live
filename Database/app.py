import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

# Ensure that the Database directory is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from daily_price import NepseDownloader, DailyPriceStorage, parse_today_price_response

# Define paths relative to this script's directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "daily_price.db")

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, "daily_price.log")

# Setup standard formatting for log file to capture requested fields:
# Date Processed, Records Downloaded, Records Saved, Errors
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DailyPriceSync")


def load_config() -> Dict[str, Any]:
    """Loads configuration settings from settings.json, creates default if missing."""
    default_config = {
        "start_date": "2022-09-18",
        "database_path": "daily_price.db",
        "request_delay_seconds": 1.5
    }
    
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"Created default settings.json at {CONFIG_PATH}")
            return default_config
        except Exception as e:
            logger.error(f"Failed to write default settings.json: {e}")
            return default_config
            
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Merge with default keys
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        logger.error(f"Error loading settings.json, using defaults. Error: {e}")
        return default_config


def main():
    """Main synchronization loop to pull and save daily price records."""
    logger.info("=========================================")
    logger.info("NEPSE Daily Price Data Synchronizer V1 Starting")
    logger.info("=========================================")
    
    config = load_config()
    
    # Resolve database path relative to Database/ folder if it's a relative path
    db_setting = config.get("database_path", "daily_price.db")
    if not os.path.isabs(db_setting):
        db_path = os.path.abspath(os.path.join(BASE_DIR, db_setting))
    else:
        db_path = db_setting
        
    start_date_str = config.get("start_date", "2022-09-18")
    delay = float(config.get("request_delay_seconds", 1.5))
    
    logger.info(f"Database Path: {db_path}")
    logger.info(f"Default Config Start Date: {start_date_str}")
    logger.info(f"Politeness Delay: {delay} seconds")
    
    # Initialize components
    storage = DailyPriceStorage(db_path)
    downloader = NepseDownloader()
    
    # Determine the starting date
    latest_stored_date = storage.get_latest_business_date()
    
    if latest_stored_date:
        try:
            # Resume from the day after the latest stored date
            last_date_obj = datetime.strptime(latest_stored_date, "%Y-%m-%d").date()
            start_date_obj = last_date_obj + timedelta(days=1)
            logger.info(f"Resume: Last saved business date found in DB is {latest_stored_date}.")
            logger.info(f"Sync will resume from the next calendar day: {start_date_obj.strftime('%Y-%m-%d')}")
        except ValueError as e:
            logger.error(f"Failed to parse latest business date '{latest_stored_date}' from DB: {e}")
            logger.info(f"Sync will fall back to config start date: {start_date_str}")
            start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        logger.info(f"Clean Run: No existing data in database.")
        logger.info(f"Sync will start from configured start date: {start_date_str}")
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        
    end_date_obj = date.today()
    logger.info(f"Sync range: {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}")
    
    if start_date_obj > end_date_obj:
        logger.info("Database is already fully synchronized up to today. Exiting.")
        return

    current_date_obj = start_date_obj
    
    while current_date_obj <= end_date_obj:
        date_str = current_date_obj.strftime("%Y-%m-%d")
        
        try:
            # 1. Download data
            response_data = downloader.fetch_today_price(date_str)
            
            # 2. Parse data
            records = parse_today_price_response(response_data)
            
            # 3. Store data
            records_downloaded = len(records)
            records_saved = 0
            
            if records_downloaded > 0:
                records_saved = storage.save_records(records)
                error_str = "None"
            else:
                # No data returned (weekend, holiday, etc.)
                error_str = "None (Skipped - No trading data)"
                
            # Log exact fields: Date Processed, Records Downloaded, Records Saved, Errors
            logger.info(
                f"Date Processed: {date_str} | "
                f"Records Downloaded: {records_downloaded} | "
                f"Records Saved: {records_saved} | "
                f"Errors: {error_str}"
            )
            
        except Exception as e:
            # Log details on error
            error_msg = str(e)
            logger.error(
                f"Date Processed: {date_str} | "
                f"Records Downloaded: 0 | "
                f"Records Saved: 0 | "
                f"Errors: {error_msg}"
            )
            logger.error("Sync loop interrupted due to request/processing error. Resuming next run will restart from this date.")
            sys.exit(1)
            
        # Move to next calendar day
        current_date_obj += timedelta(days=1)
        
        # Politeness delay to avoid overloading NEPSE servers
        if current_date_obj <= end_date_obj:
            time.sleep(delay)
            
    logger.info("=========================================")
    logger.info("NEPSE Daily Price Data Synchronizer V1 Sync Completed Successfully")
    logger.info("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nSynchronization interrupted by user. Safe to close; progress has been saved.")
        sys.exit(0)
