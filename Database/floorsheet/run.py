import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set

# Ensure Database directory is in the import path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from floorsheet.downloader import FloorsheetDownloader
from floorsheet.parser import FloorsheetParser
from floorsheet.storage import FloorsheetStorage
from floorsheet.resume import FloorsheetResume
from floorsheet.logger import setup_floorsheet_logger

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "floorsheet_settings.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def load_config() -> Dict[str, Any]:
    """
    Loads Floorsheet settings from config/floorsheet_settings.json.
    Returns defaults if the file is missing or corrupted.
    """
    default_config = {
        "start_date": "2026-06-19",
        "enabled": True,
        "test_mode": True,
        "test_days": 1,
        "page_size": 100,
        "save_raw_json": True,
        "update_frequency": "daily"
    }

    if not os.path.exists(CONFIG_PATH):
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure all keys exist with defaults
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return default_config


def get_date_range(start_date_str: str, end_date: datetime) -> List[str]:
    """
    Generates a list of date strings (YYYY-MM-DD) from start_date_str to end_date inclusive.
    """
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    date_list = []
    curr = start_dt
    while curr <= end_date:
        date_list.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return date_list


def main() -> None:
    """
    Main orchestrator for the Floorsheet Sync Module V1.
    """
    # Setup logger
    logger = setup_floorsheet_logger(log_dir=LOG_DIR, log_filename="floorsheet.log")

    logger.info("=========================================")
    logger.info("NEPSE Floorsheet Sync V1 Starting")
    logger.info("=========================================")

    # Load configuration
    config = load_config()

    if not config.get("enabled", True):
        logger.info("Floorsheet module is disabled in settings. Exiting.")
        return

    test_mode = config.get("test_mode", True)
    test_days = int(config.get("test_days", 1))
    page_size = int(config.get("page_size", 100))
    save_raw = config.get("save_raw_json", True)
    default_start_date = config.get("start_date", "2026-06-19")
    update_frequency = config.get("update_frequency", "daily")
    request_delay = 1.0

    logger.info(f"Update Frequency: {update_frequency}")
    logger.info(f"Save Raw JSON: {save_raw}")
    logger.info(f"Page Size: {page_size}")
    logger.info(f"Test Mode: {'ENABLED (days: ' + str(test_days) + ')' if test_mode else 'DISABLED'}")

    # Initialize modules
    downloader = FloorsheetDownloader()
    parser = FloorsheetParser()
    storage = FloorsheetStorage()
    resume = FloorsheetResume()

    # Determine date range to process
    today_dt = datetime.now()
    target_dates: List[str] = []

    if test_mode:
        logger.info("TEST MODE: Searching backwards for the most recent active trading day...")
        found_date = None
        check_dt = today_dt

        for _ in range(10):
            check_date_str = check_dt.strftime("%Y-%m-%d")
            try:
                raw_page = downloader.download_floorsheet_page(check_date_str, page=1, size=10)
                total_trades = parser.get_total_trades(raw_page)
                if total_trades > 0:
                    found_date = check_date_str
                    logger.info(f"TEST MODE: Found active trading day: {found_date} ({total_trades} trades).")
                    break
            except Exception:
                pass
            check_dt -= timedelta(days=1)

        if not found_date:
            logger.error("TEST MODE: Could not identify any recent active trading day. Exiting.")
            return

        if os.path.isfile(os.path.join(storage.data_dir, f"{found_date}.json")):
            logger.info(f"TEST MODE: Most recent trading day {found_date} is already completed. Skipping download.")
            logger.info("=========================================")
            logger.info("NEPSE Floorsheet Sync V1 Completed")
            logger.info("=========================================")
            return

        target_dates = [found_date]
    else:
        start_date_str = resume.get_next_start_date(default_start_date)
        logger.info(f"Resuming sync starting from: {start_date_str}")
        target_dates = get_date_range(start_date_str, today_dt)

    logger.info(f"Target calendar dates to check: {target_dates}")
    logger.info("-----------------------------------------")

    for date_str in target_dates:
        if os.path.isfile(os.path.join(storage.data_dir, f"{date_str}.json")):
            logger.info(f"Date {date_str} already processed. Skipping.")
            continue

        logger.info(f"Processing Date: {date_str}...")
        
        all_parsed_trades: List[Dict[str, Any]] = []
        page = 1
        total_pages = 1
        pages_downloaded = 0
        error_occurred = None

        try:
            raw_page = downloader.download_floorsheet_page(date_str, page=page, size=page_size)
            if save_raw:
                storage.save_raw_page(date_str, page, raw_page)

            total_pages = parser.get_total_pages(raw_page)
            total_trades = parser.get_total_trades(raw_page)

            parsed_page = parser.parse_floorsheet_page(raw_page)
            all_parsed_trades.extend(parsed_page)
            pages_downloaded += 1

            logger.info(f"  Page 1: parsed {len(parsed_page)} trades. Total pages: {total_pages}. Total trades: {total_trades}.")

            if test_mode:
                logger.info("  TEST MODE: Restricting download to page 1 only.")
                total_pages = 1

            if total_pages > 1:
                page = 2
                while page <= total_pages:
                    time.sleep(request_delay)
                    logger.info(f"  Downloading page {page}/{total_pages}...")
                    raw_page = downloader.download_floorsheet_page(date_str, page=page, size=page_size)
                    if save_raw:
                        storage.save_raw_page(date_str, page, raw_page)

                    parsed_page = parser.parse_floorsheet_page(raw_page)
                    all_parsed_trades.extend(parsed_page)
                    pages_downloaded += 1

                    if not parsed_page:
                        break

                    page += 1

        except Exception as e:
            error_occurred = str(e)
            logger.error(f"  Failed downloading floorsheet for date {date_str}: {e}")

        if error_occurred:
            logger.info(f"Date: {date_str} | Pages Downloaded: {pages_downloaded} | Trades Downloaded: 0 | Errors: {error_occurred}")
            continue

        unique_trades_map = {}
        for trade in all_parsed_trades:
            contract_id = trade.get("contract_id")
            if contract_id:
                unique_trades_map[contract_id] = trade

        deduplicated_trades = list(unique_trades_map.values())
        duplicate_count = len(all_parsed_trades) - len(deduplicated_trades)

        if duplicate_count > 0:
            logger.info(f"  Deduplicated {duplicate_count} trades.")

        storage.save_daily_floorsheet(date_str, deduplicated_trades)
        
        status_msg = "No trading data" if len(deduplicated_trades) == 0 else "Success"
        logger.info(
            f"Date: {date_str} | "
            f"Pages Downloaded: {pages_downloaded} | "
            f"Trades Downloaded: {len(deduplicated_trades)} ({status_msg}) | "
            f"Errors: None"
        )

        if date_str != target_dates[-1]:
            time.sleep(request_delay)

    logger.info("=========================================")
    logger.info("NEPSE Floorsheet Sync V1 Completed")
    logger.info("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nFloorsheet sync interrupted by user. Safe to close.")
        sys.exit(0)
