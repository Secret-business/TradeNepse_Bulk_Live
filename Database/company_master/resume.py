import os
import json
import glob
from typing import Set, List


class CompanyMasterResume:
    """
    Manages resume logic for the Company Master downloader.

    Determines which security IDs have already been successfully downloaded
    so they can be skipped on subsequent runs (unless data has changed).
    """

    def __init__(self, data_dir: str = "data/company_master"):
        """
        Initializes the resume system.

        Args:
            data_dir: Path to the company master data directory.
        """
        self.data_dir = os.path.abspath(data_dir)
        self.master_file = os.path.join(self.data_dir, "company_master.json")
        self.raw_dir = os.path.join(self.data_dir, "raw")

    def get_downloaded_security_ids(self) -> Set[int]:
        """
        Returns the set of security IDs that already exist in the master file.

        Returns:
            A set of integer security IDs already stored.
        """
        if not os.path.isfile(self.master_file):
            return set()

        try:
            with open(self.master_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    result = set()
                    for key in data:
                        try:
                            result.add(int(key))
                        except (ValueError, TypeError):
                            continue
                    return result
        except (json.JSONDecodeError, OSError):
            pass

        return set()

    def get_pending_security_ids(self, all_ids: List[int], force_update: bool = False) -> List[int]:
        """
        Determines which security IDs still need to be downloaded.

        If force_update is True, returns all IDs (for full refresh).
        Otherwise, returns only IDs not yet in the master file.

        Args:
            all_ids: Complete list of security IDs to process.
            force_update: If True, re-download all regardless of existing data.

        Returns:
            Sorted list of security IDs that need downloading.
        """
        if force_update:
            return sorted(all_ids)

        existing = self.get_downloaded_security_ids()
        pending = [sid for sid in all_ids if sid not in existing]
        return sorted(pending)

    def get_raw_downloaded_ids(self) -> Set[int]:
        """
        Returns security IDs for which raw JSON files exist on disk.

        Returns:
            A set of security IDs with raw JSON saved.
        """
        if not os.path.isdir(self.raw_dir):
            return set()

        ids = set()
        for filepath in glob.glob(os.path.join(self.raw_dir, "*.json")):
            filename = os.path.basename(filepath).replace(".json", "")
            try:
                ids.add(int(filename))
            except (ValueError, TypeError):
                continue
        return ids
