"""
AGGRESSIVE Multi-Strategy Trading System
⚠️ HIGH RISK / HIGH REWARD
Combines: Breakout + Mean Reversion + Trend + Volatility
"""

import time
import sys
from datetime import date

# Core imports
from data_loader import load_csv, add_indicators
from aggressive_strategy import aggressive_multi_strategy, resample_to_h1
from risk import RiskManager
from executor import connect, disconnect, place_trade, get_open_positions
from filters import is_kill_switch_active
from journal import init_journal, log_trade
from performance import PerformanceTracker

from aggressive_config import (
    ACCOUNT_BALANCE,
    RISK_PER_TRADE,
    ENABLE_EXECUTION,
    MAX_DAILY_LOSS,
    MAX_DAILY_TRADES,
    MAX_CONCURRENT_TRADES,
    MAX_TRADES_PER_PAIR,
    MIN_RISK_REWARD,
    TRADING_PAIRS,
    validate_config,
    print_config,
    get_enabled_pairs
)

# =========================
# STARTUP
# =========================
print("\n" + "="*80)
print("⚡ AGGRESSIVE HIGH RISK / HIGH REWARD TRADING SYSTEM")
print("="*80 + "\n")

if not validate_config():
    print("❌ Configuration errors. Please fix aggressive_config.py")
    sys.exit(1)

print_config()

input("\n⚠️  WARNING: This is an AGGRESSIVE system with 3% risk per trade!\n"
      "Press ENTER to continue or Ctrl+C to abort...")

# =========================
# INITIALIZE
# =========================
print("\n🔧 Initializing aggressive trading system...\n")

risk_manager = RiskManager(
    max_daily_loss=MAX_DAILY_LOSS,
    max_daily_trades=MAX_DAILY_TRADES,
    max_concurrent=MAX_CONCURRENT_TRADES
)

performance = PerformanceTracker(filepath="logs/aggressive_performance.json")
init_journal(filepath="logs/aggressive_journal.csv")

current_day = date.today()
pair_data = {}

# =========================
# LOAD DATA
# =========================
print("📊 Loading data for all pairs...\n")

enabled_pairs = get_enabled_pairs()

for pair_config in enabled_pairs:
    symbol = pair_config['symbol']
    data_file = pair_config['data_file']
    
    print(f"Loading {symbol}...")
    df = load_csv(data_file)
    
    if df is None:
        print(f"❌ Failed to load {symbol}. Skipping.")
        continue
    
    df = add_indicators(df)
    df_h1 = resample_to_h1(df)
    
    pair_data[symbol] = {
        'df': df,
        'df_h1': df_h1,
        'last_index': -1,
        'open_trades': 0
    }
    
    print(f"✅ {symbol}: {len(df)} M15 candles, {len(df_h1)} H1 candles\n")

if not pair_data:
    print("❌ No pairs loaded. Exiting.")
    sys.exit(1)

print(f"✅ Loaded {len(pair_data)} pairs\n")

# =========================
# MT5 CONNECTION
# =========================
if ENABLE_EXECUTION:
    print("⚠️  LIVE EXECUTION ENABLED ⚠️\n")
    
    if not connect():
        print("❌ MT5 connection failed. Exiting.")
        sys.exit(1)
    
    print("✅ MT5 connected\n")
else:
    print("🛡️  SAFE MODE - Paper Trading\n")

# =========================
# MAIN LOOP
# =========================
print("="*80)
print("🔄 Starting Aggressive Multi-Strategy Trading")
print(f"   Strategies: Volatility Breakout, London Breakout, Trend, Mean Reversion")
print(f"   Risk: 3% per trade | Min RR: 3:1")
print("="*80 + "\n")

