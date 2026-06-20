# TradeNepse Data Platform V2 - Phase 1 (Daily Price Sync)

This is the Daily Price Sync module (V1) for TradeNepse Data Platform V2. It is designed to be beginner-friendly, path-independent, modular, and operates entirely on raw JSON data storage rather than an SQL database.

---

## Features

1. **Self-Contained Architecture**: All logic and data files are confined within the `Database/` directory.
2. **Dynamic Authentication Bypass**: Uses Playwright headless Chromium to bypass NEPSE authentication and payload validation dynamically.
3. **JSON Raw Storage**: Stores unmodified API responses as `data/daily_price/YYYY-MM-DD.json`.
4. **Intelligent Resume**: Scans previously stored JSON filenames, finds the latest date, and starts syncing from `latest_date + 1 day`.
5. **Configurable Start**: On the first run, the sync starts from the `start_date` defined in `config/settings.json`.
6. **Detailed Logging**: Logs synchronization events, record counts, and detailed errors to `logs/daily_price.log` and standard output.
7. **Politeness Delay**: Employs configurable request delays to respect NEPSE server rate limits.

---

## Folder Structure

```
Database/
│
├── config/
│   └── settings.json            # Downloader configuration (start date, delays)
│
├── data/
│   ├── daily_price/             # Destination for raw YYYY-MM-DD.json files
│   ├── company_master/          # Placeholder for Company Master data
│   ├── indices/                 # Placeholder for Indices data
│   └── floorsheet/              # Placeholder for Floorsheet data
│
├── daily_price/
│   ├── __init__.py              # Exports module classes and logger helper
│   ├── downloader.py            # Playwright auth capture & today-price POST request
│   ├── parser.py                # JSON response structure parser & validator
│   ├── storage.py               # Raw JSON file storage operations
│   ├── resume.py                # Filesystem scanner to find latest synced date
│   └── logger.py                # Log setup for file and stream logging
│
├── logs/
│   └── daily_price.log          # System output and sync tracking log
│
└── app.py                       # Application execution entry point
```

---

## Setup Instructions

### 1. Install Dependencies
Ensure you have the required python packages installed (from the project's root `requirements.txt`):
```bash
pip install playwright requests urllib3
```

### 2. Install Playwright Web Browser
You must install the Chromium binary for Playwright to allow credentials capture:
```bash
playwright install chromium
```

---

## Usage Instructions

### 1. Configuration
Modify `config/settings.json` to change the default configuration:
* `start_date`: The calendar date (format `YYYY-MM-DD`) from which to sync if no previous data files exist.
* `request_delay_seconds`: The duration to wait (in seconds) between requests to NEPSE.

Example:
```json
{
  "start_date": "2026-06-16",
  "request_delay_seconds": 1.5
}
```

### 2. Run the Synchronizer
Execute `app.py` from within the `Database/` directory:
```bash
cd D:\TradeNepse\Bulk live market\Database
python app.py
```

### 3. Review Log Outputs
Inspect logs in the command line or view `logs/daily_price.log` to track processing details:
```
2026-06-20 08:20:00 [INFO] Date Processed: 2026-06-16 | Records Downloaded: 355 | Errors: None
2026-06-20 08:20:02 [INFO] Date Processed: 2026-06-17 | Records Downloaded: 352 | Errors: None
2026-06-20 08:20:04 [INFO] Date Processed: 2026-06-18 | Records Downloaded: 0 | Errors: None (Skipped - No trading data)
```
If the synchronizer encounters a critical error, it logs the traceback, saves current progress, and exits cleanly. Running it again will resume sync from that failed day.
