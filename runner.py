"""
COMPLETE TRADING SYSTEM
Automated trading with S/R strategy
"""

import time
import sys
from datetime import date

# Core imports
from data_loader import load_csv, add_indicators
from sr_strategy import auto_detect_sr_setup, resample_to_h1
from risk import RiskManager
from executor import connect, disconnect, place_trade, get_open_positions, get_account_info
from filters import is_trading_session, is_kill_switch_active, load_news, is_news_blocked, detect_regime
from journal import init_journal, log_trade
from performance import PerformanceTracker
from audit_journal import get_audit_journal

# Import MT5 for retcode constants
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from config import (
    ACCOUNT_BALANCE,
    RISK_PER_TRADE,
    ENABLE_EXECUTION,
    SYMBOL,
    DATA_FILE,
    MAX_DAILY_LOSS,
    MAX_DAILY_TRADES,
    MAX_CONCURRENT_TRADES,
    MIN_RISK_REWARD,
    PREVENT_DUPLICATE_TRADES,
    MIN_CANDLES_BETWEEN_TRADES,
    USE_SR_STRATEGY,
    validate_config,
    print_config
)

# =========================
# STARTUP
# =========================
print("\n" + "="*80)
print("🚀 COMPLETE TRADING SYSTEM v1.0")
print("="*80 + "\n")

# Validate config
if not validate_config():
    print("❌ Configuration errors. Please fix config.py")
    sys.exit(1)

print_config()

# =========================
# INITIALIZE
# =========================
print("🔧 Initializing systems...\n")

# Risk manager
risk_manager = RiskManager(
    max_daily_loss=MAX_DAILY_LOSS,
    max_daily_trades=MAX_DAILY_TRADES,
    max_concurrent=MAX_CONCURRENT_TRADES
)

# Performance tracker
performance = PerformanceTracker()

# Journal
init_journal()

# News data
news_df = load_news()

# Tracking variables
last_trade_index = -999
current_day = date.today()
_morning_reset_done = False

# =========================
# MT5 CONNECTION
# =========================
if ENABLE_EXECUTION:
    print("⚠️  LIVE EXECUTION ENABLED ⚠️\n")
    print("Connecting to MT5...")
    
    if not connect():
        print("❌ MT5 connection failed. Exiting.")
        sys.exit(1)
    
    account_info = get_account_info()
    if account_info:
        print(f"✅ Account Balance: ${account_info['balance']:.2f}\n")
else:
    print("🛡️  SAFE MODE - Paper Trading Only\n")

# =========================
# LOAD DATA
# =========================
print(f"📊 Loading data from {DATA_FILE}...")
df = load_csv(DATA_FILE)

if df is None:
    print("❌ Failed to load data. Exiting.")
    sys.exit(1)

df = add_indicators(df)

# Create H1 data for S/R strategy
if USE_SR_STRATEGY:
    print("📈 Creating H1 timeframe data...")
    df_h1 = resample_to_h1(df)
    print(f"✅ H1 data ready ({len(df_h1)} candles)\n")
else:
    df_h1 = None

last_index = -1

# =========================
# MAIN LOOP
# =========================
print("="*80)
print("🔄 Starting Trading Loop")
print("="*80 + "\n")

