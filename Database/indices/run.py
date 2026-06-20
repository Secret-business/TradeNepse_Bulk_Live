import os
import sys
import json
import time
from typing import Dict, Any, List

# Ensure Database directory is in the import path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from indices.downloader import IndicesDownloader
from indices.parser import IndicesParser
from indices.storage import IndicesStorage
from indices.resume import IndicesResume
from indices.logger import setup_indices_logger

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "indices_settings.json")
INDICES_DATA_DIR = os.path.join(BASE_DIR, "data", "indices")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def load_config() -> Dict[str, Any]:
    """
    Loads Indices settings from config/indices_settings.json.
    Returns defaults if the file is missing or corrupted.
    """
    default_config = {
        "enabled": True,
        "test_mode": True,
        "test_limit": 3,
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


def main() -> None:
    """
    Main orchestrator for the NEPSE Indices Module V1.
    """
    # Setup logger
    logger = setup_indices_logger(log_dir=LOG_DIR, log_filename="indices.log")

    logger.info("=========================================")
    logger.info("NEPSE Indices Sync V1 Starting")
    logger.info("=========================================")

    # Load configuration
    config = load_config()

    if not config.get("enabled", True):
        logger.info("Indices module is disabled in settings. Exiting.")
        return

    test_mode = config.get("test_mode", True)
    test_limit = int(config.get("test_limit", 3))
    save_raw = config.get("save_raw_json", True)
    update_frequency = config.get("update_frequency", "daily")
    request_delay = 1.0

    logger.info(f"Update Frequency: {update_frequency}")
    logger.info(f"Save Raw JSON: {save_raw}")
    logger.info(f"Test Mode: {'ENABLED (limit: ' + str(test_limit) + ')' if test_mode else 'DISABLED'}")

    # Initialize modules
    downloader = IndicesDownloader()
    parser = IndicesParser()
    storage = IndicesStorage(data_dir=INDICES_DATA_DIR)
    resume = IndicesResume(storage=storage)

    # Step 1: Refresh credentials (capture authorization token)
    logger.info("-----------------------------------------")
    logger.info("Step 1: Harvesting dynamic authorization header...")
    if not downloader.refresh_credentials():
        logger.error("Failed to capture credentials from NEPSE homepage. Exiting.")
        return
    logger.info("Authentication token captured successfully.")

    # Step 2: Fetch and save index master list
    logger.info("-----------------------------------------")
    logger.info("Step 2: Fetching active index listing...")
    master_map: Dict[str, str] = {}
    try:
        raw_master = downloader.download_indices_list()
        if save_raw:
            storage.save_raw_master(raw_master)

        master_map = parser.parse_master_response(raw_master)
        if master_map:
            storage.save_master(master_map)
            logger.info(f"Saved {len(master_map)} active indices to master list.")
        else:
            logger.warning("Parsed empty master indices mapping. Attempting to fall back.")
    except Exception as e:
        logger.error(f"Error fetching active indices: {e}")

    # Fallback to local master file if active fetch failed
    if not master_map:
        master_map = storage.load_master()
        if master_map:
            logger.info(f"Loaded {len(master_map)} indices from existing indices_master.json")
        else:
            # Absolute hardcoded backup of known index mappings from research
            master_map = {
                "51": "Banking SubIndex",
                "58": "NEPSE Index",
                "64": "Microfinance Index"
            }
            storage.save_master(master_map)
            logger.info(f"Created fallback master list with {len(master_map)} known indices.")

    # Identify which index IDs to process
    index_ids = sorted([int(k) for k in master_map.keys()])
    logger.info(f"Total active index IDs available: {index_ids}")

    # Apply test mode filtering
    if test_mode:
        test_ids = [51, 58, 64]
        index_ids = [idx for idx in index_ids if idx in test_ids]
        if not index_ids:
            index_ids = sorted([int(k) for k in list(master_map.keys())[:test_limit]])
        logger.info(f"TEST MODE: Restricting execution to target indices: {index_ids}")

    # Step 3: Crawl index history page-by-page with resume logic
    logger.info("-----------------------------------------")
    logger.info("Step 3: Downloading index history...")

    for i, index_id in enumerate(index_ids, start=1):
        index_name = master_map.get(str(index_id), f"Index {index_id}")
        logger.info(f"[{i}/{len(index_ids)}] Processing Index ID: {index_id} ({index_name})")

        # Load existing stored data and dates
        existing_history = storage.load_history(index_id)
        stored_dates = resume.get_stored_dates(index_id)
        logger.info(f"  Pre-existing dates stored: {len(stored_dates)}")

        new_parsed_records: List[Dict[str, Any]] = []
        new_raw_contents: List[Dict[str, Any]] = []
        page = 0
        stop_crawler = False

        while not stop_crawler:
            try:
                logger.info(f"  Downloading page {page} of history...")
                raw_page = downloader.download_index_history_page(index_id, page=page, size=100)

                if not raw_page or not isinstance(raw_page, dict):
                    logger.warning(f"  Received invalid response on page {page}.")
                    break

                page_content = raw_page.get("content", [])
                if not page_content:
                    logger.info(f"  No more records found on page {page}.")
                    break

                # Parse the page
                parsed_records = parser.parse_history_response(raw_page, index_name)
                
                # Check for overlap with already stored dates
                page_has_overlap = False
                non_overlapping_records = []

                for record in parsed_records:
                    rec_date = record.get("business_date")
                    if rec_date in stored_dates:
                        page_has_overlap = True
                        logger.info(f"    Resume system hit pre-existing date: {rec_date}. Stopping crawler.")
                        break
                    else:
                        non_overlapping_records.append(record)

                new_parsed_records.extend(non_overlapping_records)
                
                if save_raw:
                    new_raw_contents.extend(page_content)

                if page_has_overlap:
                    stop_crawler = True
                    break

                if raw_page.get("last", True):
                    logger.info("  Reached the last page of historical records.")
                    break

                page += 1
                time.sleep(request_delay)

            except Exception as e:
                logger.error(f"  Error downloading page {page} for Index ID {index_id}: {e}")
                break

        # Consolidate and save if we fetched new records
        if new_parsed_records:
            consolidated_dict = {r["business_date"]: r for r in existing_history}
            for r in new_parsed_records:
                consolidated_dict[r["business_date"]] = r
            
            consolidated_list = list(consolidated_dict.values())
            storage.save_history(index_id, consolidated_list)

            if save_raw:
                existing_raw = []
                raw_file_path = os.path.join(storage.raw_dir, f"{index_id}.json")
                if os.path.isfile(raw_file_path):
                    try:
                        with open(raw_file_path, "r", encoding="utf-8") as rf:
                            existing_raw = json.load(rf)
                            if not isinstance(existing_raw, list):
                                existing_raw = []
                    except Exception:
                        pass
                
                raw_dict = {item.get("businessDate"): item for item in existing_raw if item.get("businessDate")}
                for item in new_raw_contents:
                    date_val = item.get("businessDate")
                    if date_val:
                        raw_dict[date_val] = item
                
                storage.save_raw_history(index_id, list(raw_dict.values()))

            logger.info(f"  SUCCESS: Added {len(new_parsed_records)} new records. Total stored: {len(consolidated_list)}.")
        else:
            logger.info(f"  NO CHANGE: Index ID {index_id} is already up-to-date.")

        if i < len(index_ids):
            time.sleep(request_delay)

    logger.info("=========================================")
    logger.info("NEPSE Indices Sync V1 Completed")
    logger.info("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nIndices sync interrupted by user. Safe to close.")
        sys.exit(0)
