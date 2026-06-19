from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DailyPriceRecord:
    """
    Data model representing a single daily stock price record.
    Contains clean type hints and maps to the SQLite database storage schema.
    """
    business_date: str          # YYYY-MM-DD
    symbol: str                 # Stock symbol (e.g. ACLBSL)
    company_name: str           # Full security name
    open_price: float           # Opening price
    high_price: float           # Highest price of the day
    low_price: float            # Lowest price of the day
    close_price: float          # Closing price
    previous_close: float       # Previous trading day's closing price
    volume: int                 # Total traded shares quantity
    turnover: float             # Total traded turnover value
    trades: int                 # Total transactions count
    vwap: float                 # Volume Weighted Average Price (averageTradedPrice)
    last_price: float           # Last updated transaction price
    fifty_two_week_high: float  # 52 week high price
    fifty_two_week_low: float   # 52 week low price
    last_updated_time: str      # Time string when record was last updated

    @classmethod
    def from_api_json(cls, data: Dict[str, Any]) -> "DailyPriceRecord":
        """
        Creates a DailyPriceRecord instance from the API response dictionary.
        Extracts values, handles default values for missing keys, and converts types.
        """
        return cls(
            business_date=str(data.get("businessDate", "")),
            symbol=str(data.get("symbol", "")),
            company_name=str(data.get("securityName", "")),
            open_price=float(data.get("openPrice") or 0.0),
            high_price=float(data.get("highPrice") or 0.0),
            low_price=float(data.get("lowPrice") or 0.0),
            close_price=float(data.get("closePrice") or 0.0),
            previous_close=float(data.get("previousDayClosePrice") or 0.0),
            volume=int(data.get("totalTradedQuantity") or 0),
            turnover=float(data.get("totalTradedValue") or 0.0),
            trades=int(data.get("totalTrades") or 0),
            vwap=float(data.get("averageTradedPrice") or 0.0),
            last_price=float(data.get("lastUpdatedPrice") or 0.0),
            fifty_two_week_high=float(data.get("fiftyTwoWeekHigh") or 0.0),
            fifty_two_week_low=float(data.get("fiftyTwoWeekLow") or 0.0),
            last_updated_time=str(data.get("lastUpdatedTime", ""))
        )
