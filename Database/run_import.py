#!/usr/bin/env python
import os
import sys

# Ensure the root Database directory is in the import path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database.importers.import_manager import ImportManager

def main():
    """
    Command line trigger entry point for the TradeNepse ingestion process.
    """
    try:
        manager = ImportManager()
        manager.run()
    except Exception as e:
        print(f"Failed to execute ingestion orchestrator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
