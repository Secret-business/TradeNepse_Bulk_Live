from typing import Dict, Any, List, Optional


class IndicesParser:
    """
    Parses and normalizes raw JSON data from NEPSE Indices API endpoints.
    """

    def parse_master_response(self, raw_json: Any) -> Dict[str, str]:
        """
        Parses the raw indices list API response.

        Args:
            raw_json: Raw response from GET /api/nots/index.

        Returns:
            A dictionary mapping indexId string to indexName.
        """
        master_map: Dict[str, str] = {}
        if not isinstance(raw_json, list):
            return master_map

        for item in raw_json:
            if not isinstance(item, dict):
                continue
            idx_id = item.get("id")
            idx_name = item.get("indexName")
            if idx_id is not None and idx_name:
                master_map[str(idx_id)] = str(idx_name)

        return master_map

    def parse_history_response(self, raw_json: Any, index_name: str) -> List[Dict[str, Any]]:
        """
        Parses a single history response page from NEPSE.

        Args:
            raw_json: Raw response dict from GET /api/nots/index/history/{indexId}.
            index_name: Name of the index (looked up from master index).

        Returns:
            A list of normalized history records.
        """
        normalized_records: List[Dict[str, Any]] = []

        if not isinstance(raw_json, dict):
            return normalized_records

        content = raw_json.get("content")
        if not isinstance(content, list):
            return normalized_records

        for item in content:
            if not isinstance(item, dict):
                continue

            business_date = item.get("businessDate")
            # Business date is critical
            if not business_date:
                continue

            record = {
                "business_date":        str(business_date),
                "index_id":             self._get_int(item, "exchangeIndexId"),
                "index_name":           index_name,
                "open_index":           self._get_float(item, "openIndex"),
                "high_index":           self._get_float(item, "highIndex"),
                "low_index":            self._get_float(item, "lowIndex"),
                "closing_index":        self._get_float(item, "closingIndex"),
                "fifty_two_week_high":   self._get_float(item, "fiftyTwoWeekHigh"),
                "fifty_two_week_low":    self._get_float(item, "fiftyTwoWeekLow"),
                "turnover_value":       self._get_float(item, "turnoverValue"),
                "turnover_volume":      self._get_int(item, "turnoverVolume"),
                "total_transaction":    self._get_int(item, "totalTransaction"),
                "abs_change":           self._get_float(item, "absChange"),
                "percentage_change":    self._get_float(item, "percentageChange")
            }
            normalized_records.append(record)

        return normalized_records

    def _get_float(self, source: dict, key: str) -> Optional[float]:
        """Safely extracts a float value."""
        val = source.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    def _get_int(self, source: dict, key: str) -> Optional[int]:
        """Safely extracts an int value."""
        val = source.get(key)
        if val is not None:
            try:
                return int(float(val))  # Handles float strings like "123.0"
            except (ValueError, TypeError):
                pass
        return None
