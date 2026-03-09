# ================================================================
# OPTIMIZED CONFIG FOR ULTIMATE STRATEGY (3:1+ R:R)
# Best settings for maximum profitability
# ================================================================

# ================================================================
# ACCOUNT SETTINGS
# ================================================================
ACCOUNT_BALANCE = 500
RISK_PER_TRADE = 0.01  # 1% risk per trade (conservative)
MIN_RISK_REWARD = 3.0   # 🎯 MINIMUM 3:1 R:R (this is the key!)

# ================================================================
# SYMBOL & DATA
# ================================================================
SYMBOL = "EURUSD"
TIMEFRAME = "M15"
DATA_FILE = "data/EURUSD_M15.csv"

# ================================================================
# STRATEGY SELECTION (NEW!)
# ================================================================
USE_ULTIMATE_STRATEGY = True   # 🏆 Use the BEST strategy
USE_SR_STRATEGY = False        # Old S/R strategy
USE_BOS_STRATEGY = False       # Old BOS strategy

# ================================================================
# EXECUTION SETTINGS
# ================================================================
ENABLE_EXECUTION = False  # ⚠️ Set to True for live trading
MAGIC_NUMBER = 234000

# MT5 Login (Update with your details)
MT5_ACCOUNT = 5046125612
MT5_PASSWORD = "P@LoQr8m"
MT5_SERVER = "MetaQuotes-Demo"

# ================================================================
# RISK MANAGEMENT (OPTIMIZED)
# ================================================================
MAX_DAILY_LOSS = 20         # Stop trading if lose $20/day
MAX_DAILY_TRADES = 5        # Max 5 trades per day (quality over quantity)
MAX_CONCURRENT_TRADES = 2   # Max 2 positions at once
MAX_POSITION_SIZE = 0.5     # Max 0.5 lots per trade

# ================================================================
# POSITION MANAGEMENT
# ================================================================
BREAKEVEN_TRIGGER_PIPS = 15      # Move to BE after 15 pips profit
TRAILING_START_PIPS = 20         # Start trailing after 20 pips
TRAILING_DISTANCE_PIPS = 10      # Trail 10 pips behind
MAX_TRADE_DURATION_HOURS = 48    # Close if open for 48 hours

# ================================================================
# ULTIMATE STRATEGY SETTINGS
# ================================================================
MIN_CONFIDENCE = 70              # Only take trades with 70%+ confidence
LOOKBACK_SWING_POINTS = 5        # Candles for swing high/low detection
ORDER_BLOCK_LOOKBACK = 10        # Max candles to look back for order blocks
LIQUIDITY_GRAB_WINDOW = 10       # Candles to detect liquidity grabs

# ================================================================
# INDICATOR SETTINGS
# ================================================================
EMA_FAST = 20
EMA_MEDIUM = 50
EMA_SLOW = 200

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

ATR_PERIOD = 14

# ================================================================
# TRADING FILTERS
# ================================================================
ENABLE_SESSION_FILTER = True
ALLOWED_SESSIONS = ["LONDON", "NEW_YORK"]  # Best sessions for liquidity

ENABLE_NEWS_FILTER = True
NEWS_BUFFER_MINUTES = 30

ENABLE_SPREAD_FILTER = True
MAX_SPREAD_PIPS = 2.0

# ================================================================
# SAFETY FEATURES
# ================================================================
ENABLE_KILL_SWITCH = True
KILL_SWITCH_FILE = "KILL_SWITCH.txt"

PREVENT_DUPLICATE_TRADES = True
MIN_CANDLES_BETWEEN_TRADES = 5  # Wait 5 candles between trades

# ================================================================
# NOTIFICATIONS
# ================================================================
ENABLE_NOTIFICATIONS = False
NOTIFICATION_METHODS = []

# Telegram settings
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# Email settings
EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_PASSWORD = ""
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ================================================================
# LOGGING
# ================================================================
LOG_DIRECTORY = "logs"
TRADE_JOURNAL_FILE = "logs/trade_journal.csv"
PERFORMANCE_FILE = "logs/performance.json"
ERROR_LOG_FILE = "logs/errors.log"

ENABLE_CONSOLE_LOGGING = True
SHOW_DETAILED_LOGS = True

# ================================================================
# MULTI-PAIR SETTINGS (OPTIONAL)
# ================================================================
TRADE_MULTIPLE_PAIRS = False
PAIRS_TO_TRADE = [
    "EURUSD",
    "GBPUSD", 
    "USDCAD",
    "AUDUSD",
    "NZDUSD"
]

