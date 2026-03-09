"""
Multi-Pair Trading System with S/R Strategy
Trades multiple currency pairs simultaneously
"""

import time
import sys
from datetime import date
import os

# Core imports
from data_loader import load_csv, add_indicators
from sr_strategy import auto_detect_sr_setup, resample_to_h1
from risk import RiskManager
from executor import connect, disconnect, place_trade, get_open_positions
from filters import is_trading_session, is_kill_switch_active
from journal import init_journal, log_trade
from performance import PerformanceTracker

from multi_pair_config import (
    ACCOUNT_BALANCE,
    RISK_PER_TRADE,
    ENABLE_EXECUTION,
    MAX_DAILY_LOSS,
    MAX_DAILY_TRADES,
    MAX_CONCURRENT_TRADES,
    MAX_TRADES_PER_PAIR,
    MIN_RISK_REWARD,
    PREVENT_DUPLICATE_TRADES,
    MIN_CANDLES_BETWEEN_TRADES,
    USE_SR_STRATEGY,
    TRADING_PAIRS,
    SPLIT_RISK_ACROSS_PAIRS,
    validate_config,
    print_config,
    get_enabled_pairs
)

# =========================
# STARTUP
# =========================
print("\n" + "="*80)
print("🚀 MULTI-PAIR TRADING SYSTEM with S/R Strategy")
print("="*80 + "\n")

# Validate config
if not validate_config():
    print("❌ Configuration errors. Please fix multi_pair_config.py")
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

# Tracking
current_day = date.today()

# Pair-specific tracking
pair_data = {}
pair_last_trade = {}

# =========================
# LOAD DATA FOR ALL PAIRS
# =========================
print("📊 Loading data for all pairs...\n")

enabled_pairs = get_enabled_pairs()

for pair_config in enabled_pairs:
    symbol = pair_config['symbol']
    data_file = pair_config['data_file']
    
    print(f"Loading {symbol} from {data_file}...")
    
    df = load_csv(data_file)
    
    if df is None:
        print(f"❌ Failed to load {symbol}. Skipping this pair.")
        continue
    
    df = add_indicators(df)
    
    # Create H1 data
    df_h1 = resample_to_h1(df)
    
    # Store data
    pair_data[symbol] = {
        'df': df,
        'df_h1': df_h1,
        'last_index': -1,
        'last_trade_index': -999,
        'open_trades': 0
    }
    
    print(f"✅ {symbol}: {len(df)} M15 candles, {len(df_h1)} H1 candles\n")

if not pair_data:
    print("❌ No pairs loaded successfully. Exiting.")
    sys.exit(1)

print(f"✅ Loaded {len(pair_data)} pairs\n")

# =========================
# MT5 CONNECTION
# =========================
if ENABLE_EXECUTION:
    print("⚠️  LIVE EXECUTION ENABLED ⚠️\n")
    print("Connecting to MT5...")
    
    if not connect():
        print("❌ MT5 connection failed. Exiting.")
        sys.exit(1)
    
    print("✅ MT5 connected\n")
else:
    print("🛡️  SAFE MODE - Paper Trading Only\n")

# =========================
# MAIN LOOP
# =========================
print("="*80)
print("🔄 Starting Multi-Pair Trading Loop")
print(f"   Trading {len(pair_data)} pairs simultaneously")
print("="*80 + "\n")

