import os
import glob
from datetime import datetime, timedelta
from typing import Optional


class FloorsheetResume:
    """
    Manages resumption logic for Floorsheet data sync.
    Scans the data directory for existing consolidated YYYY-MM-DD.json files.
    """

    def __init__(self, data_dir: str = "data/floorsheet"):
        """
        Initializes the resume scanner.

        Args:
            data_dir: Path to directory containing floorsheet data.
        """
        self.data_dir = os.path.abspath(data_dir)

    def get_latest_completed_date(self) -> Optional[str]:
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
                # Validate date format YYYY-MM-DD
                datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_str)
            except ValueError:
                # Skip non-matching filenames
                continue

        if not dates:
            return None

        # Lexical maximum works perfectly on YYYY-MM-DD
        return max(dates)

    def get_next_start_date(self, default_start_date: str) -> str:
        """
        Determines the date from which the floorsheet synchronization should start.

        If a completed date exists, returns (latest_date + 1 day).
        Otherwise, returns default_start_date.

        Args:
            default_start_date: Configured default start date as YYYY-MM-DD string.

        Returns:
            Start date string formatted as YYYY-MM-DD.
        """
        latest_date = self.get_latest_completed_date()

        if latest_date:
            try:
                latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
                next_dt = latest_dt + timedelta(days=1)
                return next_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return default_start_date
