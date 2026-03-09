"""
HIGH RISK / HIGH REWARD Configuration
For aggressive traders seeking maximum returns
⚠️ WARNING: Higher risk = higher potential losses
"""

# =========================
# ACCOUNT SETTINGS
# =========================
ACCOUNT_BALANCE = 500
RISK_PER_TRADE = 0.03           # 3% risk per trade (AGGRESSIVE!)
MIN_RISK_REWARD = 3.0           # Minimum 3:1 RR (HIGH REWARD)

# =========================
# TRADING PAIRS
# =========================
TRADING_PAIRS = [
    {'symbol': 'EURUSD', 'data_file': 'data/EURUSD_M15.csv', 'enabled': True},
    {'symbol': 'USDCAD', 'data_file': 'data/USDCAD_M15.csv', 'enabled': True},
    {'symbol': 'GBPUSD', 'data_file': 'data/GBPUSD_M15.csv', 'enabled': True},
    {'symbol': 'USDCHF', 'data_file': 'data/USDCHF_M15.csv', 'enabled': True},
    {'symbol': 'NZDUSD', 'data_file': 'data/NZDUSD_M15.csv', 'enabled': True}
]

SYMBOL = TRADING_PAIRS[0]['symbol']
DATA_FILE = TRADING_PAIRS[0]['data_file']

# =========================
# AGGRESSIVE SETTINGS
# =========================
MAX_TRADES_PER_PAIR = 2         # Up to 2 trades per pair
MAX_TOTAL_TRADES = 5            # Up to 5 trades total (AGGRESSIVE)
SPLIT_RISK_ACROSS_PAIRS = False # Each trade risks full 3%

# =========================
# EXECUTION
# =========================
ENABLE_EXECUTION = False        # ⚠️ Keep FALSE for testing
MAGIC_NUMBER = 234000

# =========================
# RISK MANAGEMENT (Adjusted for aggressive)
# =========================
MAX_DAILY_LOSS = 150            # $150 max daily loss (30% of account!)
MAX_DAILY_TRADES = 20           # More trades allowed
MAX_CONCURRENT_TRADES = 5       # Up to 5 concurrent
MAX_POSITION_SIZE = 5.0         # Larger positions allowed

# =========================
# STRATEGY SELECTION
# =========================
USE_AGGRESSIVE_STRATEGY = True
USE_SR_STRATEGY = False         # Disable conservative strategy
USE_BOTH_STRATEGIES = False

# Aggressive Strategy Priority
ENABLE_VOLATILITY_BREAKOUT = True    # Highest risk/reward
ENABLE_LONDON_BREAKOUT = True        # High risk/reward
ENABLE_AGGRESSIVE_TREND = True       # Medium-high risk/reward
ENABLE_MEAN_REVERSION = True         # Medium risk/reward

# =========================
# INDICATORS
# =========================
RSI_PERIOD = 14
RSI_OVERSOLD = 25               # More extreme
RSI_OVERBOUGHT = 75             # More extreme

EMA_FAST = 8                    # Faster EMAs
EMA_MEDIUM = 21
EMA_SLOW = 50

ATR_PERIOD = 14
BB_PERIOD = 20
BB_STD_DEV = 2.5                # Wider bands

# =========================
# TRADING FILTERS (Relaxed)
# =========================
ENABLE_SESSION_FILTER = False   # Trade 24/7 for more opportunities
ALLOWED_SESSIONS = ["LONDON", "NEW_YORK", "ASIAN"]

ENABLE_NEWS_FILTER = False      # Trade through news (RISKY!)
ENABLE_REGIME_FILTER = False    # No regime filter

# =========================
# POSITION MANAGEMENT (Aggressive)
# =========================
BREAKEVEN_TRIGGER_PIPS = 15     # Move to BE after 15 pips
TRAILING_START_PIPS = 25        # Start trailing after 25 pips
TRAILING_DISTANCE_PIPS = 15     # Trail 15 pips behind
MAX_TRADE_DURATION_HOURS = 48   # Longer hold time

