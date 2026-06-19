import pandas as pd

def calculate_summary_metrics(df, bulk_threshold=5000):
    """
    Computes summary cards values from the trades DataFrame.
    """
    if df.empty:
        return {
            "total_contracts": 0,
            "total_volume": 0.0,
            "total_turnover": 0.0,
            "total_bulk_transactions": 0,
            "largest_trade_quantity": 0,
            "largest_trade_value": 0.0
        }
        
    total_contracts = len(df)
    total_volume = float(df["contractQuantity"].sum())
    total_turnover = float(df["contractAmount"].sum())
    
    # Bulk trades count
    bulk_trades = df[df["contractQuantity"] >= bulk_threshold]
    total_bulk_transactions = len(bulk_trades)
    
    largest_trade_quantity = int(df["contractQuantity"].max())
    largest_trade_value = float(df["contractAmount"].max())
    
    return {
        "total_contracts": total_contracts,
        "total_volume": total_volume,
        "total_turnover": total_turnover,
        "total_bulk_transactions": total_bulk_transactions,
        "largest_trade_quantity": largest_trade_quantity,
        "largest_trade_value": largest_trade_value
    }

def get_hot_stocks_volume(df, limit=10):
    """
    Rank stocks by total contract quantity (volume).
    """
    if df.empty:
        return pd.DataFrame(columns=["Symbol", "Volume"])
    
    volume_df = df.groupby("stockSymbol")["contractQuantity"].sum().reset_index()
    volume_df.columns = ["Symbol", "Volume"]
    volume_df = volume_df.sort_values(by="Volume", ascending=False).head(limit)
    return volume_df

def get_hot_stocks_turnover(df, limit=10):
    """
    Rank stocks by total contract amount (turnover).
    """
    if df.empty:
        return pd.DataFrame(columns=["Symbol", "Turnover"])
        
    turnover_df = df.groupby("stockSymbol")["contractAmount"].sum().reset_index()
    turnover_df.columns = ["Symbol", "Turnover"]
    turnover_df = turnover_df.sort_values(by="Turnover", ascending=False).head(limit)
    return turnover_df

def get_hot_stocks_bulk_transactions(df, bulk_threshold=5000, limit=10):
    """
    Rank stocks by number of bulk transactions.
    """
    if df.empty:
        return pd.DataFrame(columns=["Symbol", "Bulk Transactions"])
        
    bulk_df = df[df["contractQuantity"] >= bulk_threshold]
    if bulk_df.empty:
        return pd.DataFrame(columns=["Symbol", "Bulk Transactions"])
        
    ranks_df = bulk_df.groupby("stockSymbol").size().reset_index()
    ranks_df.columns = ["Symbol", "Bulk Transactions"]
    ranks_df = ranks_df.sort_values(by="Bulk Transactions", ascending=False).head(limit)
    return ranks_df

def filter_bulk_trades(df, bulk_threshold=5000):
    """
    Returns only trades that meet or exceed the bulk threshold.
    """
    if df.empty:
        return df
    return df[df["contractQuantity"] >= bulk_threshold]
