from typing import Set
from indices.storage import IndicesStorage


class IndicesResume:
    """
    Manages the resume logic for Indices historical data sync.
    Identifies which business dates are already stored for a given index to avoid redownloads.
    """

    def __init__(self, storage: IndicesStorage):
        """
        Initializes the resume system.

        Args:
            storage: An instance of IndicesStorage.
        """
        self.storage = storage

    def get_stored_dates(self, index_id: int) -> Set[str]:
        """
        Extracts the set of all unique business dates already downloaded for a given index.

        Args:
            index_id: The numeric ID of the index.

        Returns:
            A set of date strings (YYYY-MM-DD) already stored.
        """
        history = self.storage.load_history(index_id)
        stored_dates = set()
        for record in history:
            date_str = record.get("business_date")
            if date_str:
                stored_dates.add(str(date_str))
        return stored_dates
