import os
import json
import logging
from datetime import datetime
from psycopg2.extras import execute_values

logger = logging.getLogger("import_manager")

class DailyPriceImporter:
    """
    Importer responsible for loading daily price JSON files into PostgreSQL.
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
            # ISO timestamp e.g. "2026-06-19T14:59:38.013793"
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None

    def is_already_imported(self, business_date) -> bool:
        """
        Resume check: checks if the date has already been imported into daily_price.
        """
        query = "SELECT 1 FROM daily_price WHERE business_date = %s LIMIT 1"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (business_date,))
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking daily_price resume state: {e}")
            return False

    def import_file(self, file_path) -> dict:
        """
        Imports a single daily price YYYY-MM-DD.json file.
        """
        start_time = datetime.now()
        filename = os.path.basename(file_path)
        date_str = os.path.splitext(filename)[0]
        records_imported = 0
        status = "Success"
        error_message = None

        try:
            # Check if already imported
            business_date = self._parse_date(date_str)
            if not business_date:
                raise ValueError(f"Invalid date format in file name: {filename}")

            if self.is_already_imported(business_date):
                logger.info(f"Daily Price date {date_str} already imported. Skipping (Resume check).")
                return {
                    "source": "daily_price",
                    "date": date_str,
                    "records_imported": 0,
                    "duration": 0.0,
                    "status": "Skipped",
                    "error_message": None
                }

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError(f"Expected dict in file {filename}, got {type(data)}")

            content = data.get("content", [])
            if not isinstance(content, list):
                logger.warning(f"No content list in file {filename}. Skipping.")
                return {
                    "source": "daily_price",
                    "date": date_str,
                    "records_imported": 0,
                    "duration": 0.0,
                    "status": "No Data",
                    "error_message": None
                }

            records = []
            for item in content:
                if not isinstance(item, dict):
                    continue

                if self.test_mode and len(records) >= 10:
                    break

                # Fields normalization
                b_date = self._parse_date(item.get("businessDate")) or business_date
                sec_id = item.get("securityId")
                if sec_id is not None:
                    sec_id = int(sec_id)

                symbol = item.get("symbol")
                if not symbol:
                    continue  # Symbol is critical primary key

                last_updated_time = self._parse_timestamp(item.get("lastUpdatedTime"))

                record = (
                    b_date,
                    sec_id,
                    symbol,
                    item.get("securityName", "UNKNOWN"),
                    item.get("openPrice"),
                    item.get("highPrice"),
                    item.get("lowPrice"),
                    item.get("closePrice"),
                    item.get("previousDayClosePrice"),
                    item.get("totalTradedQuantity"),
                    item.get("totalTradedValue"),
                    item.get("totalTrades"),
                    item.get("averageTradedPrice"),
                    item.get("lastUpdatedPrice"),
                    item.get("fiftyTwoWeekHigh"),
                    item.get("fiftyTwoWeekLow"),
                    last_updated_time
                )
                records.append(record)

            if records:
                query = """
                    INSERT INTO daily_price (
                        business_date, security_id, symbol, company_name, open_price, 
                        high_price, low_price, close_price, previous_close, volume, 
                        turnover, trades, vwap, last_price, fifty_two_week_high, 
                        fifty_two_week_low, last_updated_time
                    ) VALUES %s
                    ON CONFLICT (business_date, symbol) DO UPDATE SET
                        security_id = EXCLUDED.security_id,
                        company_name = EXCLUDED.company_name,
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        previous_close = EXCLUDED.previous_close,
                        volume = EXCLUDED.volume,
                        turnover = EXCLUDED.turnover,
                        trades = EXCLUDED.trades,
                        vwap = EXCLUDED.vwap,
                        last_price = EXCLUDED.last_price,
                        fifty_two_week_high = EXCLUDED.fifty_two_week_high,
                        fifty_two_week_low = EXCLUDED.fifty_two_week_low,
                        last_updated_time = EXCLUDED.last_updated_time
                """
                with self.conn.cursor() as cur:
                    execute_values(cur, query, records)
                self.conn.commit()
                records_imported = len(records)
                logger.info(f"Imported {records_imported} daily price records for date {date_str}.")
            else:
                logger.info(f"No records found to import for date {date_str}.")

        except Exception as e:
            self.conn.rollback()
            status = "Error"
            error_message = str(e)
            logger.error(f"Error importing daily price file {filename}: {e}", exc_info=True)

        duration = (datetime.now() - start_time).total_seconds()
        return {
            "source": "daily_price",
            "date": date_str,
            "records_imported": records_imported,
            "duration": duration,
            "status": status,
            "error_message": error_message
        }