try:
    iteration = 0
    
    while True:
        iteration += 1
        
        # Print iteration header every 10 iterations
        if iteration % 10 == 1:
            print(f"\n{'='*80}")
            print(f"Iteration {iteration}")
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
            
            # Reset per-pair trade counts
            for symbol in pair_data:
                pair_data[symbol]['open_trades'] = 0
        
        # -------------------------------------------------
        # KILL SWITCH
        # -------------------------------------------------
        if is_kill_switch_active():
            print("🛑 KILL SWITCH ACTIVE - All trading halted")
            time.sleep(5)
            continue
        
        # -------------------------------------------------
        # RISK CHECKS (Global)
        # -------------------------------------------------
        can_trade, reason = risk_manager.can_trade()
        if not can_trade:
            print(f"🛑 Global limit: {reason}")
            time.sleep(5)
            continue
        
        # Update open positions count
        if ENABLE_EXECUTION:
            all_open = get_open_positions()
            risk_manager.current_positions = len(all_open)
        
        # -------------------------------------------------
        # PROCESS EACH PAIR
        # -------------------------------------------------
        for symbol, data in pair_data.items():
            df = data['df']
            df_h1 = data['df_h1']
            last_index = data['last_index']
            last_trade_index = data['last_trade_index']
            
            # Check for new candle
            if last_index >= len(df) - 1:
                continue  # No more data for this pair
            
            last_index += 1
            data['last_index'] = last_index
            
            df_slice = df.iloc[: last_index + 1]
            row = df_slice.iloc[-1]
            
            candle_time = row["time"]
            price = row["close"]
            
            # Quick filters
            if not is_trading_session(candle_time):
                continue
            
            # Check per-pair limits
            if data['open_trades'] >= MAX_TRADES_PER_PAIR:
                continue
            
            # Duplicate prevention
            if PREVENT_DUPLICATE_TRADES:
                candles_since = last_index - last_trade_index
                if candles_since < MIN_CANDLES_BETWEEN_TRADES:
                    continue
            
            # -------------------------------------------------
            # S/R STRATEGY
            # -------------------------------------------------
            if USE_SR_STRATEGY:
                # Get H1 slice
                h1_index = min(last_index // 4, len(df_h1) - 1)
                df_h1_slice = df_h1.iloc[: h1_index + 1]
                
                # Detect setup
                setup = auto_detect_sr_setup(df_h1_slice, df_slice)
                
                if setup is None:
                    continue  # No setup for this pair
                
                # Extract setup
                direction = "LONG" if setup['side'] == "BUY" else "SHORT"
                entry = setup['entry']
                stop = setup['sl']
                target = setup['tp']
                
                print(f"\n{'='*80}")
                print(f"💡 {symbol} S/R SETUP at {candle_time}")
                print(f"{'='*80}")
                print(f"   Type: {setup['type']}")
                print(f"   Zone: {setup['zone']['center']:.5f}")
                print(f"   Direction: {direction}")
                
            else:
                continue  # No other strategy implemented
            
            # -------------------------------------------------
            # VALIDATE TRADE
            # -------------------------------------------------
            valid, msg = risk_manager.validate_trade(
                entry, stop, target, direction, MIN_RISK_REWARD
            )
            
            if not valid:
                print(f"   ❌ Validation: {msg}")
                continue
            
            # -------------------------------------------------
            # POSITION SIZING
            # -------------------------------------------------
            # Adjust risk if splitting across pairs
            if SPLIT_RISK_ACROSS_PAIRS and risk_manager.current_positions > 0:
                risk_pct = RISK_PER_TRADE / (risk_manager.current_positions + 1)
            else:
                risk_pct = RISK_PER_TRADE
            
            position_size = risk_manager.calculate_position_size(
                ACCOUNT_BALANCE,
                risk_pct,
                entry,
                stop,
                symbol
            )
            
            rr = risk_manager.calculate_rr(entry, stop, target)
            
            print(f"\n   💰 TRADE DETAILS:")
            print(f"   Entry: {entry:.5f}")
            print(f"   Stop:  {stop:.5f} ({abs(entry-stop)*10000:.1f} pips)")
            print(f"   Target: {target:.5f}")
            print(f"   RR: {rr}:1")
            print(f"   Size: {position_size} lots")
            print(f"   Risk: ${ACCOUNT_BALANCE * risk_pct:.2f}")
            
            # -------------------------------------------------
            # EXECUTE TRADE
            # -------------------------------------------------
            if ENABLE_EXECUTION:
                print(f"   🔴 PLACING ORDER on {symbol}...")
                
                try:
                    result = place_trade(
                        symbol,
                        direction,
                        position_size,
                        stop,
                        target,
                        f"SR_{direction}_{symbol}"
                    )
                    
                    if result and result.retcode == 10009:
                        print(f"   ✅ ORDER EXECUTED\n")
                        
                        risk_manager.add_trade()
                        data['last_trade_index'] = last_index
                        data['open_trades'] += 1
                        
                        log_trade(
                            candle_time, price, f"{symbol} TRADE {direction}",
                            [setup['type']], rr, position_size, "EXECUTED"
                        )
                    else:
                        error = f"Failed: {result.retcode if result else 'No result'}"
                        print(f"   ❌ {error}\n")
                
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}\n")
            
            else:
                print(f"   📝 PAPER TRADE\n")
                
                risk_manager.add_trade()
                data['last_trade_index'] = last_index
                data['open_trades'] += 1
                
                log_trade(
                    candle_time, price, f"{symbol} PAPER {direction}",
                    [setup['type']], rr, position_size, "PAPER"
                )
        
        # -------------------------------------------------
        # STATUS UPDATE (every 10 iterations)
        # -------------------------------------------------
        if iteration % 10 == 0:
            stats = risk_manager.get_stats()
            print(f"\n📊 Status: PnL ${stats['daily_pnl']:.2f} | "
                  f"Trades {stats['daily_trades']}/{MAX_DAILY_TRADES} | "
                  f"Open {stats['open_positions']}/{MAX_CONCURRENT_TRADES}")
            
            # Show pair status
            for symbol, data in pair_data.items():
                print(f"   {symbol}: Candle {data['last_index']}/{len(data['df'])-1} | "
                      f"Trades: {data['open_trades']}/{MAX_TRADES_PER_PAIR}")
        
        # Sleep
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
    print("Multi-pair trading system shutdown complete")
