import time
import os
import sys
from datetime import datetime
from settings.config import load_settings
from storage.csv_storage import (
    get_csv_path,
    load_existing_ids,
    append_new_trades,
    update_collector_status
)
from collector.nepse_scraper import NepseScraper

def run_sync_loop():
    """
    Main loop for data collector.
    Polls NEPSE floorsheet API, checks for updates, and appends to CSV.
    """
    print("Initializing NEPSE Live Bulk Market Analyzer Collector Daemon...")
    scraper = NepseScraper()
    
    # Keep track of active date and in-memory set of contractIds
    current_date = None
    existing_ids = set()
    csv_path = None
    
    # Keep track of heartbeat status
    status_dict = {
        "status": "starting",
        "last_heartbeat": datetime.now().isoformat(),
        "last_sync_time": None,
        "total_records": 0,
        "is_syncing": False,
        "business_date": None,
        "sync_progress": ""
    }
    
    settings = load_settings()
    data_folder = settings.get("data_folder", "data")
    update_collector_status(status_dict, data_folder)
    
    while True:
        try:
            # Reload settings in case they changed in the dashboard
            settings = load_settings()
            data_folder = settings.get("data_folder", "data")
            refresh_interval = settings.get("refresh_interval", 15)
            
            # Check if market is open before performing any network actions
            from analytics.schedule import market_is_open
            if not market_is_open():
                print("Market is closed. Skipping Floorsheet sync cycle.")
                status_dict["status"] = "idle"
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                update_collector_status(status_dict, data_folder)
                time.sleep(refresh_interval)
                continue
                
            # 1. Fetch page 0 to get current business date and total pages
            print("Checking floorsheet page 0...")
            status_dict["status"] = "checking"
            status_dict["last_heartbeat"] = datetime.now().isoformat()
            update_collector_status(status_dict, data_folder)
            
            page0_data = scraper.fetch_floorsheet_page(page=0, size=50)
            
            floorsheets_section = page0_data.get("floorsheets", {})
            content = floorsheets_section.get("content", [])
            total_pages = floorsheets_section.get("totalPages", 0)
            total_elements = floorsheets_section.get("totalElements", 0)
            
            if not content:
                print("No trade data found in page 0 response. Market might not have started or data is temporarily empty.")
                status_dict["status"] = "idle"
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                update_collector_status(status_dict, data_folder)
                time.sleep(refresh_interval)
                continue
                
            # Read business date from the first record
            api_business_date = content[0].get("businessDate")
            if not api_business_date:
                # Fallback to local date if missing
                api_business_date = datetime.now().strftime("%Y-%m-%d")
                
            # 2. Check if the business date has rolled over or is not initialized
            if current_date != api_business_date:
                print(f"New business date detected: {api_business_date} (Previous: {current_date})")
                current_date = api_business_date
                csv_path = get_csv_path(current_date, data_folder)
                print(f"Loading existing trade IDs for {current_date} from {csv_path}...")
                existing_ids = load_existing_ids(csv_path)
                print(f"Loaded {len(existing_ids)} existing trade IDs.")
                
            # 3. Determine if we need Historical Sync or Live Sync
            if not existing_ids:
                print(f"No records found for business date {current_date}. Triggering Historical Sync...")
                status_dict["is_syncing"] = True
                status_dict["status"] = "historical_sync"
                status_dict["business_date"] = current_date
                status_dict["sync_progress"] = f"0 / {total_pages} pages"
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                update_collector_status(status_dict, data_folder)
                
                # Fetch all pages from 0 to total_pages-1
                all_new_trades = []
                # Go backwards or forwards? If we go page 0 to total_pages, page 0 contains the newest.
                # Let's collect page by page.
                print(f"Historical Sync: Syncing {total_pages} pages ({total_elements} records)...")
                
                for p_num in range(total_pages):
                    status_dict["sync_progress"] = f"Syncing page {p_num + 1} / {total_pages}"
                    status_dict["last_heartbeat"] = datetime.now().isoformat()
                    update_collector_status(status_dict, data_folder)
                    
                    print(f"Fetching page {p_num + 1}/{total_pages}...")
                    try:
                        p_data = scraper.fetch_floorsheet_page(page=p_num, size=50)
                        p_content = p_data.get("floorsheets", {}).get("content", [])
                        
                        page_new_trades = []
                        for t in p_content:
                            cid = int(t.get("contractId"))
                            if cid not in existing_ids:
                                existing_ids.add(cid)
                                t["capturedAt"] = datetime.now().isoformat()
                                page_new_trades.append(t)
                                
                        if page_new_trades:
                            # Append page by page to save progress and keep file written
                            append_new_trades(csv_path, page_new_trades)
                            print(f"  Saved {len(page_new_trades)} new trades from page {p_num + 1}.")
                            
                    except Exception as e_page:
                        print(f"Error fetching page {p_num}: {e_page}. Will retry next loop.")
                    
                    # Sleep slightly to avoid rate limit
                    time.sleep(0.1)
                
                status_dict["is_syncing"] = False
                status_dict["status"] = "running"
                status_dict["sync_progress"] = "Complete"
                status_dict["last_sync_time"] = datetime.now().isoformat()
                status_dict["total_records"] = len(existing_ids)
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                update_collector_status(status_dict, data_folder)
                print("Historical Sync Completed.")
                
            else:
                # Incremental Live Mode
                print(f"Starting incremental sync. Checking newest pages...")
                status_dict["status"] = "live_sync"
                status_dict["business_date"] = current_date
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                update_collector_status(status_dict, data_folder)
                
                new_trades_found = []
                stop_traversal = False
                p_num = 0
                
                # Check pages until we find a page that contains only already-seen records
                while not stop_traversal and p_num < total_pages:
                    print(f"Checking page {p_num}...")
                    p_data = scraper.fetch_floorsheet_page(page=p_num, size=50)
                    p_content = p_data.get("floorsheets", {}).get("content", [])
                    
                    if not p_content:
                        break
                        
                    page_has_new = False
                    for t in p_content:
                        cid = int(t.get("contractId"))
                        if cid not in existing_ids:
                            existing_ids.add(cid)
                            t["capturedAt"] = datetime.now().isoformat()
                            new_trades_found.append(t)
                            page_has_new = True
                            
                    # If this page had no new records at all, we stop going deeper!
                    if not page_has_new:
                        print(f"Page {p_num} contains only already-seen records. Stopping traversal.")
                        stop_traversal = True
                    else:
                        p_num += 1
                        time.sleep(0.1)
                
                if new_trades_found:
                    print(f"Live Sync: Found and saving {len(new_trades_found)} new trades.")
                    # Sort by contractId ascending so we append them in chronological order
                    new_trades_found.sort(key=lambda x: int(x.get("contractId")))
                    append_new_trades(csv_path, new_trades_found)
                else:
                    print("Live Sync: No new trades detected.")
                    
                status_dict["status"] = "running"
                status_dict["last_sync_time"] = datetime.now().isoformat()
                status_dict["total_records"] = len(existing_ids)
                status_dict["last_heartbeat"] = datetime.now().isoformat()
                status_dict["sync_progress"] = f"Synced {len(new_trades_found)} new"
                update_collector_status(status_dict, data_folder)
                
        except Exception as e:
            print(f"Error in sync loop: {e}")
            status_dict["status"] = "error"
            status_dict["sync_progress"] = str(e)[:50]
            status_dict["last_heartbeat"] = datetime.now().isoformat()
            update_collector_status(status_dict, data_folder)
            
        print(f"Sleeping for {refresh_interval} seconds...")
        time.sleep(refresh_interval)

if __name__ == "__main__":
    try:
        run_sync_loop()
    except KeyboardInterrupt:
        print("\nCollector Daemon stopped by user.")
        sys.exit(0)
