import time
import requests
import urllib3
from playwright.sync_api import sync_playwright

# Suppress certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NepseScraper:
    """
    A scraper class to fetch floorsheet data from NEPSE.
    Uses Playwright to intercept auth tokens and dynamic payload IDs,
    then makes direct high-speed HTTP requests in python.
    """
    def __init__(self):
        self.auth_token = None
        self.payload_id = None
        
    def refresh_credentials(self, max_retries=3):
        """
        Launches Playwright headless Chromium browser, navigates to the floor-sheet page,
        intercepts the API authorization token and payload id, and closes the browser.
        """
        for attempt in range(1, max_retries + 1):
            print(f"[{attempt}/{max_retries}] Starting Playwright browser to intercept credentials...")
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
                    
                    url = "https://www.nepalstock.com/floor-sheet"
                    page.goto(url, timeout=35000, wait_until="networkidle")
                    
                    # Wait up to 10 seconds for the AJAX request to load and be intercepted
                    for _ in range(20):
                        if captured_token and captured_id:
                            break
                        time.sleep(0.5)
                        
                    browser.close()
                    
                    if captured_token and captured_id:
                        self.auth_token = captured_token
                        self.payload_id = captured_id
                        print(f"Successfully captured credentials: ID={self.payload_id}")
                        return True
                    else:
                        print("Failed to capture credentials. Retrying...")
            except Exception as e:
                print(f"Error during Playwright token capture: {e}")
            time.sleep(2)
        return False

    def fetch_floorsheet_page(self, page, size=20):
        """
        Fetches a single page of floorsheet data using python requests with intercepted credentials.
        Automatically handles credential expiration.
        """
        if not self.auth_token or not self.payload_id:
            print("Credentials missing. Performing initial authentication...")
            if not self.refresh_credentials():
                raise Exception("Could not capture credentials from NEPSE floorsheet page.")
                
        url = "https://www.nepalstock.com/api/nots/nepse-data/floorsheet"
        params = {
            "page": str(page),
            "size": str(size),
            "sort": "contractId,desc"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Referer": "https://www.nepalstock.com/floor-sheet"
        }
        payload = {"id": self.payload_id}
        
        try:
            response = requests.post(url, params=params, json=payload, headers=headers, verify=False, timeout=15)
            
            # If unauthorized or forbidden, reload credentials and retry
            if response.status_code in (401, 403):
                print(f"API request failed with status {response.status_code} (Expired token). Refreshing credentials...")
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(url, params=params, json=payload, headers=headers, verify=False, timeout=15)
                else:
                    raise Exception("Failed to re-authenticate with NEPSE.")
                    
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to fetch floorsheet. Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            # Catch other request exceptions and try to heal once
            print(f"Network error on page {page}: {e}. Retrying with fresh authentication...")
            try:
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(url, params=params, json=payload, headers=headers, verify=False, timeout=15)
                    if response.status_code == 200:
                        return response.json()
            except Exception as e_retry:
                print(f"Retry request failed: {e_retry}")
            raise e
