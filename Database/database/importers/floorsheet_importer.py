import os
import json
import logging
from datetime import datetime
from psycopg2.extras import execute_values

logger = logging.getLogger("import_manager")

class FloorsheetImporter:
    """
    Importer responsible for loading floorsheet JSON files into PostgreSQL.
    """

    def __init__(self, conn, batch_size=5000, test_mode=False):
        self.conn = conn
        self.batch_size = batch_size
        self.test_mode = test_mode

    def _parse_date(self, val):
        if not val:
            return None
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _parse_timestamp(self, val):
        if not val:
            return None
        try:
            # ISO timestamp e.g. "2026-06-19T10:46:00.015045Z"
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None

    def is_already_imported(self, business_date) -> bool:
        """
        Resume check: checks if any records exist in floorsheet for the given business_date.
        """
        query = "SELECT 1 FROM floorsheet WHERE business_date = %s LIMIT 1"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (business_date,))
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking floorsheet resume state: {e}")
            return False

    def import_file(self, file_path) -> dict:
        """
        Imports a single daily floorsheet YYYY-MM-DD.json file.
        """
        start_time = datetime.now()
        filename = os.path.basename(file_path)
        date_str = os.path.splitext(filename)[0]
        records_imported = 0
        status = "Success"
        error_message = None

        try:
            business_date = self._parse_date(date_str)
            if not business_date:
                raise ValueError(f"Invalid date format in file name: {filename}")

            if self.is_already_imported(business_date):
                logger.info(f"Floorsheet date {date_str} already imported. Skipping (Resume check).")
                return {
                    "source": "floorsheet",
                    "date": date_str,
                    "records_imported": 0,
                    "duration": 0.0,
                    "status": "Skipped",
                    "error_message": None
                }

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(f"Expected list in floorsheet file {filename}, got {type(data)}")

            records = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                if self.test_mode and len(records) >= 100:
                    logger.info("Test mode enabled: limiting floorsheet import to 100 records.")
                    break

                b_date = self._parse_date(item.get("business_date")) or business_date
                contract_id = item.get("contract_id")
                if contract_id is not None:
                    contract_id = int(contract_id)
                else:
                    continue  # contract_id is primary key component

                trade_time = self._parse_timestamp(item.get("trade_time"))
                if not trade_time:
                    continue

                record = (
                    contract_id,
                    b_date,
                    item.get("symbol"),
                    item.get("company_name"),
                    item.get("buyer_broker_id"),
                    item.get("seller_broker_id"),
                    item.get("buyer_broker_name"),
                    item.get("seller_broker_name"),
                    item.get("quantity"),
                    item.get("rate"),
                    item.get("amount"),
                    trade_time
                )
                records.append(record)

            if records:
                query = """
                    INSERT INTO floorsheet (
                        contract_id, business_date, symbol, company_name, buyer_broker_id, 
                        seller_broker_id, buyer_broker_name, seller_broker_name, 
                        quantity, rate, amount, trade_time
                    ) VALUES %s
                    ON CONFLICT (contract_id, business_date) DO NOTHING
                """
                # Insert in chunks to avoid blocking database and keeping memory low
                with self.conn.cursor() as cur:
                    for i in range(0, len(records), self.batch_size):
                        chunk = records[i:i + self.batch_size]
                        execute_values(cur, query, chunk)
                self.conn.commit()
                records_imported = len(records)
                logger.info(f"Imported {records_imported} floorsheet records for date {date_str}.")
            else:
                logger.info(f"No records found to import for date {date_str}.")

        except Exception as e:
            self.conn.rollback()
            status = "Error"
            error_message = str(e)
            logger.error(f"Error importing floorsheet file {filename}: {e}", exc_info=True)

        duration = (datetime.now() - start_time).total_seconds()
        return {
            "source": "floorsheet",
            "date": date_str,
            "records_imported": records_imported,
            "duration": duration,
            "status": status,
            "error_message": error_message
        }
