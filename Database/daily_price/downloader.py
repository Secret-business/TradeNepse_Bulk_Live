import time
import requests
import urllib3
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright

# Suppress certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DailyPriceDownloader:
    """
    Downloader responsible for fetching today's price raw JSON data from NEPSE.
    
    Uses Playwright to intercept dynamic authorization tokens and payload IDs
    from the floorsheet page, then performs standard POST requests to the NEPSE API.
    """
    
    def __init__(self):
        self.auth_token: Optional[str] = None
        self.payload_id: Optional[str] = None
        self.floorsheet_url: str = "https://www.nepalstock.com/floor-sheet"
        self.api_url: str = "https://www.nepalstock.com/api/nots/nepse-data/today-price"

    def refresh_credentials(self, max_retries: int = 3) -> bool:
        """
        Launches a headless browser to capture dynamic authentication headers and IDs.
        
        Args:
            max_retries: Maximum number of attempts to capture credentials.
            
        Returns:
            True if credentials were captured successfully, False otherwise.
        """
        for attempt in range(1, max_retries + 1):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled", "--disable-http2", "--no-sandbox"]
                    )
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        ignore_https_errors=True
                    )
                    page = context.new_page()
                    # Hide webdriver property to look like a normal browser
                    page.add_init_script("delete navigator.__proto__.webdriver;")
                    
                    captured_token = None
                    captured_id = None
                    
                    def handle_request(request):
                        nonlocal captured_token, captured_id
                        if "/api/nots/nepse-data/floorsheet" in request.url:
                            auth = request.headers.get("authorization")
                            if auth:
                                captured_token = auth
                            try:
                                payload = request.post_data_json
                                if payload and "id" in payload:
                                    captured_id = payload["id"]
                            except Exception:
                                pass
                                
                    page.on("request", handle_request)
                    
                    page.goto(self.floorsheet_url, timeout=35000, wait_until="networkidle")
                    
                    # Wait up to 10 seconds for interception
                    for _ in range(20):
                        if captured_token and captured_id:
                            break
                        time.sleep(0.5)
                        
                    browser.close()
                    
                    if captured_token and captured_id:
                        self.auth_token = captured_token
                        self.payload_id = captured_id
                        return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def download_date(self, business_date: str, size: int = 500) -> Dict[str, Any]:
        """
        Downloads today's stock prices for a specific date from NEPSE.
        
        Args:
            business_date: Date string formatted as YYYY-MM-DD.
            size: The page size or number of records to request (defaults to 500).
            
        Returns:
            The raw JSON dictionary from NEPSE API response.
        """
        if not self.auth_token or not self.payload_id:
            if not self.refresh_credentials():
                raise RuntimeError("Failed to capture credentials from NEPSE floorsheet.")
                
        params = {
            "size": str(size),
            "businessDate": business_date
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Referer": "https://www.nepalstock.com/today-price"
        }
        payload = {"id": self.payload_id}
        
        try:
            response = requests.post(self.api_url, params=params, json=payload, headers=headers, verify=False, timeout=15)
            
            # If unauthorized or forbidden, reload credentials and retry once
            if response.status_code in (401, 403):
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(self.api_url, params=params, json=payload, headers=headers, verify=False, timeout=15)
                else:
                    raise RuntimeError("Failed to re-authenticate with NEPSE.")
                    
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500 and "Searched Date is not valid" in response.text:
                return {"content": [], "message": "Searched Date is not valid"}
            else:
                raise RuntimeError(f"HTTP error {response.status_code}: {response.text}")
        except Exception as e:
            # Healing attempt for connection exceptions
            try:
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(self.api_url, params=params, json=payload, headers=headers, verify=False, timeout=15)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 500 and "Searched Date is not valid" in response.text:
                        return {"content": [], "message": "Searched Date is not valid"}
            except Exception:
                pass
            raise e
