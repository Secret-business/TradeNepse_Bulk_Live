import os
import sys
import json
import logging

# Ensure Database directory is in the import path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import daily_price.run
import company_master.run
import indices.run
import floorsheet.run

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def check_enabled(config_filename: str) -> bool:
    """
    Checks if a module is enabled by reading its settings file.
    Returns True if enabled or if settings file is missing.
    """
    config_path = os.path.join(BASE_DIR, "config", config_filename)
    if not os.path.exists(config_path):
        return True
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("enabled", True)
    except Exception:
        return True

def main() -> None:
    print("=========================================")
    print("TradeNepse Platform Sync Orchestrator starting")
    print("=========================================\n")

    # Define modules in standard order (Daily Price is dependency first, then Company Master, Indices, Floorsheet)
    modules = [
        {
            "name": "Daily Price",
            "settings": "daily_price_settings.json",
            "module_run": daily_price.run
        },
        {
            "name": "Company Master",
            "settings": "company_master_settings.json",
            "module_run": company_master.run
        },
        {
            "name": "Indices",
            "settings": "indices_settings.json",
            "module_run": indices.run
        },
        {
            "name": "Floorsheet",
            "settings": "floorsheet_settings.json",
            "module_run": floorsheet.run
        }
    ]

    for mod in modules:
        name = mod["name"]
        settings_file = mod["settings"]
        module_run = mod["module_run"]

        if check_enabled(settings_file):
            print(f"--> Executing Module: {name}...")
            try:
                module_run.main()
            except Exception as e:
                print(f"ERROR executing module {name}: {e}\n")
        else:
            print(f"--> Module {name} is disabled. Skipping.\n")

    print("=========================================")
    print("TradeNepse Platform Sync Orchestrator completed")
    print("=========================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOrchestrator sync interrupted by user. Safe to close.")
        sys.exit(0)
