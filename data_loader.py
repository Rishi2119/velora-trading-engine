"""
Data Loader
Load market data from CSV files
"""

import pandas as pd


def load_csv(filepath):
    """
    Load market data from CSV file
    
    Expected columns: time, open, high, low, close, volume (optional)
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        DataFrame with market data
    """
    try:
        df = pd.read_csv(filepath)
        
        # Ensure required columns exist
        required = ['time', 'open', 'high', 'low', 'close']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return None
        
        # Convert time to datetime
        df['time'] = pd.to_datetime(df['time'])
        
        # Sort by time
        df = df.sort_values('time').reset_index(drop=True)
        
        print(f"✅ Loaded {len(df)} candles from {filepath}")
        
        return df
    
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def add_indicators(df):
    """
    Add technical indicators to dataframe
    
    Args:
        df: Market data dataframe
    
    Returns:
        DataFrame with indicators added
    """
    # You can add your indicators here
    # For now, just return the dataframe
    return df
