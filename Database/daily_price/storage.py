import sqlite3
import os
from typing import List, Optional
from daily_price.models import DailyPriceRecord

class DailyPriceStorage:
    """
    Handles SQLite storage for Daily Price records.
    Initializes the database, handles schema updates, queries the latest business date,
    and inserts records transactionally.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Create directory path if it does not exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection to the SQLite database with Row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes the database table and indexes if they do not exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS daily_prices (
            business_date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            previous_close REAL,
            volume INTEGER,
            turnover REAL,
            trades INTEGER,
            vwap REAL,
            last_price REAL,
            fifty_two_week_high REAL,
            fifty_two_week_low REAL,
            last_updated_time TEXT,
            PRIMARY KEY (business_date, symbol)
        );
        CREATE INDEX IF NOT EXISTS idx_business_date ON daily_prices (business_date);
        CREATE INDEX IF NOT EXISTS idx_symbol ON daily_prices (symbol);
        """
        with self._get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    def get_latest_business_date(self) -> Optional[str]:
        """
        Queries the database for the maximum business date stored.
        
        Returns:
            The latest business date as a string (YYYY-MM-DD), or None if the database has no records.
        """
        query = "SELECT MAX(business_date) as max_date FROM daily_prices"
        with self._get_connection() as conn:
            row = conn.execute(query).fetchone()
            if row and row["max_date"]:
                return str(row["max_date"])
        return None

    def save_records(self, records: List[DailyPriceRecord]) -> int:
        """
        Saves a batch of parsed DailyPriceRecord objects.
        Uses INSERT OR REPLACE to prevent duplicate records on (business_date, symbol).
        
        Args:
            records: List of DailyPriceRecord dataclass instances.
            
        Returns:
            The count of saved records.
        """
        if not records:
            return 0

        query = """
        INSERT OR REPLACE INTO daily_prices (
            business_date, symbol, company_name, open_price, high_price, low_price,
            close_price, previous_close, volume, turnover, trades, vwap,
            last_price, fifty_two_week_high, fifty_two_week_low, last_updated_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        data_tuples = [
            (
                r.business_date, r.symbol, r.company_name, r.open_price, r.high_price, r.low_price,
                r.close_price, r.previous_close, r.volume, r.turnover, r.trades, r.vwap,
                r.last_price, r.fifty_two_week_high, r.fifty_two_week_low, r.last_updated_time
            )
            for r in records
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data_tuples)
            conn.commit()
            return cursor.rowcount
