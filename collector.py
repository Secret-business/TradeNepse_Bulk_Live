import os
import sys

# Add the project root directory to the python path so modules are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collector.sync_daemon import run_sync_loop

if __name__ == "__main__":
    try:
        run_sync_loop()
    except KeyboardInterrupt:
        print("\nCollector process terminated.")
        sys.exit(0)
