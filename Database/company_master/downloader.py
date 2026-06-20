import os
import sys
import json
import time
import glob
import requests
import urllib3
from typing import Optional, Dict, Any, List, Set
from playwright.sync_api import sync_playwright

# Suppress certificate verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CompanyMasterDownloader:
    """
    Downloader responsible for fetching company master data from NEPSE.

    Step 1: Reads securityId values from existing Daily Price data files.
    Step 2: For each securityId, calls POST /api/nots/security/{securityId}
            to retrieve company detail data.

    Uses Playwright to capture dynamic authentication tokens by visiting
    a company detail page and intercepting the POST request to the
    /api/nots/security/ endpoint, which carries the correct dynamic
    payload ID for security API calls.
    """

    # A known active securityId used to trigger the company detail page
    # and capture the auth token + dynamic payload ID.
    PROBE_SECURITY_ID = 2790  # ACLBSL - always active

    def __init__(self, daily_price_data_dir: str = "data/daily_price"):
        """
        Initializes the Company Master downloader.

        Args:
            daily_price_data_dir: Path to the directory containing daily price JSON files.
        """
        self.auth_token: Optional[str] = None
        self.payload_id: Optional[str] = None
        self.company_detail_url: str = f"https://www.nepalstock.com/company/detail/{self.PROBE_SECURITY_ID}"
        self.security_api_base: str = "https://www.nepalstock.com/api/nots/security"
        self.daily_price_data_dir: str = os.path.abspath(daily_price_data_dir)

    def refresh_credentials(self, max_retries: int = 3) -> bool:
        """
        Launches a headless browser to capture dynamic authentication headers
        and the correct payload ID for the security API endpoint.

        Navigates to a company detail page (/company/detail/{id}) which triggers
        a POST request to /api/nots/security/{id}. We intercept that request to
        capture both the auth token and the dynamic 'id' field in the payload.

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
                        # Intercept POST requests to /api/nots/security/{securityId}
                        url = request.url
                        if "/api/nots/security/" in url and request.method == "POST":
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

                    page.goto(self.company_detail_url, timeout=45000, wait_until="networkidle")

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

    def extract_all_security_ids(self) -> List[int]:
        """
        Scans all Daily Price JSON files and extracts unique securityId values.

        Returns:
            A sorted list of unique integer securityId values found across all files.
        """
        all_ids: Set[int] = set()

        if not os.path.isdir(self.daily_price_data_dir):
            return []

        search_pattern = os.path.join(self.daily_price_data_dir, "????-??-??.json")
        matching_files = glob.glob(search_pattern)

        for file_path in matching_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    continue

                content = data.get("content", [])
                if not isinstance(content, list):
                    continue

                for item in content:
                    if isinstance(item, dict) and "securityId" in item:
                        try:
                            sid = int(item["securityId"])
                            all_ids.add(sid)
                        except (ValueError, TypeError):
                            continue
            except (json.JSONDecodeError, OSError):
                continue

        return sorted(all_ids)

    def download_security(self, security_id: int) -> Dict[str, Any]:
        """
        Downloads company data for a single securityId from NEPSE.

        Endpoint: POST /api/nots/security/{securityId}

        Args:
            security_id: The numeric security ID to look up.

        Returns:
            The raw JSON dictionary from the NEPSE security API response.

        Raises:
            RuntimeError: If authentication fails or the API returns an error.
        """
        if not self.auth_token or not self.payload_id:
            if not self.refresh_credentials():
                raise RuntimeError("Failed to capture credentials from NEPSE company detail page.")

        url = f"{self.security_api_base}/{security_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Referer": "https://www.nepalstock.com/company/detail"
        }
        payload = {"id": self.payload_id}

        try:
            response = requests.post(url, json=payload, headers=headers, verify=False, timeout=15)

            # If unauthorized or forbidden, reload credentials and retry once
            if response.status_code in (401, 403):
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(url, json=payload, headers=headers, verify=False, timeout=15)
                else:
                    raise RuntimeError("Failed to re-authenticate with NEPSE.")

            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"HTTP error {response.status_code} for securityId {security_id}: {response.text}")

        except requests.exceptions.RequestException as e:
            # Healing attempt for connection exceptions
            try:
                if self.refresh_credentials():
                    headers["Authorization"] = self.auth_token
                    payload["id"] = self.payload_id
                    response = requests.post(url, json=payload, headers=headers, verify=False, timeout=15)
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass
            raise RuntimeError(f"Connection error for securityId {security_id}: {e}")
