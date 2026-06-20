import os
import sys
import json
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any

# Ensure Database directory is in the import path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from daily_price.downloader import DailyPriceDownloader
from daily_price.parser import DailyPriceParser
from daily_price.storage import DailyPriceStorageManager
from daily_price.resume import DailyPriceResumeSystem
from daily_price.logger import setup_logger

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "daily_price_settings.json")
DATA_DIR = os.path.join(BASE_DIR, "data", "daily_price")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def load_config() -> Dict[str, Any]:
    """
    Loads configuration settings from daily_price_settings.json.
    Returns defaults if the file is missing or corrupted.
    """
    default_config = {
        "enabled": True,
        "start_date": "2022-09-18",
        "request_delay_seconds": 1.5,
        "update_frequency": "daily"
    }

    if not os.path.exists(CONFIG_PATH):
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure keys exist
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return default_config


def main() -> None:
    """
    Main entry point for syncing daily stock prices.
    Determines start date, downloads day-by-day raw JSON files, and saves them.
    """
    # Setup logger
    logger = setup_logger(log_dir=LOG_DIR, log_filename="daily_price.log")

    logger.info("=========================================")
    logger.info("NEPSE Daily Price Sync V2 Platform Starting")
    logger.info("=========================================")

    # Load configuration
    config = load_config()

    if not config.get("enabled", True):
        logger.info("Daily Price module is disabled in settings. Exiting.")
        return

    start_date_str = config.get("start_date", "2022-09-18")
    delay = float(config.get("request_delay_seconds", 1.5))
    update_frequency = config.get("update_frequency", "daily")

    logger.info(f"Update Frequency: {update_frequency}")

    # Initialize V2 modules
    storage_manager = DailyPriceStorageManager(data_dir=DATA_DIR)
    downloader = DailyPriceDownloader()
    parser = DailyPriceParser()
    resume_system = DailyPriceResumeSystem(data_dir=DATA_DIR, config_path=CONFIG_PATH)

    # Determine the starting date
    start_date_str = resume_system.get_next_start_date()
    try:
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError as e:
        logger.error(f"Invalid start date format '{start_date_str}': {e}. Falling back to 2022-09-18.")
        start_date_obj = datetime.strptime("2022-09-18", "%Y-%m-%d").date()

    end_date_obj = date.today()

    logger.info(f"Sync Range: {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}")
    logger.info(f"Politeness Delay: {delay} seconds")

    if start_date_obj > end_date_obj:
        logger.info("Daily Price V2 is already fully synchronized up to today. Exiting.")
        return

    current_date_obj = start_date_obj

    while current_date_obj <= end_date_obj:
        date_str = current_date_obj.strftime("%Y-%m-%d")

        # Safe resume check: Skip if file already exists on disk
        if storage_manager.exists(date_str):
            logger.info(f"Date Processed: {date_str} | Records Downloaded: 0 (Already Exists) | Errors: None")
            current_date_obj += timedelta(days=1)
            continue

        try:
            # 1. Download
            response_data = downloader.download_date(date_str)

            # 2. Parse & Validate
            records = parser.parse_and_validate(response_data)
            records_count = len(records)

            # 3. Store raw JSON only if it contains active trading data
            if records_count > 0:
                storage_manager.save_raw_json(date_str, response_data)

            error_status = "None"
            if records_count == 0:
                error_status = "None (Skipped - No trading data)"

            logger.info(
                f"Date Processed: {date_str} | "
                f"Records Downloaded: {records_count} | "
                f"Errors: {error_status}"
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Date Processed: {date_str} | "
                f"Records Downloaded: 0 | "
                f"Errors: {error_msg}"
            )
            logger.error("Sync loop interrupted due to error. Next run will resume from this date.")
            sys.exit(1)

        # Move to next calendar day
        current_date_obj += timedelta(days=1)

        # Apply delay to respect server request rates
        if current_date_obj <= end_date_obj:
            time.sleep(delay)

    logger.info("=========================================")
    logger.info("NEPSE Daily Price Sync V2 Completed Successfully")
    logger.info("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSync interrupted by user. Safe to close.")
        sys.exit(0)
