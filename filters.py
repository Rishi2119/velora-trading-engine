"""
Trading Filters
Session, news, and other filters
"""

from datetime import datetime, time
import os


def is_trading_session(candle_time):
    """
    Check if time is within trading sessions
    
    Args:
        candle_time: Datetime or string
    
    Returns:
        True if within London or NY session
    """
    if isinstance(candle_time, str):
        candle_time = datetime.fromisoformat(candle_time)
    
    current_time = candle_time.time()
    
    # London session: 08:00 - 16:00 GMT
    london_start = time(8, 0)
    london_end = time(16, 0)
    
    # New York session: 13:00 - 21:00 GMT
    ny_start = time(13, 0)
    ny_end = time(21, 0)
    
    in_london = london_start <= current_time <= london_end
    in_ny = ny_start <= current_time <= ny_end
    
    return in_london or in_ny


def is_kill_switch_active():
    """
    Check if kill switch file exists
    
    Returns:
        True if KILL_SWITCH.txt exists
    """
    return os.path.exists("KILL_SWITCH.txt")


def load_news():
    """Load news events (placeholder)"""
    # Return empty dataframe - you can add news loading here
    import pandas as pd
    return pd.DataFrame()


def is_news_blocked(candle_time, news_df):
    """Check if news blocks trading (placeholder)"""
    # No news filtering for now
    return False, None


def detect_regime(df):
    """
    Detect market regime (placeholder)
    
    Returns:
        regime, allowed, reason
    """
    # Simple regime: allow all for now
    return "TRENDING", True, "Market trending"
