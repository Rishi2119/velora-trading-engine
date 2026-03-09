"""
Download M15 Data for Multiple Pairs from MT5
Run this script to download historical data for all your trading pairs
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

# =========================
# SETTINGS
# =========================

# Pairs to download
PAIRS = [
    "EURUSD",
    "USDCAD",
    "GBPUSD",
    "USDCHF",
    "NZDUSD"
]

# Timeframe
TIMEFRAME = mt5.TIMEFRAME_M15  # 15-minute candles

# How much data (days)
DAYS_OF_DATA = 365  # 1 year

# Output directory
OUTPUT_DIR = "data"

# =========================
# DOWNLOAD FUNCTION
# =========================

def download_pair_data(symbol, timeframe, days):
    """Download historical data for a symbol"""
    print(f"\nDownloading {symbol}...")
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Request data
    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    
    if rates is None or len(rates) == 0:
        print(f"   ❌ Failed to get data for {symbol}")
        print(f"   Error: {mt5.last_error()}")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Select columns
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    print(f"   ✅ Downloaded {len(df)} candles")
    print(f"   Period: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
    
    return df

# =========================
# MAIN
# =========================

def main():
    print("="*80)
    print("📥 MT5 Data Downloader for Multiple Pairs")
    print("="*80)
    
    # Initialize MT5
    print("\n🔌 Connecting to MT5...")
    
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        print("\nMake sure:")
        print("  1. MT5 terminal is open")
        print("  2. You're logged into an account")
        return
    
    print("✅ Connected to MT5")
    
    # Account info
    account_info = mt5.account_info()
    if account_info:
        print(f"   Account: {account_info.login}")
        print(f"   Server: {account_info.server}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n📁 Output directory: {OUTPUT_DIR}/")
    
    # Download each pair
    print(f"\n📊 Downloading {len(PAIRS)} pairs ({DAYS_OF_DATA} days of data each)...")
    
    success_count = 0
    
    for symbol in PAIRS:
        df = download_pair_data(symbol, TIMEFRAME, DAYS_OF_DATA)
        
        if df is not None:
            # Save to CSV
            filename = f"{OUTPUT_DIR}/{symbol}_M15.csv"
            df.to_csv(filename, index=False)
            print(f"   💾 Saved to: {filename}")
            success_count += 1
        
        # Small delay between requests
        import time
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("📊 DOWNLOAD SUMMARY")
    print("="*80)
    print(f"✅ Successfully downloaded: {success_count}/{len(PAIRS)} pairs")
    
    if success_count < len(PAIRS):
        print(f"❌ Failed: {len(PAIRS) - success_count} pairs")
        print("\nFailed pairs may not be available on your broker.")
        print("Check symbol names in MT5 (they might be slightly different)")
    
    print("\n✅ Download complete!")
    print(f"\nYour data files are in: {OUTPUT_DIR}/")
    print("\nYou can now run the trading system:")
    print("  python multi_pair_runner.py")
    
    # Shutdown MT5
    mt5.shutdown()
    print("\nMT5 disconnected")

if __name__ == "__main__":
    main()
