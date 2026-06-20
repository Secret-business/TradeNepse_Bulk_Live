import os
import json
from typing import Dict, Any, List, Optional


class FloorsheetStorage:
    """
    Handles storage operations for Floorsheet data.

    Layout:
        data/floorsheet/
            {YYYY-MM-DD}.json             # Consolidated daily trades
            {YYYY-MM-DD}/                 # Optional raw pages folder
                page_001.json
                page_002.json
    """

    def __init__(self, data_dir: str = "data/floorsheet"):
        """
        Initializes the storage manager with the target directory.

        Args:
            data_dir: Target directory path for storing floorsheet data.
        """
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    def load_daily_floorsheet(self, business_date: str) -> List[Dict[str, Any]]:
        """
        Loads consolidated daily floorsheet file.

        Args:
            business_date: Date string formatted as YYYY-MM-DD.

        Returns:
            A list of trade records. Returns empty list if file doesn't exist or is invalid.
        """
        file_path = os.path.join(self.data_dir, f"{business_date}.json")
        if not os.path.isfile(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def save_daily_floorsheet(self, business_date: str, records: List[Dict[str, Any]]) -> None:
        """
        Saves the normalized and consolidated trade list for a business date.
        Ensures sorting chronologically / by contract ID ascending.

        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            records: Consolidated list of normalized trade records.
        """
        file_path = os.path.join(self.data_dir, f"{business_date}.json")
        # Sort trades by contract_id ascending for chronological consistency
        sorted_records = sorted(
            records,
            key=lambda x: x.get("contract_id", 0)
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted_records, f, indent=4, ensure_ascii=False)

    def save_raw_page(self, business_date: str, page_number: int, raw_json: Any) -> None:
        """
        Saves the raw page JSON response to its date-specific directory.

        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            page_number: 1-indexed page number.
            raw_json: Raw API response dict.
        """
        date_dir = os.path.join(self.data_dir, business_date)
        os.makedirs(date_dir, exist_ok=True)
        file_path = os.path.join(date_dir, f"page_{page_number:03d}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, indent=4, ensure_ascii=False)
