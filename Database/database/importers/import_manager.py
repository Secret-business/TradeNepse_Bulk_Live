import os
import sys
import json
import logging
import psycopg2
from datetime import datetime
from glob import glob

# Set up root/parent paths to make sure package imports work
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database.importers.company_master_importer import CompanyMasterImporter
from database.importers.daily_price_importer import DailyPriceImporter
from database.importers.indices_importer import IndicesImporter
from database.importers.floorsheet_importer import FloorsheetImporter

class ImportManager:
    """
    Orchestrator for the TradeNepse ingestion pipeline.
    Coordinates database connections, config loading, sequential importer calls,
    test mode filtering, and detailed progress logging.
    """

    def __init__(self, config_path=None, log_dir=None):
        self.base_dir = BASE_DIR
        self.config_path = config_path or os.path.join(self.base_dir, "config", "database_settings.json")
        self.log_dir = log_dir or os.path.join(self.base_dir, "logs", "imports")
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.config = self._load_config()
        self.logger = self._setup_logging()

    def _load_config(self) -> dict:
        default_config = {
            "host": "localhost",
            "port": 5432,
            "database": "tradenepse",
            "schema": "public",
            "batch_size": 5000,
            "import_enabled": True,
            "company_master_enabled": True,
            "daily_price_enabled": True,
            "indices_enabled": True,
            "floorsheet_enabled": True,
            "max_retries": 3,
            "log_imports": True,
            "test_mode": False
        }

        if not os.path.exists(self.config_path):
            return default_config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge defaults
                for k, v in default_config.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception:
            return default_config

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("import_manager")
        logger.setLevel(logging.INFO)

        # Clear existing handlers
        if logger.handlers:
            logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(console_handler)

        # File handler
        log_file = os.path.join(self.log_dir, "import_history.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)

        return logger

    def _get_connection(self):
        """
        Creates connection to PostgreSQL. Supports reading user/password from environment
        variables as DB_USER / DB_PASSWORD, with fallback keys in database_settings.json.
        """
        user = os.environ.get("DB_USER") or self.config.get("user") or "postgres"
        password = os.environ.get("DB_PASSWORD") or self.config.get("password") or ""
        
        conn_params = {
            "host": self.config.get("host", "localhost"),
            "port": self.config.get("port", 5432),
            "database": self.config.get("database", "tradenepse"),
            "user": user,
            "password": password
        }

        retries = int(self.config.get("max_retries", 3))
        for attempt in range(1, retries + 1):
            try:
                conn = psycopg2.connect(**conn_params)
                # Set schema
                schema = self.config.get("schema", "public")
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {schema}")
                return conn
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt}/{retries} failed: {e}")
                if attempt == retries:
                    raise ConnectionError(f"Could not connect to PostgreSQL after {retries} attempts: {e}")

    def _save_run_metrics(self, run_metrics: list):
        """
        Writes run metrics file to logs/imports/import_run_{timestamp}.json
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_file = os.path.join(self.log_dir, f"import_run_{timestamp}.json")
        try:
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "test_mode": self.config.get("test_mode", False),
                    "runs": run_metrics
                }, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to write run metrics JSON log: {e}")

    def run(self):
        """
        Main runner orchestrating the execution of active importers in dependency order.
        """
        self.logger.info("=========================================")
        self.logger.info("TradeNepse Ingestion Platform V2 Starting")
        self.logger.info("=========================================")

        if not self.config.get("import_enabled", True):
            self.logger.info("Ingestion is disabled in configuration. Exiting.")
            return

        test_mode = self.config.get("test_mode", False)
        batch_size = self.config.get("batch_size", 5000)

        if test_mode:
            self.logger.info("!!! TEST MODE IS ENABLED !!! (Only small samples will be imported)")

        run_metrics = []
        try:
            conn = self._get_connection()
        except Exception as e:
            self.logger.critical(f"Database connection failed. Ingestion aborted: {e}")
            return

        try:
            # 1. Company Master Importer
            if self.config.get("company_master_enabled", True):
                self.logger.info("-----------------------------------------")
                self.logger.info("1. Starting Company Master Import...")
                importer = CompanyMasterImporter(conn, batch_size=batch_size, test_mode=test_mode)
                file_path = os.path.join(self.base_dir, "data", "company_master", "company_master.json")
                if os.path.exists(file_path):
                    metrics = importer.import_data(file_path)
                    run_metrics.append(metrics)
                else:
                    self.logger.warning(f"Company master file not found at: {file_path}")

            # 2. Daily Price Importer
            if self.config.get("daily_price_enabled", True):
                self.logger.info("-----------------------------------------")
                self.logger.info("2. Starting Daily Price Import...")
                importer = DailyPriceImporter(conn, batch_size=batch_size, test_mode=test_mode)
                files = sorted(glob(os.path.join(self.base_dir, "data", "daily_price", "*.json")))
                
                if test_mode and len(files) > 2:
                    files = files[:2]
                    self.logger.info(f"Test Mode: Restricting Daily Price to first 2 files.")

                self.logger.info(f"Found {len(files)} daily price files to process.")
                for f_path in files:
                    metrics = importer.import_file(f_path)
                    run_metrics.append(metrics)

            # 3. Indices Importer
            if self.config.get("indices_enabled", True):
                self.logger.info("-----------------------------------------")
                self.logger.info("3. Starting Indices Import...")
                importer = IndicesImporter(conn, batch_size=batch_size, test_mode=test_mode)
                files = sorted(glob(os.path.join(self.base_dir, "data", "indices", "*.json")))
                # Skip the indices_master.json list file, as history is in index_id.json files
                files = [f for f in files if not os.path.basename(f) == "indices_master.json"]
                
                if test_mode and len(files) > 2:
                    files = files[:2]
                    self.logger.info(f"Test Mode: Restricting Indices to first 2 index files.")

                self.logger.info(f"Found {len(files)} historical index files to process.")
                for f_path in files:
                    metrics = importer.import_file(f_path)
                    run_metrics.append(metrics)

            # 4. Floorsheet Importer
            if self.config.get("floorsheet_enabled", True):
                self.logger.info("-----------------------------------------")
                self.logger.info("4. Starting Floorsheet Import...")
                importer = FloorsheetImporter(conn, batch_size=batch_size, test_mode=test_mode)
                files = sorted(glob(os.path.join(self.base_dir, "data", "floorsheet", "*.json")))
                
                if test_mode and len(files) > 1:
                    files = files[:1]
                    self.logger.info(f"Test Mode: Restricting Floorsheet to first 1 file.")

                self.logger.info(f"Found {len(files)} floorsheet files to process.")
                for f_path in files:
                    metrics = importer.import_file(f_path)
                    run_metrics.append(metrics)

        except Exception as e:
            self.logger.error(f"Ingestion lifecycle failed: {e}", exc_info=True)
        finally:
            conn.close()

        # Save metrics to JSON log
        if self.config.get("log_imports", True):
            self._save_run_metrics(run_metrics)

        # Print summary
        self.logger.info("=========================================")
        self.logger.info("Import Execution Complete Summary:")
        total_imported = sum(m["records_imported"] for m in run_metrics if m["status"] in ("Success", "Skipped"))
        success_count = sum(1 for m in run_metrics if m["status"] == "Success")
        skipped_count = sum(1 for m in run_metrics if m["status"] == "Skipped")
        failed_count = sum(1 for m in run_metrics if m["status"] == "Error")
        
        self.logger.info(f"  Total Files Processed: {len(run_metrics)}")
        self.logger.info(f"  Successful Syncs:      {success_count}")
        self.logger.info(f"  Skipped (Up-to-date):  {skipped_count}")
        self.logger.info(f"  Failed Operations:     {failed_count}")
        self.logger.info(f"  Total Records Loaded:  {total_imported}")
        self.logger.info("=========================================")
        self.logger.info("TradeNepse Ingestion Platform Completed")
        self.logger.info("=========================================")
