import json
import logging
from datetime import datetime
from psycopg2.extras import execute_values

logger = logging.getLogger("import_manager")

class CompanyMasterImporter:
    """
    Importer responsible for loading company_master JSON data into PostgreSQL.
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
            try:
                # Fallback for ISO format with time
                return datetime.fromisoformat(val.replace("Z", "+00:00")).date()
            except ValueError:
                return None

    def _parse_timestamp(self, val):
        if not val:
            return datetime.now()
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()

    def import_data(self, file_path) -> dict:
        """
        Imports company master from consolidated JSON file.
        Returns a dict containing metrics about the run.
        """
        start_time = datetime.now()
        records_imported = 0
        status = "Success"
        error_message = None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object (dict) in company master file, got {type(data)}")

            records = []
            for sec_id_str, record_dict in data.items():
                # In test_mode, we still import all company profiles (~380 records) 
                # because daily_price testing files contain foreign keys referencing them.
                # Satisfying foreign key constraints is required for daily_price tests.

                sec_id = int(sec_id_str)
                listing_date = self._parse_date(record_dict.get("listing_date"))
                updated_date = self._parse_timestamp(record_dict.get("updated_date"))

                record = (
                    sec_id,
                    record_dict.get("symbol"),
                    record_dict.get("security_name"),
                    record_dict.get("sector"),
                    listing_date,
                    record_dict.get("isin"),
                    record_dict.get("stock_listed_shares"),
                    record_dict.get("public_shares"),
                    record_dict.get("public_percentage"),
                    record_dict.get("promoter_shares"),
                    record_dict.get("promoter_percentage"),
                    record_dict.get("paid_up_capital"),
                    record_dict.get("issued_capital"),
                    record_dict.get("market_capitalization"),
                    updated_date
                )
                records.append(record)

            if records:
                query = """
                    INSERT INTO company_master (
                        security_id, symbol, security_name, sector, listing_date, isin, 
                        stock_listed_shares, public_shares, public_percentage, 
                        promoter_shares, promoter_percentage, paid_up_capital, 
                        issued_capital, market_capitalization, updated_date
                    ) VALUES %s
                    ON CONFLICT (security_id) DO UPDATE SET
                        symbol = EXCLUDED.symbol,
                        security_name = EXCLUDED.security_name,
                        sector = EXCLUDED.sector,
                        listing_date = EXCLUDED.listing_date,
                        isin = EXCLUDED.isin,
                        stock_listed_shares = EXCLUDED.stock_listed_shares,
                        public_shares = EXCLUDED.public_shares,
                        public_percentage = EXCLUDED.public_percentage,
                        promoter_shares = EXCLUDED.promoter_shares,
                        promoter_percentage = EXCLUDED.promoter_percentage,
                        paid_up_capital = EXCLUDED.paid_up_capital,
                        issued_capital = EXCLUDED.issued_capital,
                        market_capitalization = EXCLUDED.market_capitalization,
                        updated_date = EXCLUDED.updated_date
                """
                with self.conn.cursor() as cur:
                    execute_values(cur, query, records)
                self.conn.commit()
                records_imported = len(records)
                logger.info(f"Successfully upserted {records_imported} company master records.")
            else:
                logger.info("No company master records found to import.")

        except Exception as e:
            self.conn.rollback()
            status = "Error"
            error_message = str(e)
            logger.error(f"Error importing company master: {e}", exc_info=True)

        duration = (datetime.now() - start_time).total_seconds()
        return {
            "source": "company_master",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "records_imported": records_imported,
            "duration": duration,
            "status": status,
            "error_message": error_message
        }