try:
    iteration = 0
    
    while True:
        iteration += 1
        
        if iteration % 10 == 1:
            print(f"\n{'='*80}")
            print(f"Iteration {iteration}")
            print(f"{'='*80}")
        
        # New day check
        today = date.today()
        if today != current_day:
            print(f"\n📅 NEW DAY: {today}")
            performance.print_summary()
            risk_manager.reset_daily()
            current_day = today
            
            for symbol in pair_data:
                pair_data[symbol]['open_trades'] = 0
        
        # Kill switch
        if is_kill_switch_active():
            print("🛑 KILL SWITCH ACTIVE")
            time.sleep(5)
            continue
        
        # Risk checks
        can_trade, reason = risk_manager.can_trade()
        if not can_trade:
            if iteration % 10 == 0:
                print(f"🛑 {reason}")
            time.sleep(1)
            continue
        
        # Update positions
        if ENABLE_EXECUTION:
            all_open = get_open_positions()
            risk_manager.current_positions = len(all_open)
        
        # Process each pair
        for symbol, data in pair_data.items():
            df = data['df']
            df_h1 = data['df_h1']
            last_index = data['last_index']
            
            # Check for new candle
            if last_index >= len(df) - 1:
                continue
            
            last_index += 1
            data['last_index'] = last_index
            
            df_slice = df.iloc[: last_index + 1]
            row = df_slice.iloc[-1]
            
            candle_time = row["time"]
            price = row["close"]
            
            # Check per-pair limits
            if data['open_trades'] >= MAX_TRADES_PER_PAIR:
                continue
            
            # Get H1 slice
            h1_index = min(last_index // 4, len(df_h1) - 1)
            df_h1_slice = df_h1.iloc[: h1_index + 1]
            
            # =========================
            # AGGRESSIVE MULTI-STRATEGY
            # =========================
            setup = aggressive_multi_strategy(df_h1_slice, df_slice)
            
            if setup is None:
                continue
            
            # Extract setup
            direction = "LONG" if setup['side'] == "BUY" else "SHORT"
            entry = setup['entry']
            stop = setup['sl']
            target = setup['tp']
            
            print(f"\n{'='*80}")
            print(f"⚡ {symbol} {setup['type'].upper()} - {setup['strength']} PRIORITY")
            print(f"{'='*80}")
            print(f"   Time: {candle_time}")
            print(f"   Direction: {direction}")
            
            # Validate
            valid, msg = risk_manager.validate_trade(
                entry, stop, target, direction, MIN_RISK_REWARD
            )
            
            if not valid:
                print(f"   ❌ Validation: {msg}")
                continue
            
            # Position sizing (AGGRESSIVE 3%)
            position_size = risk_manager.calculate_position_size(
                ACCOUNT_BALANCE,
                RISK_PER_TRADE,
                entry,
                stop,
                symbol
            )
            
            rr = risk_manager.calculate_rr(entry, stop, target)
            risk_amount = ACCOUNT_BALANCE * RISK_PER_TRADE
            
            print(f"\n   💰 TRADE DETAILS:")
            print(f"   Entry: {entry:.5f}")
            print(f"   Stop:  {stop:.5f} ({abs(entry-stop)*10000:.1f} pips)")
            print(f"   Target: {target:.5f}")
            print(f"   RR: {rr}:1 ⚡")
            print(f"   Size: {position_size} lots")
            print(f"   Risk: ${risk_amount:.2f} (3% of account) ⚠️")
            print(f"   Potential Profit: ${risk_amount * rr:.2f}")
            
            # Execute
            if ENABLE_EXECUTION:
                print(f"   🔴 PLACING AGGRESSIVE ORDER...")
                
                try:
                    result = place_trade(
                        symbol,
                        direction,
                        position_size,
                        stop,
                        target,
                        f"AGG_{setup['type']}"
                    )
                    
                    if result and result.retcode == 10009:
                        print(f"   ✅ ORDER EXECUTED\n")
                        
                        risk_manager.add_trade()
                        data['open_trades'] += 1
                        
                        log_trade(
                            candle_time, price, f"{symbol} AGG {direction}",
                            [setup['type'], setup['strength']], 
                            rr, position_size, "EXECUTED"
                        )
                    else:
                        error = f"Failed: {result.retcode if result else 'No result'}"
                        print(f"   ❌ {error}\n")
                
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}\n")
            
            else:
                print(f"   📝 PAPER TRADE (AGGRESSIVE)\n")
                
                risk_manager.add_trade()
                data['open_trades'] += 1
                
                log_trade(
                    candle_time, price, f"{symbol} PAPER_AGG {direction}",
                    [setup['type'], setup['strength']], 
                    rr, position_size, "PAPER"
                )
        
        # Status update
        if iteration % 10 == 0:
            stats = risk_manager.get_stats()
            print(f"\n📊 Status: PnL ${stats['daily_pnl']:.2f} | "
                  f"Trades {stats['daily_trades']}/{MAX_DAILY_TRADES} | "
                  f"Open {stats['open_positions']}/{MAX_CONCURRENT_TRADES}")
            
            for symbol, data in pair_data.items():
                print(f"   {symbol}: Candle {data['last_index']}/{len(data['df'])-1} | "
                      f"Trades: {data['open_trades']}/{MAX_TRADES_PER_PAIR}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n🛑 Shutdown signal received...")
    print("="*80)
    
    performance.print_summary()
    
    if ENABLE_EXECUTION:
        print("\nDisconnecting from MT5...")
        disconnect()
    
    print("\n✅ Aggressive system stopped")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    if ENABLE_EXECUTION:
        disconnect()
    
    raise

finally:
    print("Aggressive trading system shutdown complete")
