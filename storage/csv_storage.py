import os
import csv
import json
import pandas as pd
from datetime import datetime

COLUMNS = [
    "contractId",
    "stockSymbol",
    "securityName",
    "contractQuantity",
    "contractRate",
    "contractAmount",
    "tradeTime",
    "businessDate",
    "capturedAt"
]

def get_csv_path(business_date_str, data_folder="data"):
    """
    Returns the absolute path to the CSV file for the given business date.
    E.g. data_folder/2026-06-16.csv
    """
    os.makedirs(data_folder, exist_ok=True)
    return os.path.abspath(os.path.join(data_folder, f"{business_date_str}.csv"))

def load_existing_ids(file_path):
    """
    Loads all existing contractIds from the CSV file into a set.
    """
    existing_ids = set()
    if not os.path.exists(file_path):
        return existing_ids
    
    try:
        df = pd.read_csv(file_path, usecols=["contractId"], dtype={"contractId": int})
        existing_ids = set(df["contractId"].tolist())
    except Exception as e:
        # Fallback to pure CSV reading if file is empty or corrupted
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "contractId" in row and row["contractId"]:
                        existing_ids.add(int(row["contractId"]))
        except Exception as e_csv:
            print(f"Error loading existing IDs from {file_path}: {e_csv}")
            
    return existing_ids

def append_new_trades(file_path, trades):
    """
    Appends new trades to the CSV file.
    trades is a list of dictionaries containing trade details.
    """
    if not trades:
        return
    
    file_exists = os.path.exists(file_path)
    
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            if not file_exists:
                writer.writeheader()
            
            for t in trades:
                # Align fields and make sure they conform to columns
                row = {
                    "contractId": int(t.get("contractId")),
                    "stockSymbol": t.get("stockSymbol"),
                    "securityName": t.get("securityName"),
                    "contractQuantity": int(t.get("contractQuantity", 0)),
                    "contractRate": float(t.get("contractRate", 0.0)),
                    "contractAmount": float(t.get("contractAmount", 0.0)),
                    "tradeTime": t.get("tradeTime"),
                    "businessDate": t.get("businessDate"),
                    "capturedAt": t.get("capturedAt", datetime.now().isoformat())
                }
                writer.writerow(row)
    except Exception as e:
        print(f"Error writing to CSV {file_path}: {e}")

def read_today_trades(file_path):
    """
    Reads trades from CSV file and returns a Pandas DataFrame.
    """
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=COLUMNS)
    
    try:
        df = pd.read_csv(file_path, dtype={"contractId": int})
        # Double check types are correct
        df["contractId"] = df["contractId"].astype(int)
        df["contractQuantity"] = df["contractQuantity"].astype(int)
        df["contractRate"] = df["contractRate"].astype(float)
        df["contractAmount"] = df["contractAmount"].astype(float)
        return df
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return pd.DataFrame(columns=COLUMNS)

def get_status_file_path(data_folder="data"):
    os.makedirs(data_folder, exist_ok=True)
    return os.path.abspath(os.path.join(data_folder, "collector_status.json"))

def update_collector_status(status_dict, data_folder="data"):
    """
    Writes background collector status to data/collector_status.json
    """
    filepath = get_status_file_path(data_folder)
    try:
        with open(filepath, "w") as f:
            json.dump(status_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error updating collector status: {e}")
        return False

def read_collector_status(data_folder="data"):
    """
    Reads background collector status from data/collector_status.json
    """
    filepath = get_status_file_path(data_folder)
    if not os.path.exists(filepath):
        return {
            "status": "offline",
            "last_heartbeat": None,
            "last_sync_time": None,
            "total_records": 0,
            "is_syncing": False,
            "business_date": None
        }
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading collector status: {e}")
        return {
            "status": "offline",
            "last_heartbeat": None,
            "last_sync_time": None,
            "total_records": 0,
            "is_syncing": False,
            "business_date": None
        }
