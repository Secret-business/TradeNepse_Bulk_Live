from typing import Dict, Any, List, Optional


class FloorsheetParser:
    """
    Parses and normalizes raw JSON data from the ShareHub Floorsheet GET API response.
    """

    def parse_floorsheet_page(self, raw_json: Any) -> List[Dict[str, Any]]:
        """
        Parses a single floorsheet page response.

        Args:
            raw_json: Raw response dict from GET /live/api/v2/floorsheet.

        Returns:
            A list of normalized trade records.
        """
        normalized_records: List[Dict[str, Any]] = []

        if not isinstance(raw_json, dict):
            return normalized_records

        data = raw_json.get("data")
        if not isinstance(data, dict):
            return normalized_records

        content = data.get("content")
        if not isinstance(content, list):
            return normalized_records

        for item in content:
            if not isinstance(item, dict):
                continue

            contract_id = self._get_int(item, "contractId")
            if not contract_id:
                continue

            business_date_raw = item.get("businessDate", "")
            business_date = str(business_date_raw)[:10] if business_date_raw else ""

            record = {
                "business_date":        business_date,
                "symbol":               self._get_str(item, "symbol"),
                "company_name":         self._get_str(item, "name"),
                "buyer_broker_id":      self._get_str(item, "buyerMemberId"),
                "seller_broker_id":     self._get_str(item, "sellerMemberId"),
                "buyer_broker_name":    self._get_str(item, "buyerBrokerName"),
                "seller_broker_name":   self._get_str(item, "sellerBrokerName"),
                "contract_id":          contract_id,
                "quantity":             self._get_int(item, "contractQuantity"),
                "rate":                 self._get_float(item, "contractRate"),
                "amount":               self._get_float(item, "contractAmount"),
                "trade_time":           self._get_str(item, "tradeTime")
            }
            normalized_records.append(record)

        return normalized_records

    def get_total_pages(self, raw_json: Any) -> int:
        """
        Extracts the total pages count from raw page response.
        """
        if not isinstance(raw_json, dict):
            return 0
        data = raw_json.get("data")
        if not isinstance(data, dict):
            return 0
        return self._get_int(data, "totalPages") or 0

    def get_total_trades(self, raw_json: Any) -> int:
        """
        Extracts the total number of trades from raw page response.
        """
        if not isinstance(raw_json, dict):
            return 0
        data = raw_json.get("data")
        if not isinstance(data, dict):
            return 0
        # Check both totalTrades and totalItems
        total = self._get_int(data, "totalTrades")
        if total is None:
            total = self._get_int(data, "totalItems")
        return total or 0

    def has_next_page(self, raw_json: Any) -> bool:
        """
        Checks if a next page is available according to the API.
        """
        if not isinstance(raw_json, dict):
            return False
        data = raw_json.get("data")
        if not isinstance(data, dict):
            return False
        return bool(data.get("hasNext", False))

    def _get_str(self, source: dict, key: str) -> Optional[str]:
        """Safely extracts a string."""
        val = source.get(key)
        if val is not None:
            return str(val).strip()
        return None

    def _get_float(self, source: dict, key: str) -> Optional[float]:
        """Safely extracts a float."""
        val = source.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    def _get_int(self, source: dict, key: str) -> Optional[int]:
        """Safely extracts an int."""
        val = source.get(key)
        if val is not None:
            try:
                return int(float(val))
            except (ValueError, TypeError):
                pass
        return None
