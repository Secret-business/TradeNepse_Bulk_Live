from typing import List, Dict, Any
from daily_price.models import DailyPriceRecord

def parse_today_price_response(response_json: Dict[str, Any]) -> List[DailyPriceRecord]:
    """
    Parses the JSON response from NEPSE today-price endpoint.
    Extracts the list of records from the 'content' key and converts them
    to DailyPriceRecord structures.

    Args:
        response_json: Raw API response dictionary.

    Returns:
        List of parsed DailyPriceRecord instances.
    """
    if not isinstance(response_json, dict):
        return []

    content = response_json.get("content")
    if not isinstance(content, list):
        return []

    records: List[DailyPriceRecord] = []
    for index, item in enumerate(content):
        if not isinstance(item, dict):
            continue
            
        # Ensure critical identification fields are present
        if not item.get("symbol") or not item.get("businessDate"):
            continue

        try:
            record = DailyPriceRecord.from_api_json(item)
            records.append(record)
        except (ValueError, TypeError):
            # Ignore individual malformed records but log or print if debugging
            continue

    return records
