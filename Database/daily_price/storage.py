import os
import json
from typing import Dict, Any

class DailyPriceStorageManager:
    """
    Handles the file storage operations for raw Daily Price JSON data.
    """

    def __init__(self, data_dir: str = "data/daily_price"):
        """
        Initializes the storage manager with the target directory.
        
        Args:
            data_dir: Target directory path for storing JSON files.
        """
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    def get_file_path(self, business_date: str) -> str:
        """
        Returns the absolute file path for a given business date.
        
        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            
        Returns:
            The absolute file path string.
        """
        return os.path.join(self.data_dir, f"{business_date}.json")

    def exists(self, business_date: str) -> bool:
        """
        Checks if a JSON file for the given business date already exists.
        
        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            
        Returns:
            True if the file exists, False otherwise.
        """
        return os.path.isfile(self.get_file_path(business_date))

    def save_raw_json(self, business_date: str, data: Dict[str, Any]) -> None:
        """
        Saves raw JSON dictionary to the file corresponding to the business date.
        
        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            data: Raw dictionary data to save.
        """
        file_path = self.get_file_path(business_date)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