# =========================
# SAFETY (Still important!)
# =========================
ENABLE_KILL_SWITCH = True
KILL_SWITCH_FILE = "KILL_SWITCH.txt"

PREVENT_DUPLICATE_TRADES = False # Allow more trades
MIN_CANDLES_BETWEEN_TRADES = 1

# =========================
# LOGGING
# =========================
LOG_DIRECTORY = "logs"
TRADE_JOURNAL_FILE = "logs/aggressive_journal.csv"
PERFORMANCE_FILE = "logs/aggressive_performance.json"

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
    warnings = []
    
    if ACCOUNT_BALANCE <= 0:
        errors.append("ACCOUNT_BALANCE must be positive")
    
    if RISK_PER_TRADE > 0.05:
        warnings.append(f"⚠️ Risk per trade is {RISK_PER_TRADE*100}% - This is VERY AGGRESSIVE!")
    
    if MAX_DAILY_LOSS > ACCOUNT_BALANCE * 0.5:
        warnings.append(f"⚠️ Max daily loss (${MAX_DAILY_LOSS}) is >50% of account")
    
    import os
    for pair in TRADING_PAIRS:
        if pair['enabled'] and not os.path.exists(pair['data_file']):
            errors.append(f"Data file not found: {pair['data_file']}")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


def print_config():
    """Print configuration"""
    print("\n" + "="*80)
    print("⚡ HIGH RISK / HIGH REWARD TRADING SYSTEM")
    print("="*80)
    
    print(f"\n💰 Account (AGGRESSIVE SETTINGS):")
    print(f"   Balance: ${ACCOUNT_BALANCE}")
    print(f"   Risk per Trade: {RISK_PER_TRADE*100}% (${ACCOUNT_BALANCE * RISK_PER_TRADE}) ⚠️")
    print(f"   Min RR Required: {MIN_RISK_REWARD}:1")
    print(f"   Max Daily Loss: ${MAX_DAILY_LOSS} ({MAX_DAILY_LOSS/ACCOUNT_BALANCE*100:.1f}%) ⚠️")
    
    print(f"\n📊 Trading Pairs ({sum(1 for p in TRADING_PAIRS if p['enabled'])} enabled):")
    for pair in TRADING_PAIRS:
        status = "✅" if pair['enabled'] else "❌"
        print(f"   {status} {pair['symbol']}")
    
    print(f"\n🎯 Strategies (Multi-Strategy Aggressive):")
    strategies = []
    if ENABLE_VOLATILITY_BREAKOUT:
        strategies.append("Volatility Breakout")
    if ENABLE_LONDON_BREAKOUT:
        strategies.append("London Breakout")
    if ENABLE_AGGRESSIVE_TREND:
        strategies.append("Aggressive Trend")
    if ENABLE_MEAN_REVERSION:
        strategies.append("Mean Reversion")
    
    for s in strategies:
        print(f"   ✅ {s}")
    
    print(f"\n🛡️  Risk Limits:")
    print(f"   Max Total Concurrent: {MAX_CONCURRENT_TRADES} ⚠️")
    print(f"   Max Per Pair: {MAX_TRADES_PER_PAIR}")
    print(f"   Max Daily Trades: {MAX_DAILY_TRADES}")
    
    print(f"\n⚡ Execution:")
    print(f"   Live Trading: {'⚠️ ENABLED' if ENABLE_EXECUTION else '✅ DISABLED (SAFE)'}")
    
    print(f"\n⚠️  WARNING:")
    print(f"   This is a HIGH RISK configuration!")
    print(f"   - 3% risk per trade (vs 1% conservative)")
    print(f"   - 30% max daily loss (vs 10% conservative)")
    print(f"   - Up to 5 concurrent trades")
    print(f"   - Aggressive entry strategies")
    print(f"   - Higher potential rewards BUT higher potential losses!")
    
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
