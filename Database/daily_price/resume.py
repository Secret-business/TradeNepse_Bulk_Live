import os
import glob
import json
from datetime import datetime, timedelta
from typing import Optional

class DailyPriceResumeSystem:
    """
    Manages the resume logic for the Daily Price downloader.
    Determines where to start downloading based on existing data files or configuration.
    """

    def __init__(self, data_dir: str = "data/daily_price", config_path: str = "config/daily_price_settings.json"):
        """
        Initializes the resume system with directories and config paths.
        
        Args:
            data_dir: Path to directory containing daily price files.
            config_path: Path to settings.json config file.
        """
        self.data_dir = os.path.abspath(data_dir)
        self.config_path = os.path.abspath(config_path)

    def get_latest_downloaded_date(self) -> Optional[str]:
        """
        Scans the data directory for YYYY-MM-DD.json files and returns the latest date.
        
        Returns:
            The latest business date as a string (YYYY-MM-DD), or None if no files are found.
        """
        if not os.path.exists(self.data_dir):
            return None

        # Search for files matching YYYY-MM-DD.json pattern
        search_pattern = os.path.join(self.data_dir, "????-??-??.json")
        matching_files = glob.glob(search_pattern)
        
        if not matching_files:
            return None

        dates = []
        for file_path in matching_files:
            filename = os.path.basename(file_path)
            date_str = filename.replace(".json", "")
            try:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_str)
            except ValueError:
                # Skip files that don't match the format
                continue

        if not dates:
            return None

        # Returns the max date string lexical sort works perfectly on YYYY-MM-DD
        return max(dates)

    def get_next_start_date(self) -> str:
        """
        Determines the date from which the synchronizer should begin fetching.
        
        If previous files exist, returns (latest date + 1 day).
        Otherwise, returns the start_date from settings.json.
        
        Returns:
            A date string formatted as YYYY-MM-DD.
        """
        latest_date = self.get_latest_downloaded_date()
        
        if latest_date:
            try:
                latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
                next_dt = latest_dt + timedelta(days=1)
                return next_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Fall back to settings.json start_date
        default_start_date = "2022-09-18"
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("start_date", default_start_date)
            except Exception:
                pass

        return default_start_date
