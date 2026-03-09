"""
Multi-Pair Trading System Configuration
Trade multiple currency pairs simultaneously
"""

# =========================
# ACCOUNT SETTINGS
# =========================
ACCOUNT_BALANCE = 500           # $500 account
RISK_PER_TRADE = 0.01          # Risk 1% per trade ($5 per trade)
MIN_RISK_REWARD = 2.0          # Minimum 2:1 RR

# =========================
# TRADING PAIRS
# =========================
TRADING_PAIRS = [
    {
        'symbol': 'EURUSD',
        'data_file': 'data/EURUSD_M15.csv',
        'enabled': True
    },
    {
        'symbol': 'USDCAD',
        'data_file': 'data/USDCAD_M15.csv',
        'enabled': True
    },
    {
        'symbol': 'GBPUSD',
        'data_file': 'data/GBPUSD_M15.csv',
        'enabled': True
    },
    {
        'symbol': 'USDCHF',
        'data_file': 'data/USDCHF_M15.csv',
        'enabled': True
    },
    {
        'symbol': 'NZDUSD',
        'data_file': 'data/NZDUSD_M15.csv',
        'enabled': True
    }
]

# Legacy support (for old code that uses SYMBOL and DATA_FILE)
SYMBOL = TRADING_PAIRS[0]['symbol']
DATA_FILE = TRADING_PAIRS[0]['data_file']

# =========================
# MULTI-PAIR SETTINGS
# =========================
MAX_TRADES_PER_PAIR = 1         # Max 1 trade per pair at a time
MAX_TOTAL_TRADES = 5            # Max 3 trades across all pairs
RISK_PER_PAIR = 0.01           # 1% risk per pair (or split total risk)
SPLIT_RISK_ACROSS_PAIRS = True # If True, splits 1% across all active trades

# =========================
# EXECUTION SETTINGS
# =========================
ENABLE_EXECUTION = True        # ⚠️ Keep FALSE for testing
MAGIC_NUMBER = 234000

# MT5 Login (optional)
MT5_ACCOUNT = 5046125612
MT5_PASSWORD = P@LoQr8m
MT5_SERVER = MetaQuotes-Demo

# =========================
# RISK MANAGEMENT
# =========================
MAX_DAILY_LOSS = 50            # Stop after $50 loss (10% of account)
MAX_DAILY_TRADES = 15          # Max 15 trades per day (all pairs)
MAX_CONCURRENT_TRADES = 3      # Max 3 open positions total
MAX_POSITION_SIZE = 2.0        # Max 2 lots per trade

# =========================
# S/R STRATEGY SETTINGS
# =========================
USE_SR_STRATEGY = True
SR_LOOKBACK = 100              # Candles to check for S/R zones
SR_ZONE_TOLERANCE = 0.0002     # Zone width (20 pips)
SR_MIN_RR = 2.0               # Minimum 2:1 RR

# =========================
# INDICATORS
# =========================
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_BUY_MIN = 40              # Don't buy if RSI < 40
RSI_SELL_MAX = 60             # Don't sell if RSI > 60

EMA_FAST = 50
EMA_SLOW = 200

# =========================
# TRADING FILTERS
# =========================
ENABLE_SESSION_FILTER = False
ALLOWED_SESSIONS = ["LONDON", "NEW_YORK"]

ENABLE_NEWS_FILTER = False     # Disable for now
NEWS_BUFFER_MINUTES = 30

ENABLE_REGIME_FILTER = False   # Disable for now
BLOCKED_REGIMES = ["CHOPPY"]

# =========================
# SAFETY FEATURES
# =========================
ENABLE_KILL_SWITCH = True
KILL_SWITCH_FILE = "KILL_SWITCH.txt"

PREVENT_DUPLICATE_TRADES = True
MIN_CANDLES_BETWEEN_TRADES = 3

# =========================
# LOGGING
# =========================
LOG_DIRECTORY = "logs"
TRADE_JOURNAL_FILE = "logs/trade_journal.csv"
PERFORMANCE_FILE = "logs/performance.json"

ENABLE_CONSOLE_LOGGING = True
SHOW_DETAILED_LOGS = True

# =========================
# COMPATIBILITY
# =========================
RSI_RANGE = (RSI_OVERSOLD, RSI_OVERBOUGHT)
MIN_RR = MIN_RISK_REWARD
BALANCE = ACCOUNT_BALANCE
RISK_PCT = RISK_PER_TRADE

# =========================
# VALIDATION
# =========================
def validate_config():
    """Validate configuration"""
    errors = []
    
    if ACCOUNT_BALANCE <= 0:
        errors.append("ACCOUNT_BALANCE must be positive")
    
    if RISK_PER_TRADE <= 0 or RISK_PER_TRADE > 0.05:
        errors.append("RISK_PER_TRADE must be between 0 and 0.05 (5%)")
    
    if MAX_DAILY_LOSS > ACCOUNT_BALANCE * 0.2:
        errors.append(f"MAX_DAILY_LOSS (${MAX_DAILY_LOSS}) too high for ${ACCOUNT_BALANCE} account")
    
    # Check data files exist
    import os
    for pair in TRADING_PAIRS:
        if pair['enabled'] and not os.path.exists(pair['data_file']):
            errors.append(f"Data file not found: {pair['data_file']}")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


def print_config():
    """Print configuration"""
    print("\n" + "="*80)
    print("⚙️  MULTI-PAIR TRADING SYSTEM CONFIGURATION")
    print("="*80)
    
    print(f"\n💰 Account:")
    print(f"   Balance: ${ACCOUNT_BALANCE}")
    print(f"   Risk per Trade: {RISK_PER_TRADE*100}% (${ACCOUNT_BALANCE * RISK_PER_TRADE})")
    print(f"   Max Daily Loss: ${MAX_DAILY_LOSS} ({MAX_DAILY_LOSS/ACCOUNT_BALANCE*100:.1f}%)")
    
    print(f"\n📊 Trading Pairs ({sum(1 for p in TRADING_PAIRS if p['enabled'])} enabled):")
    for pair in TRADING_PAIRS:
        status = "✅" if pair['enabled'] else "❌"
        print(f"   {status} {pair['symbol']}")
    
    print(f"\n🎯 Strategy:")
    print(f"   S/R Rejection: {'ON' if USE_SR_STRATEGY else 'OFF'}")
    print(f"   Min RR: {MIN_RISK_REWARD}:1")
    
    print(f"\n🛡️  Risk Limits:")
    print(f"   Max Daily Loss: ${MAX_DAILY_LOSS}")
    print(f"   Max Daily Trades: {MAX_DAILY_TRADES}")
    print(f"   Max Total Concurrent: {MAX_CONCURRENT_TRADES}")
    print(f"   Max Per Pair: {MAX_TRADES_PER_PAIR}")
    
    print(f"\n⚡ Execution:")
    print(f"   Live Trading: {'⚠️ ENABLED' if ENABLE_EXECUTION else '✅ DISABLED (SAFE)'}")
    
    print("="*80 + "\n")


def get_enabled_pairs():
    """Get list of enabled trading pairs"""
    return [p for p in TRADING_PAIRS if p['enabled']]


if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration is valid")
        print_config()
    else:
        print("❌ Please fix configuration errors")