# ================================================================
# BACKTESTING SETTINGS
# ================================================================
BACKTEST_START_DATE = "2024-01-01"
BACKTEST_END_DATE = "2025-12-31"
BACKTEST_INITIAL_BALANCE = 500

# ================================================================
# COMPATIBILITY (keep old variable names)
# ================================================================
RSI_RANGE = (RSI_OVERSOLD, RSI_OVERBOUGHT)
MIN_RR = MIN_RISK_REWARD
BALANCE = ACCOUNT_BALANCE
RISK_PCT = RISK_PER_TRADE

# ================================================================
# VALIDATION FUNCTION
# ================================================================
def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []
    
    # Check risk settings
    if RISK_PER_TRADE <= 0 or RISK_PER_TRADE > 0.05:
        errors.append("⚠️ RISK_PER_TRADE should be between 0.01 and 0.05 (1-5%)")
    
    if MIN_RISK_REWARD < 2.0:
        warnings.append("⚠️ MIN_RISK_REWARD below 2.0 - consider increasing to 3.0+")
    
    if MAX_DAILY_LOSS <= 0:
        errors.append("❌ MAX_DAILY_LOSS must be positive")
    
    if not SYMBOL:
        errors.append("❌ SYMBOL must be set")
    
    if ENABLE_EXECUTION and not MT5_ACCOUNT:
        errors.append("❌ MT5_ACCOUNT required for live trading")
    
    # Print errors
    if errors:
        print("\n❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"   {error}")
        return False
    
    # Print warnings
    if warnings:
        print("\n⚠️ CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    return True


def print_config():
    """Display current configuration"""
    print("\n" + "="*70)
    print("⚙️ CONFIGURATION SUMMARY")
    print("="*70)
    
    print(f"\n💰 ACCOUNT:")
    print(f"   Balance: ${ACCOUNT_BALANCE:,.2f}")
    print(f"   Risk per Trade: {RISK_PER_TRADE*100}%")
    print(f"   Min R:R: {MIN_RISK_REWARD}:1")
    
    print(f"\n📊 TRADING:")
    print(f"   Symbol: {SYMBOL}")
    print(f"   Timeframe: {TIMEFRAME}")
    print(f"   Strategy: {'🏆 ULTIMATE' if USE_ULTIMATE_STRATEGY else 'S/R' if USE_SR_STRATEGY else 'BOS'}")
    print(f"   Execution: {'🔴 ENABLED' if ENABLE_EXECUTION else '✅ DISABLED (Safe)'}")
    
    print(f"\n🛡️ RISK MANAGEMENT:")
    print(f"   Max Daily Loss: ${MAX_DAILY_LOSS}")
    print(f"   Max Daily Trades: {MAX_DAILY_TRADES}")
    print(f"   Max Concurrent: {MAX_CONCURRENT_TRADES}")
    
    print(f"\n🎯 STRATEGY:")
    print(f"   Min Confidence: {MIN_CONFIDENCE}%")
    print(f"   Sessions: {', '.join(ALLOWED_SESSIONS)}")
    
    print("="*70 + "\n")


# ================================================================
# STRATEGY PROFILES (PRESETS)
# ================================================================

def load_aggressive_profile():
    """High risk, high reward profile"""
    global RISK_PER_TRADE, MIN_RISK_REWARD, MAX_DAILY_TRADES
    RISK_PER_TRADE = 0.02      # 2% risk
    MIN_RISK_REWARD = 4.0      # 4:1 R:R
    MAX_DAILY_TRADES = 10      # More trades
    print("📊 Loaded: AGGRESSIVE profile")


def load_conservative_profile():
    """Low risk, steady growth profile"""
    global RISK_PER_TRADE, MIN_RISK_REWARD, MAX_DAILY_TRADES
    RISK_PER_TRADE = 0.005     # 0.5% risk
    MIN_RISK_REWARD = 3.0      # 3:1 R:R
    MAX_DAILY_TRADES = 3       # Fewer trades
    print("📊 Loaded: CONSERVATIVE profile")


def load_balanced_profile():
    """Balanced risk/reward (RECOMMENDED)"""
    global RISK_PER_TRADE, MIN_RISK_REWARD, MAX_DAILY_TRADES
    RISK_PER_TRADE = 0.01      # 1% risk
    MIN_RISK_REWARD = 3.0      # 3:1 R:R
    MAX_DAILY_TRADES = 5       # Moderate trades
    print("📊 Loaded: BALANCED profile (Recommended)")


# ================================================================
# RUN VALIDATION ON IMPORT
# ================================================================
if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration is valid")
        print_config()
    else:
        print("\n❌ Please fix configuration errors before trading")
