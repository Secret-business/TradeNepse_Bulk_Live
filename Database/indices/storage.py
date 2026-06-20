import os
import json
from typing import Dict, Any, List, Optional


class IndicesStorage:
    """
    Handles file storage operations for the Indices module.

    Storage layout:
        data/indices/
            indices_master.json         # Normalized master index mappings (IDs to Names)
            {index_id}.json             # Consolidated historical data per index
            raw/                        # Optional raw API response backups
                indices_master.json     # Raw response of GET /api/nots/index
                {index_id}.json         # Consolidated raw history response pages
    """

    def __init__(self, data_dir: str = "data/indices"):
        """
        Initializes the storage manager with the target directories.

        Args:
            data_dir: Target directory path for storing indices data.
        """
        self.data_dir = os.path.abspath(data_dir)
        self.raw_dir = os.path.join(self.data_dir, "raw")
        self.master_file = os.path.join(self.data_dir, "indices_master.json")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    def load_master(self) -> Dict[str, Any]:
        """
        Loads the normalized index master file.

        Returns:
            A dictionary mapping index_id (as string) to index details/name.
            Returns an empty dict if the file does not exist or is corrupted.
        """
        if not os.path.isfile(self.master_file):
            return {}

        try:
            with open(self.master_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except (json.JSONDecodeError, OSError):
            return {}

    def save_master(self, master_data: Dict[str, Any]) -> None:
        """
        Saves the normalized index master dictionary to indices_master.json.

        Args:
            master_data: Dictionary mapping index_id (string) to index details.
        """
        with open(self.master_file, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)

    def load_history(self, index_id: int) -> List[Dict[str, Any]]:
        """
        Loads the normalized historical records for a specific index.

        Args:
            index_id: The numeric ID of the index.

        Returns:
            A list of historical records sorted by date.
        """
        file_path = os.path.join(self.data_dir, f"{index_id}.json")
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

    def save_history(self, index_id: int, history_records: List[Dict[str, Any]]) -> None:
        """
        Saves the normalized historical records list for a specific index.

        Args:
            index_id: The numeric ID of the index.
            history_records: List of normalized historical records.
        """
        file_path = os.path.join(self.data_dir, f"{index_id}.json")
        # Ensure sorting by date ascending for chronological consistency
        sorted_records = sorted(
            history_records,
            key=lambda x: x.get("business_date", "")
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted_records, f, indent=4, ensure_ascii=False)

    def save_raw_master(self, raw_data: Any) -> None:
        """
        Saves the raw API response for the indices list.

        Args:
            raw_data: Unmodified response from GET /api/nots/index.
        """
        file_path = os.path.join(self.raw_dir, "indices_master.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=4, ensure_ascii=False)

    def save_raw_history(self, index_id: int, raw_data: Any) -> None:
        """
        Saves raw history data (usually a page or consolidated response).

        Args:
            index_id: The numeric index ID.
            raw_data: Unmodified history response data.
        """
        file_path = os.path.join(self.raw_dir, f"{index_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=4, ensure_ascii=False)
