from typing import Dict, Any, Optional
from datetime import datetime


class CompanyMasterParser:
    """
    Parser responsible for extracting and normalizing company master fields
    from the raw NEPSE /api/nots/security/{securityId} API response.

    Actual API response structure:
    {
        "securityDailyTradeDto": { ... trading data ... },
        "security": {
            "id": 2790,
            "symbol": "ACLBSL",
            "isin": "NPE322A00005",
            "listingDate": "2019-01-01",
            "securityName": "...",
            "companyId": {
                "sectorMaster": {
                    "sectorDescription": "Microfinance"
                }
            }
        },
        "stockListedShares": 3671435.0,
        "paidUpCapital": 367143488.0,
        "issuedCapital": 367143488.0,
        "marketCapitalization": 3490066111.0,
        "publicShares": 1334566,
        "publicPercentage": 36.35,
        "promoterShares": 2336869.0,
        "promoterPercentage": 63.65,
        "updatedDate": "2022-03-30T17:27:10.933",
        "securityId": 2790
    }
    """

    def parse_security_response(self, raw_json: Any, security_id: int) -> Optional[Dict[str, Any]]:
        """
        Parses a single security API response into a normalized company record.

        Args:
            raw_json: The raw JSON from the security API (dict or list).
            security_id: The securityId used to make the request (fallback).

        Returns:
            A normalized dictionary with company master fields, or None if
            the response is invalid / missing critical data.
        """
        # Handle empty list responses (inactive/delisted securities)
        if isinstance(raw_json, list):
            if len(raw_json) == 0:
                return None
            # If the list has a single dict, use it
            if len(raw_json) == 1 and isinstance(raw_json[0], dict):
                raw_json = raw_json[0]
            else:
                return None

        if not isinstance(raw_json, dict):
            return None

        # Extract nested sections
        security = raw_json.get("security", {}) or {}
        trade_dto = raw_json.get("securityDailyTradeDto", {}) or {}

        # Extract sector from deeply nested company -> sectorMaster
        sector = None
        company_id = security.get("companyId")
        if isinstance(company_id, dict):
            sector_master = company_id.get("sectorMaster")
            if isinstance(sector_master, dict):
                sector = sector_master.get("sectorDescription")

        # Build normalized record
        record = {
            "security_id":          self._get_int(raw_json, security, "securityId", "id", fallback=security_id),
            "symbol":               self._get_str(security, "symbol"),
            "security_name":        self._get_str(security, "securityName"),
            "sector":               sector,
            "listing_date":         self._get_str(security, "listingDate"),
            "isin":                 self._get_str(security, "isin"),
            "stock_listed_shares":  self._get_num(raw_json, "stockListedShares"),
            "public_shares":        self._get_num(raw_json, "publicShares"),
            "public_percentage":    self._get_num(raw_json, "publicPercentage"),
            "promoter_shares":      self._get_num(raw_json, "promoterShares"),
            "promoter_percentage":  self._get_num(raw_json, "promoterPercentage"),
            "paid_up_capital":      self._get_num(raw_json, "paidUpCapital"),
            "issued_capital":       self._get_num(raw_json, "issuedCapital"),
            "market_capitalization": self._get_num(raw_json, "marketCapitalization"),
            "updated_date":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Validate: must have at least symbol or security_name
        if not record.get("symbol") and not record.get("security_name"):
            return None

        return record

    def _get_str(self, source: dict, *keys: str) -> Optional[str]:
        """Extract the first non-None string value from source using keys."""
        for key in keys:
            val = source.get(key)
            if val is not None:
                return str(val)
        return None

    def _get_num(self, source: dict, *keys: str) -> Optional[float]:
        """Extract the first non-None numeric value from source using keys."""
        for key in keys:
            val = source.get(key)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return None

    def _get_int(self, *sources_and_keys, fallback: int = 0) -> int:
        """Extract the first integer value from multiple sources and keys."""
        # Separate sources (dicts) from keys (strings)
        sources = [s for s in sources_and_keys if isinstance(s, dict)]
        keys = [k for k in sources_and_keys if isinstance(k, str)]

        for source in sources:
            for key in keys:
                val = source.get(key)
                if val is not None:
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        continue
        return fallback

    def extract_security_ids_from_daily_price(self, daily_price_data: Dict[str, Any]) -> list:
        """
        Extracts unique securityId values from a daily price JSON response.

        Args:
            daily_price_data: Raw daily price JSON dictionary (has 'content' key with list).

        Returns:
            A sorted list of unique integer securityId values.
        """
        security_ids = set()

        if not isinstance(daily_price_data, dict):
            return []

        content = daily_price_data.get("content", [])
        if not isinstance(content, list):
            return []

        for item in content:
            if isinstance(item, dict) and "securityId" in item:
                try:
                    sid = int(item["securityId"])
                    security_ids.add(sid)
                except (ValueError, TypeError):
                    continue

        return sorted(security_ids)
