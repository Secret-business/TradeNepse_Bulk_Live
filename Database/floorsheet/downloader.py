import requests
import urllib3
from typing import Any

# Suppress certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FloorsheetDownloader:
    """
    Downloader responsible for querying the public floorsheet GET API on sharehubnepal.com.
    """

    def __init__(self):
        """
        Initializes the Floorsheet downloader.
        """
        self.api_url: str = "https://sharehubnepal.com/live/api/v2/floorsheet"

    def download_floorsheet_page(self, business_date: str, page: int = 1, size: int = 100) -> Any:
        """
        Downloads a single page of trade records for a specific business date.

        Endpoint: GET /live/api/v2/floorsheet?Size={size}&date={date}&page={page}

        Args:
            business_date: Date string formatted as YYYY-MM-DD or YYYY-M-D.
            page: 1-indexed page number to request.
            size: Page size or number of records to request.

        Returns:
            The raw JSON dictionary response from ShareHub.
        """
        params = {
            "Size": str(size),
            "date": business_date,
            "page": str(page)
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://sharehubnepal.com/nepse/floorsheet"
        }

        try:
            response = requests.get(self.api_url, params=params, headers=headers, verify=False, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"HTTP error {response.status_code} requesting page {page}: {response.text}")
        except Exception as e:
            raise RuntimeError(f"Connection error requesting floorsheet page {page} for date {business_date}: {e}")
