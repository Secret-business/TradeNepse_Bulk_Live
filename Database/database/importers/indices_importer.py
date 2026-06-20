import os
import json
import logging
from datetime import datetime
from psycopg2.extras import execute_values

logger = logging.getLogger("import_manager")

class IndicesImporter:
    """
    Importer responsible for loading historical indices JSON files into PostgreSQL.
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

    def get_existing_dates(self, index_id) -> set:
        """
        Fetches all business_dates already imported for the given index_id.
        """
        query = "SELECT business_date FROM indices WHERE index_id = %s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (index_id,))
                return {row[0] for row in cur.fetchall()}
        except Exception as e:
            logger.error(f"Error fetching indices existing dates: {e}")
            return set()

    def import_file(self, file_path) -> dict:
        """
        Imports a single index history JSON file (e.g., 58.json).
        """
        start_time = datetime.now()
        filename = os.path.basename(file_path)
        index_id_str = os.path.splitext(filename)[0]
        records_imported = 0
        status = "Success"
        error_message = None

        try:
            index_id = int(index_id_str)
            existing_dates = self.get_existing_dates(index_id)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError(f"Expected list in index file {filename}, got {type(data)}")

            records = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                b_date = self._parse_date(item.get("business_date"))
                if not b_date:
                    continue

                # Skip if already imported
                if b_date in existing_dates:
                    continue

                if self.test_mode and len(records) >= 10:
                    break

                record = (
                    b_date,
                    index_id,
                    item.get("index_name", "UNKNOWN"),
                    item.get("open_index"),
                    item.get("high_index"),
                    item.get("low_index"),
                    item.get("closing_index"),
                    item.get("fifty_two_week_high"),
                    item.get("fifty_two_week_low"),
                    item.get("turnover_value"),
                    item.get("turnover_volume"),
                    item.get("total_transaction"),
                    item.get("abs_change"),
                    item.get("percentage_change")
                )
                records.append(record)

            if records:
                query = """
                    INSERT INTO indices (
                        business_date, index_id, index_name, open_index, high_index, 
                        low_index, closing_index, fifty_two_week_high, fifty_two_week_low, 
                        turnover_value, turnover_volume, total_transaction, abs_change, 
                        percentage_change
                    ) VALUES %s
                    ON CONFLICT (business_date, index_id) DO UPDATE SET
                        index_name = EXCLUDED.index_name,
                        open_index = EXCLUDED.open_index,
                        high_index = EXCLUDED.high_index,
                        low_index = EXCLUDED.low_index,
                        closing_index = EXCLUDED.closing_index,
                        fifty_two_week_high = EXCLUDED.fifty_two_week_high,
                        fifty_two_week_low = EXCLUDED.fifty_two_week_low,
                        turnover_value = EXCLUDED.turnover_value,
                        turnover_volume = EXCLUDED.turnover_volume,
                        total_transaction = EXCLUDED.total_transaction,
                        abs_change = EXCLUDED.abs_change,
                        percentage_change = EXCLUDED.percentage_change
                """
                with self.conn.cursor() as cur:
                    execute_values(cur, query, records)
                self.conn.commit()
                records_imported = len(records)
                logger.info(f"Imported {records_imported} new index records for index ID {index_id_str}.")
            else:
                logger.info(f"No new records to import for index ID {index_id_str}.")

        except Exception as e:
            self.conn.rollback()
            status = "Error"
            error_message = str(e)
            logger.error(f"Error importing index file {filename}: {e}", exc_info=True)

        duration = (datetime.now() - start_time).total_seconds()
        return {
            "source": f"indices_{index_id_str}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "records_imported": records_imported,
            "duration": duration,
            "status": status,
            "error_message": error_message
        }
