import os
import json
from typing import Dict, Any, Optional, List


class CompanyMasterStorage:
    """
    Handles file storage operations for Company Master data.

    Storage layout:
        data/company_master/
            company_master.json     # Consolidated master record (all companies)
            raw/                    # Optional raw API responses per securityId
                {securityId}.json
    """

    def __init__(self, data_dir: str = "data/company_master"):
        """
        Initializes the storage manager with the target directory.

        Args:
            data_dir: Target directory path for storing company master data.
        """
        self.data_dir = os.path.abspath(data_dir)
        self.raw_dir = os.path.join(self.data_dir, "raw")
        self.master_file = os.path.join(self.data_dir, "company_master.json")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    def load_master(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the existing company master JSON file.

        Returns:
            A dictionary keyed by security_id (as string) mapping to company records.
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

    def save_master(self, master_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Saves the full company master dictionary to the consolidated JSON file.

        Args:
            master_data: Dictionary keyed by security_id (string) with company records.
        """
        with open(self.master_file, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)

    def save_raw_json(self, security_id: int, raw_data: Dict[str, Any]) -> None:
        """
        Saves the raw API response JSON for a specific security.

        Args:
            security_id: The numeric security ID.
            raw_data: The raw JSON response dictionary.
        """
        file_path = os.path.join(self.raw_dir, f"{security_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=4, ensure_ascii=False)

    def upsert_record(self, master_data: Dict[str, Dict[str, Any]], record: Dict[str, Any]) -> bool:
        """
        Inserts or updates a single company record in the master dictionary.
        Returns True if the record was new or changed, False if unchanged.

        Args:
            master_data: The in-memory master dictionary (mutated in place).
            record: A normalized company record from the parser.

        Returns:
            True if the record was inserted or updated, False if identical.
        """
        key = str(record.get("security_id", ""))
        if not key:
            return False

        existing = master_data.get(key)
        if existing:
            # Compare all fields except updated_date
            changed = False
            for field, value in record.items():
                if field == "updated_date":
                    continue
                if existing.get(field) != value:
                    changed = True
                    break

            if not changed:
                return False

        master_data[key] = record
        return True

    def get_existing_security_ids(self) -> List[int]:
        """
        Returns a list of security IDs already present in the master file.

        Returns:
            Sorted list of integer security IDs.
        """
        master = self.load_master()
        ids = []
        for key in master:
            try:
                ids.append(int(key))
            except (ValueError, TypeError):
                continue
        return sorted(ids)
