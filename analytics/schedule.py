from datetime import datetime, time, timedelta
import pytz
from settings.config import load_settings

def market_is_open():
    """
    Returns True if current local Nepal time falls within configured trading days and hours,
    and Holiday Mode is disabled. Supports forced state overrides.
    """
    settings = load_settings()
    
    # Forced state checks
    if settings.get("force_market_closed", False):
        return False
    if settings.get("force_market_open", False):
        return True
        
    if settings.get("holiday_mode", False):
        return False
        
    tz_name = settings.get("timezone", "Asia/Kathmandu")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("Asia/Kathmandu")
        
    now_tz = datetime.now(tz)
    
    # Check weekday
    weekday = now_tz.weekday() # 0 = Monday, 6 = Sunday
    trading_days = settings.get("trading_days", [0, 1, 2, 3, 4, 6])
    if weekday not in trading_days:
        return False
        
    # Check hours
    open_str = settings.get("market_open", "11:01")
    close_str = settings.get("market_close", "15:05")
    
    try:
        open_time = datetime.strptime(open_str, "%H:%M").time()
        close_time = datetime.strptime(close_str, "%H:%M").time()
    except Exception:
        open_time = time(11, 1)
        close_time = time(15, 5)
        
    current_time = now_tz.time()
    return open_time <= current_time <= close_time

def get_next_market_open():
    """
    Looks ahead (up to 7 days) and returns the datetime of the next opening market session.
    Returns None if holiday mode is active, market is forced open/closed, or no trading days are configured.
    """
    settings = load_settings()
    if settings.get("holiday_mode", False):
        return None
        
    tz_name = settings.get("timezone", "Asia/Kathmandu")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("Asia/Kathmandu")
        
    now_tz = datetime.now(tz)
    
    open_str = settings.get("market_open", "11:01")
    try:
        open_time = datetime.strptime(open_str, "%H:%M").time()
    except Exception:
        open_time = time(11, 1)
        
    trading_days = settings.get("trading_days", [0, 1, 2, 3, 4, 6])
    if not trading_days:
        return None
        
    # Start checking from today's date
    check_date = now_tz.date()
    
    # If today's time has already passed opening, look forward starting tomorrow
    if now_tz.time() >= open_time:
        check_date += timedelta(days=1)
        
    for _ in range(8):
        if check_date.weekday() in trading_days:
            next_open = datetime.combine(check_date, open_time)
            next_open = tz.localize(next_open)
            return next_open
        check_date += timedelta(days=1)
            
    return None

def get_next_market_close():
    """
    Looks ahead (up to 7 days) and returns the datetime of the next closing market session.
    Returns None if no trading days are configured.
    """
    settings = load_settings()
    tz_name = settings.get("timezone", "Asia/Kathmandu")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("Asia/Kathmandu")
        
    now_tz = datetime.now(tz)
    
    close_str = settings.get("market_close", "15:05")
    try:
        close_time = datetime.strptime(close_str, "%H:%M").time()
    except Exception:
        close_time = time(15, 5)
        
    trading_days = settings.get("trading_days", [0, 1, 2, 3, 4, 6])
    if not trading_days:
        return None
        
    # Start checking from today's date
    check_date = now_tz.date()
    
    # If today's time has already passed closing, look forward starting tomorrow
    if now_tz.time() >= close_time:
        check_date += timedelta(days=1)
        
    for _ in range(8):
        if check_date.weekday() in trading_days:
            next_close = datetime.combine(check_date, close_time)
            next_close = tz.localize(next_close)
            return next_close
        check_date += timedelta(days=1)
            
    return None

def get_market_status():
    """
    Returns a formatted string representing the current NEPSE market status,
    optionally including the next opening time if closed. Supports overrides.
    """
    settings = load_settings()
    
    # Respect forced overrides first
    if settings.get("force_market_closed", False):
        return "🔴 Market Closed (Forced)"
    if settings.get("force_market_open", False):
        return "🟢 Market Open (Forced)"
        
    if settings.get("holiday_mode", False):
        return "🔴 Holiday / Market Closed"
        
    if market_is_open():
        return "🟢 Market Open"
        
    next_open = get_next_market_open()
    if next_open:
        next_open_str = next_open.strftime("%a %I:%M %p")
        return f"🔴 Market Closed (Opens {next_open_str})"
    
    return "🔴 Market Closed"
