import os
import sys
import json
import time
from typing import Dict, Any

# Ensure Database directory is in the import path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from company_master.downloader import CompanyMasterDownloader
from company_master.parser import CompanyMasterParser
from company_master.storage import CompanyMasterStorage
from company_master.resume import CompanyMasterResume
from company_master.logger import setup_company_master_logger

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "company_master_settings.json")
DAILY_PRICE_DATA_DIR = os.path.join(BASE_DIR, "data", "daily_price")
COMPANY_MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "company_master")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def load_config() -> Dict[str, Any]:
    """
    Loads Company Master settings from its dedicated config file.
    Returns defaults if the file is missing or corrupted.
    """
    default_config = {
        "enabled": True,
        "update_frequency": "weekly",
        "download_delay_seconds": 1,
        "max_workers": 5,
        "save_raw_json": True,
        "test_mode": True,
        "test_limit": 3
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
    Main entry point for the Company Master sync.
    """
    # Setup logger
    logger = setup_company_master_logger(log_dir=LOG_DIR, log_filename="company_master.log")

    logger.info("=========================================")
    logger.info("NEPSE Company Master Sync V1 Starting")
    logger.info("=========================================")

    # Load configuration
    config = load_config()

    if not config.get("enabled", True):
        logger.info("Company Master module is disabled in settings. Exiting.")
        return

    test_mode = config.get("test_mode", False)
    test_limit = int(config.get("test_limit", 3))
    delay = float(config.get("download_delay_seconds", 1))
    save_raw = config.get("save_raw_json", True)
    update_frequency = config.get("update_frequency", "weekly")

    logger.info(f"Update Frequency: {update_frequency}")
    logger.info(f"Download Delay: {delay} seconds")
    logger.info(f"Save Raw JSON: {save_raw}")
    logger.info(f"Test Mode: {'ENABLED (limit: ' + str(test_limit) + ')' if test_mode else 'DISABLED'}")

    # Initialize modules
    downloader = CompanyMasterDownloader(daily_price_data_dir=DAILY_PRICE_DATA_DIR)
    parser = CompanyMasterParser()
    storage = CompanyMasterStorage(data_dir=COMPANY_MASTER_DATA_DIR)
    resume = CompanyMasterResume(data_dir=COMPANY_MASTER_DATA_DIR)

    # Step 1: Extract all securityId values from Daily Price data
    logger.info("-----------------------------------------")
    logger.info("Step 1: Extracting securityId values from Daily Price data...")
    all_security_ids = downloader.extract_all_security_ids()

    if not all_security_ids:
        logger.warning("No securityId values found in Daily Price data. Ensure Daily Price sync has run first.")
        logger.info("Exiting Company Master sync.")
        return

    logger.info(f"Total unique securityId values found: {len(all_security_ids)}")

    # Apply test mode limit
    if test_mode:
        all_security_ids = all_security_ids[:test_limit]
        logger.info(f"TEST MODE: Limited to first {test_limit} companies: {all_security_ids}")

    # Step 2: Resume logic - find pending IDs
    pending_ids = resume.get_pending_security_ids(all_security_ids, force_update=False)
    already_downloaded = len(all_security_ids) - len(pending_ids)

    logger.info(f"Already downloaded: {already_downloaded}")
    logger.info(f"Pending download: {len(pending_ids)}")

    if not pending_ids:
        logger.info("All companies are already up to date. Nothing to download.")
        logger.info("=========================================")
        logger.info("NEPSE Company Master Sync V1 Completed")
        logger.info("=========================================")
        return

    logger.info("-----------------------------------------")
    logger.info("Step 2: Downloading company data from NEPSE API...")

    # Load existing master data for upsert
    master_data = storage.load_master()

    # Counters
    downloaded_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for i, security_id in enumerate(pending_ids, start=1):
        try:
            # Download raw data
            raw_response = downloader.download_security(security_id)

            # Optionally save raw JSON
            if save_raw:
                storage.save_raw_json(security_id, raw_response)

            # Parse into normalized record
            record = parser.parse_security_response(raw_response, security_id)

            if record:
                changed = storage.upsert_record(master_data, record)
                if changed:
                    updated_count += 1
                    status = "Updated"
                else:
                    skipped_count += 1
                    status = "Unchanged"

                symbol = record.get("symbol", "UNKNOWN")
                logger.info(
                    f"[{i}/{len(pending_ids)}] securityId: {security_id} | "
                    f"Symbol: {symbol} | Status: {status}"
                )
            else:
                skipped_count += 1
                logger.warning(
                    f"[{i}/{len(pending_ids)}] securityId: {security_id} | "
                    f"Status: Skipped (invalid/empty response)"
                )

            downloaded_count += 1

        except Exception as e:
            error_count += 1
            logger.error(
                f"[{i}/{len(pending_ids)}] securityId: {security_id} | "
                f"Status: ERROR | {str(e)}"
            )

        # Save master after each download (crash-safe)
        if downloaded_count % 10 == 0 or i == len(pending_ids):
            storage.save_master(master_data)

        # Apply delay between requests (except after the last one)
        if i < len(pending_ids):
            time.sleep(delay)

    # Final save
    storage.save_master(master_data)

    # Summary
    logger.info("-----------------------------------------")
    logger.info("Sync Summary:")
    logger.info(f"  Total Securities Processed: {downloaded_count}")
    logger.info(f"  New/Updated Records:        {updated_count}")
    logger.info(f"  Unchanged Records:          {skipped_count}")
    logger.info(f"  Errors:                     {error_count}")
    logger.info(f"  Total in Master File:       {len(master_data)}")
    logger.info("=========================================")
    logger.info("NEPSE Company Master Sync V1 Completed")
    logger.info("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCompany Master sync interrupted by user. Safe to close.")
        sys.exit(0)
