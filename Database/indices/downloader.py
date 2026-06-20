import time
import requests
import urllib3
from typing import Optional, Any
from playwright.sync_api import sync_playwright

# Suppress certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IndicesDownloader:
    """
    Downloader responsible for fetching index listings and historical index data from NEPSE.
    
    Uses Playwright to intercept dynamic authorization tokens (headers) by visiting
    the NEPSE homepage, which allows us to call standard GET requests on the API.
    """

    def __init__(self):
        """
        Initializes the Indices downloader.
        """
        self.auth_token: Optional[str] = None
        self.base_url: str = "https://www.nepalstock.com"
        self.index_list_api: str = "https://www.nepalstock.com/api/nots/index"
        self.history_api_base: str = "https://www.nepalstock.com/api/nots/index/history"

    def refresh_credentials(self, max_retries: int = 3) -> bool:
        """
        Launches a headless browser to capture dynamic authentication headers.
        
        Navigates to the homepage and listens to requests to extract the 'authorization' header.

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

                    def handle_request(request):
                        nonlocal captured_token
                        if not captured_token:
                            auth = request.headers.get("authorization")
                            if auth:
                                captured_token = auth

                    page.on("request", handle_request)
                    page.goto(self.base_url, timeout=45000, wait_until="networkidle")

                    # Wait up to 10 seconds for interception
                    for _ in range(20):
                        if captured_token:
                            break
                        time.sleep(0.5)

                    browser.close()

                    if captured_token:
                        self.auth_token = captured_token
                        return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def download_indices_list(self) -> Any:
        """
        Downloads all active indices and their basic metadata.

        Endpoint: GET /api/nots/index

        Returns:
            The raw JSON response from NEPSE.
        """
        if not self.auth_token:
            if not self.refresh_credentials():
                raise RuntimeError("Failed to capture authentication token from NEPSE.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Authorization": self.auth_token,
            "Referer": "https://www.nepalstock.com/"
        }

        try:
            response = requests.get(self.index_list_api, headers=headers, verify=False, timeout=15)

            # If unauthorized, reload token and retry
            if response.status_code in (401, 403):
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    response = requests.get(self.index_list_api, headers=headers, verify=False, timeout=15)
                else:
                    raise RuntimeError("Failed to re-authenticate with NEPSE.")

            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"HTTP error {response.status_code} requesting indices list: {response.text}")
        except requests.exceptions.RequestException as e:
            # Self-healing connection error retry
            try:
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    response = requests.get(self.index_list_api, headers=headers, verify=False, timeout=15)
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass
            raise RuntimeError(f"Connection error requesting indices list: {e}")

    def download_index_history_page(self, index_id: int, page: int = 0, size: int = 500) -> Any:
        """
        Downloads a single page of historical records for an index.

        Endpoint: GET /api/nots/index/history/{indexId}?page={page}&size={size}

        Args:
            index_id: Numeric index ID.
            page: Zero-based page number to request.
            size: Size of the page to request.

        Returns:
            The raw JSON response from NEPSE history endpoint.
        """
        if not self.auth_token:
            if not self.refresh_credentials():
                raise RuntimeError("Failed to capture authentication token from NEPSE.")

        url = f"{self.history_api_base}/{index_id}"
        params = {
            "page": str(page),
            "size": str(size)
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Authorization": self.auth_token,
            "Referer": "https://www.nepalstock.com/"
        }

        try:
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=15)

            # If unauthorized, reload token and retry
            if response.status_code in (401, 403):
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    response = requests.get(url, params=params, headers=headers, verify=False, timeout=15)
                else:
                    raise RuntimeError("Failed to re-authenticate with NEPSE.")

            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"HTTP error {response.status_code} for indexId {index_id} (page {page}): {response.text}")
        except requests.exceptions.RequestException as e:
            # Self-healing connection error retry
            try:
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    response = requests.get(url, params=params, headers=headers, verify=False, timeout=15)
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass
            raise RuntimeError(f"Connection error requesting history page for indexId {index_id}: {e}")