try:
    while True:
        # Check for new candle
        if last_index < len(df) - 1:
            last_index += 1
            
            df_slice = df.iloc[: last_index + 1]
            row = df_slice.iloc[-1]
            
            candle_time = row["time"]
            price = row["close"]
            
            print(f"\n{'='*80}")
            print(f"🕐 Time: {candle_time} | Price: {price:.5f}")
            print(f"{'='*80}")
            
            # -------------------------------------------------
            # NEW DAY CHECK
            # -------------------------------------------------
            today = date.today()
            if today != current_day:
                print(f"\n📅 NEW DAY: {today}")
                performance.print_summary()
                risk_manager.reset_daily()
                performance.reset_daily()
                current_day = today
            
            # -------------------------------------------------
            # KILL SWITCH
            # -------------------------------------------------
            if is_kill_switch_active():
                print("🛑 KILL SWITCH ACTIVE - Trading halted")
                log_trade(candle_time, price, "NO TRADE", ["Kill switch"], "", "", "KILL_SWITCH")
                time.sleep(1)
                continue
            
            # -------------------------------------------------
            # RISK CHECKS
            # -------------------------------------------------
            can_trade, reason = risk_manager.can_trade()
            if not can_trade:
                print(f"🛑 {reason}")
                log_trade(candle_time, price, "NO TRADE", [reason], "", "", "RISK_BLOCK")
                time.sleep(1)
                continue
            
            # Update positions count
            if ENABLE_EXECUTION:
                open_positions = get_open_positions(symbol=SYMBOL)
                risk_manager.current_positions = len(open_positions)
            
            # Show stats
            stats = risk_manager.get_stats()
            print(f"📊 Daily: PnL ${stats['daily_pnl']:.2f} | Trades {stats['daily_trades']}/{MAX_DAILY_TRADES} | Open {stats['open_positions']}")
            
            # -------------------------------------------------
            # SESSION FILTER
            # -------------------------------------------------
            if not is_trading_session(candle_time):
                print("⏰ Outside trading session")
                continue
            
            # -------------------------------------------------
            # NEWS FILTER
            # -------------------------------------------------
            blocked, event = is_news_blocked(candle_time, news_df)
            if blocked:
                print(f"📰 News block: {event}")
                continue
            
            # -------------------------------------------------
            # REGIME FILTER
            # -------------------------------------------------
            regime, allowed, regime_reason = detect_regime(df_slice)
            if not allowed:
                print(f"📉 Regime blocked: {regime}")
                continue
            
            print(f"✅ Regime: {regime}")
            
            # -------------------------------------------------
            # DUPLICATE PREVENTION
            # -------------------------------------------------
            if PREVENT_DUPLICATE_TRADES:
                candles_since_last = last_index - last_trade_index
                if candles_since_last < MIN_CANDLES_BETWEEN_TRADES:
                    print(f"⏸️  Too soon ({candles_since_last} candles)")
                    continue
            
            # -------------------------------------------------
            # STRATEGY - S/R REJECTION
            # -------------------------------------------------
            if USE_SR_STRATEGY and df_h1 is not None:
                # Get H1 slice
                h1_index = min(last_index // 4, len(df_h1) - 1)
                df_h1_slice = df_h1.iloc[: h1_index + 1]
                
                # Detect setup
                setup = auto_detect_sr_setup(df_h1_slice, df_slice)
                
                if setup is None:
                    print("⏸️  No S/R setup detected")
                    log_trade(candle_time, price, "NO TRADE", ["No S/R setup"], "", "", "ACTIVE")
                    continue
                
                # Extract setup
                direction = "LONG" if setup['side'] == "BUY" else "SHORT"
                entry = setup['entry']
                stop = setup['sl']
                target = setup['tp']
                
                print(f"\n✅ S/R SETUP DETECTED")
                print(f"   Type: {setup['type']}")
                print(f"   Zone: {setup['zone']['center']:.5f}")
                print(f"   Direction: {direction}")
                
            else:
                # No strategy configured
                print("⚠️  No strategy enabled in config")
                continue
            
            # -------------------------------------------------
            # VALIDATE TRADE
            # -------------------------------------------------
            valid, validation_msg = risk_manager.validate_trade(
                entry, stop, target, direction, min_rr=MIN_RISK_REWARD
            )
            
            if not valid:
                print(f"❌ Validation failed: {validation_msg}")
                log_trade(candle_time, price, "NO TRADE", [validation_msg], "", "", "INVALID")
                continue
            
            # -------------------------------------------------
            # POSITION SIZING
            # -------------------------------------------------
            position_size = risk_manager.calculate_position_size(
                ACCOUNT_BALANCE,
                RISK_PER_TRADE,
                entry,
                stop,
                SYMBOL
            )
            
            rr = risk_manager.calculate_rr(entry, stop, target)
            
            print(f"\n{'='*80}")
            print(f"💰 TRADE SIGNAL")
            print(f"{'='*80}")
            print(f"Direction: {direction}")
            print(f"Entry: {entry:.5f}")
            print(f"Stop:  {stop:.5f} ({abs(entry-stop)*10000:.1f} pips)")
            print(f"Target: {target:.5f}")
            print(f"RR: {rr}:1")
            print(f"Size: {position_size} lots")
            print(f"Risk: ${ACCOUNT_BALANCE * RISK_PER_TRADE:.2f}")
            print(f"{'='*80}\n")
            
            # -------------------------------------------------
            # EXECUTE TRADE
            # -------------------------------------------------
            if ENABLE_EXECUTION:
                print("🔴 PLACING LIVE ORDER...")
                
                try:
                    result = place_trade(
                        SYMBOL,
                        direction,
                        position_size,
                        stop,
                        target,
                        f"SR_{direction}"
                    )
                    
                    if result:
                        # Check for success retcode (10009 = TRADE_RETCODE_DONE)
                        try:
                            retcode = result.retcode
                            if retcode == 10009 or retcode == mt5.TRADE_RETCODE_DONE:
                                print("✅ ORDER EXECUTED\n")
                                
                                risk_manager.add_trade()
                                last_trade_index = last_index
                                
                                log_trade(
                                    candle_time, price, f"TRADE {direction}",
                                    [setup['type']], rr, position_size, "EXECUTED"
                                )
                            else:
                                error = f"Order failed: {retcode} - {getattr(result, 'comment', 'Unknown')}"
                                print(f"❌ {error}\n")
                                log_trade(candle_time, price, "FAILED", [error], rr, position_size, "ERROR")
                        except AttributeError:
                            print("✅ ORDER SENT (verification pending)\n")
                            risk_manager.add_trade()
                            last_trade_index = last_index
                            log_trade(
                                candle_time, price, f"TRADE {direction}",
                                [setup['type']], rr, position_size, "PENDING"
                            )
                    else:
                        error = "Order failed: No result returned"
                        print(f"❌ {error}\n")
                        log_trade(candle_time, price, "FAILED", [error], rr, position_size, "ERROR")
                
                except Exception as e:
                    error = f"Execution error: {str(e)}"
                    print(f"❌ {error}\n")
                    log_trade(candle_time, price, "ERROR", [error], "", "", "ERROR")
            
            else:
                print("📝 PAPER TRADE (Execution disabled)\n")
                
                risk_manager.add_trade()
                last_trade_index = last_index
                
                log_trade(
                    candle_time, price, f"PAPER {direction}",
                    [setup['type']], rr, position_size, "PAPER"
                )
        
        # Sleep before next iteration
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n🛑 Shutdown signal received...")
    print("="*80)
    
    performance.print_summary()
    
    if ENABLE_EXECUTION:
        print("\nDisconnecting from MT5...")
        disconnect()
    
    print("\n✅ System stopped safely")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    if ENABLE_EXECUTION:
        disconnect()
    
    raise

finally:
    print("System shutdown complete")
