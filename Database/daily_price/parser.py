from typing import Dict, Any, List, Optional

class DailyPriceParser:
    """
    Parser class responsible for validating and interpreting raw daily price JSON data.
    """

    def parse_and_validate(self, response_json: Any) -> List[Dict[str, Any]]:
        """
        Parses and validates the raw API JSON response.
        
        Args:
            response_json: The raw JSON returned by the NEPSE today-price endpoint.
            
        Returns:
            A list of valid records from the response. Returns an empty list if the structure is invalid.
        """
        if not isinstance(response_json, dict):
            return []

        content = response_json.get("content")
        if not isinstance(content, list):
            return []

        valid_records: List[Dict[str, Any]] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            
            # A valid record must contain at least the business date and symbol
            if not item.get("businessDate") or not item.get("symbol"):
                continue
                
            valid_records.append(item)

        return valid_records

    def get_record_count(self, response_json: Any) -> int:
        """
        Convenience method to retrieve the count of valid records.
        
        Args:
            response_json: The raw JSON response.
            
        Returns:
            The number of valid records in the response.
        """
        return len(self.parse_and_validate(response_json))
