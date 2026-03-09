# ================================================================
# OPTIMIZED CONFIG FOR ULTIMATE STRATEGY (3:1+ R:R)
# Best settings for maximum profitability
# ================================================================

import sys
import os
import json

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
ENABLE_EXECUTION = True  # ⚠️ Live trading enabled
MAGIC_NUMBER = 234000

# MT5 Login - Read from env vars OR mt5_config.json

MT5_ACCOUNT = int(os.environ.get('MT5_ACCOUNT', 0))
MT5_PASSWORD = os.environ.get('MT5_PASSWORD', '')
MT5_SERVER = os.environ.get('MT5_SERVER', '')

# Fallback to mt5_config.json if not in environment
if MT5_ACCOUNT == 0 or not MT5_PASSWORD or not MT5_SERVER:
    mt5_config_path = os.path.join(os.path.dirname(__file__), 'mobile_api', 'mt5_config.json')
    if os.path.exists(mt5_config_path):
        try:
            with open(mt5_config_path) as f:
                mt5_cfg = json.load(f)
                if mt5_cfg.get('account') and str(mt5_cfg.get('account')).isdigit():
                    MT5_ACCOUNT = int(mt5_cfg.get('account', 0))
                MT5_PASSWORD = mt5_cfg.get('password', '')
                MT5_SERVER = mt5_cfg.get('server', '')
        except:
            pass

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
# HARD RISK LIMITS (Non-overrideable)
# ================================================================
class RiskLimits:
    """Non-overrideable risk limits for capital preservation"""
    MAX_RISK_PER_TRADE = 0.02       # 2% absolute max per trade
    MAX_DAILY_LOSS = 20             # $20 hard limit per day
    MAX_DAILY_TRADES = 10           # 10 trades max per day
    MAX_CONCURRENT = 3              # 3 positions max at once
    MIN_CONFIDENCE = 70             # Minimum AI confidence threshold
    EMERGENCY_LOSS_THRESHOLD = 50   # Kill switch at $50 loss


# ================================================================
# VALIDATION FUNCTION
# ================================================================
def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []
    
    # Check risk settings - respect hard limits
    if RISK_PER_TRADE <= 0 or RISK_PER_TRADE > RiskLimits.MAX_RISK_PER_TRADE:
        errors.append(f"⚠️ RISK_PER_TRADE should be between 0.01 and {RiskLimits.MAX_RISK_PER_TRADE*100}% (hard limit)")
    
    if RISK_PER_TRADE > 0.02:
        warnings.append(f"⚠️ RISK_PER_TRADE above 2% is aggressive - consider lowering")
    
    if MIN_RISK_REWARD < 2.0:
        warnings.append("⚠️ MIN_RISK_REWARD below 2.0 - consider increasing to 3.0+")
    
    # Hard limit validations
    global MAX_DAILY_LOSS, MAX_DAILY_TRADES, MAX_CONCURRENT_TRADES
    
    if MAX_DAILY_LOSS > RiskLimits.MAX_DAILY_LOSS:
        warnings.append(f"⚠️ MAX_DAILY_LOSS capped at ${RiskLimits.MAX_DAILY_LOSS} (hard limit)")
        MAX_DAILY_LOSS = RiskLimits.MAX_DAILY_LOSS
    
    if MAX_DAILY_TRADES > RiskLimits.MAX_DAILY_TRADES:
        warnings.append(f"⚠️ MAX_DAILY_TRADES capped at {RiskLimits.MAX_DAILY_TRADES} (hard limit)")
        MAX_DAILY_TRADES = RiskLimits.MAX_DAILY_TRADES
    
    if MAX_CONCURRENT_TRADES > RiskLimits.MAX_CONCURRENT:
        warnings.append(f"⚠️ MAX_CONCURRENT_TRADES capped at {RiskLimits.MAX_CONCURRENT} (hard limit)")
        MAX_CONCURRENT_TRADES = RiskLimits.MAX_CONCURRENT
    
    if MAX_DAILY_LOSS <= 0:
        errors.append("❌ MAX_DAILY_LOSS must be positive")
    
    if not SYMBOL:
        errors.append("❌ SYMBOL must be set")
    
    if ENABLE_EXECUTION and not MT5_ACCOUNT:
        # Check if MT5 is already connected via mobile_api
        mt5_connected = False
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mobile_api'))
            from mt5_manager import mt5_manager
            mt5_connected = mt5_manager.connected
        except:
            pass
        
        if not mt5_connected:
            errors.append("MT5_ACCOUNT required for live trading (or connect via API first)")
    
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
