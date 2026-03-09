"""
AI Agent Integrated Trading System
Combines your strategies with AI agent analysis for enhanced decision making
"""

import time
import sys
from datetime import date

# Core imports
from data_loader import load_csv, add_indicators
from aggressive_strategy import aggressive_multi_strategy, resample_to_h1
from sr_strategy import auto_detect_sr_setup
from risk import RiskManager
from executor import connect, disconnect, place_trade, get_open_positions
from filters import is_kill_switch_active
from journal import init_journal, log_trade
from performance import PerformanceTracker
from ai_agents import AIFinanceAgentTeam

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
    get_enabled_pairs
)

# =========================
# AI AGENT CONFIG
# =========================
ENABLE_AI_AGENTS = True
AI_MIN_CONFIDENCE = 60          # Minimum AI confidence to take trade
AI_ANALYSIS_INTERVAL = 10       # Analyze every N candles
AI_OVERRIDE_STRATEGY = False    # If True, AI can override strategy signals

# =========================
# STARTUP
# =========================
print("\n" + "="*80)
print("🤖 AI AGENT INTEGRATED TRADING SYSTEM")
print("="*80 + "\n")

print("🔧 Initializing AI agents...\n")

# Initialize AI Agent Team
if ENABLE_AI_AGENTS:
    ai_team = AIFinanceAgentTeam()
    print("\n✅ AI agents ready\n")
else:
    ai_team = None
    print("⚠️  AI agents disabled\n")

# Initialize other systems
risk_manager = RiskManager(
    max_daily_loss=MAX_DAILY_LOSS,
    max_daily_trades=MAX_DAILY_TRADES,
    max_concurrent=MAX_CONCURRENT_TRADES
)

performance = PerformanceTracker(filepath="logs/ai_integrated_performance.json")
init_journal(filepath="logs/ai_integrated_journal.csv")

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
        'open_trades': 0,
        'last_ai_analysis': None,
        'ai_analysis_counter': 0
    }
    
    print(f"✅ {symbol}: {len(df)} M15, {len(df_h1)} H1 candles\n")

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
print("🔄 Starting AI-Enhanced Trading")
print("   Strategy: Aggressive Multi-Strategy + AI Analysis")
print("   AI Confidence Required: {}%".format(AI_MIN_CONFIDENCE))
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
            data['ai_analysis_counter'] += 1
            
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
            # AI AGENT ANALYSIS
            # =========================
            ai_recommendation = None
            
            if ENABLE_AI_AGENTS and data['ai_analysis_counter'] >= AI_ANALYSIS_INTERVAL:
                # Run AI analysis
                ai_analysis = ai_team.analyze(df_slice, symbol)
                data['last_ai_analysis'] = ai_analysis
                data['ai_analysis_counter'] = 0
                
                # Get AI recommendation
                should_trade_ai, ai_rec = ai_team.should_trade(
                    df_slice, 
                    min_confidence=AI_MIN_CONFIDENCE
                )
                
                if should_trade_ai:
                    ai_recommendation = ai_rec
                    print(f"\n🤖 AI RECOMMENDATION for {symbol}:")
                    print(f"   Action: {ai_rec['action']}")
                    print(f"   Confidence: {ai_rec['confidence']}%")
                    print(f"   Reason: {ai_rec['reason']}")
            
            # =========================
            # STRATEGY DETECTION
            # =========================
            setup = aggressive_multi_strategy(df_h1_slice, df_slice)
            
            # =========================
            # DECISION LOGIC
            # =========================
            final_decision = None
            
            if AI_OVERRIDE_STRATEGY and ai_recommendation:
                # AI overrides strategy
                final_decision = {
                    'side': ai_recommendation['action'],
                    'entry': ai_recommendation['entry'],
                    'sl': ai_recommendation['stop'],
                    'tp': ai_recommendation['target'],
                    'type': 'ai_recommendation',
                    'strength': 'AI_' + str(ai_recommendation['confidence']),
                    'source': 'AI_AGENT'
                }
            
            elif setup and ai_recommendation:
                # Both agree - high confidence
                strategy_direction = "BUY" if setup['side'] == "BUY" else "SELL"
                ai_direction = ai_recommendation['action']
                
                if strategy_direction == ai_direction:
                    print(f"\n✅ {symbol}: Strategy + AI AGREE ({strategy_direction})")
                    final_decision = setup
                    final_decision['source'] = 'STRATEGY_AI_CONFIRMED'
                    final_decision['ai_confidence'] = ai_recommendation['confidence']
                else:
                    print(f"\n⚠️  {symbol}: Strategy says {strategy_direction}, AI says {ai_direction} - SKIPPING")
                    continue
            
            elif setup:
                # Strategy only
                final_decision = setup
                final_decision['source'] = 'STRATEGY_ONLY'
            
            elif ai_recommendation and not AI_OVERRIDE_STRATEGY:
                # AI only (but not overriding)
                print(f"\n🤖 {symbol}: AI signal but waiting for strategy confirmation")
                continue
            
            else:
                # No signal
                continue
            
            if not final_decision:
                continue
            
            # Extract trade details
            direction = "LONG" if final_decision['side'] == "BUY" else "SHORT"
            entry = final_decision['entry']
            stop = final_decision['sl']
            target = final_decision['tp']
            
            print(f"\n{'='*80}")
            print(f"💡 {symbol} {final_decision.get('type', 'UNKNOWN').upper()}")
            print(f"   Source: {final_decision.get('source', 'UNKNOWN')}")
            if 'ai_confidence' in final_decision:
                print(f"   AI Confidence: {final_decision['ai_confidence']}%")
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
            
            # Position sizing
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
            print(f"   RR: {rr}:1")
            print(f"   Size: {position_size} lots")
            print(f"   Risk: ${risk_amount:.2f}")
            
            # Execute
            if ENABLE_EXECUTION:
                print(f"   🔴 PLACING ORDER...")
                
                try:
                    result = place_trade(
                        symbol,
                        direction,
                        position_size,
                        stop,
                        target,
                        f"AI_{final_decision['source']}"
                    )
                    
                    if result and result.retcode == 10009:
                        print(f"   ✅ ORDER EXECUTED\n")
                        
                        risk_manager.add_trade()
                        data['open_trades'] += 1
                        
                        log_trade(
                            candle_time, price, f"{symbol} AI {direction}",
                            [final_decision['type'], final_decision.get('source', 'UNKNOWN')], 
                            rr, position_size, "EXECUTED"
                        )
                    else:
                        error = f"Failed: {result.retcode if result else 'No result'}"
                        print(f"   ❌ {error}\n")
                
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}\n")
            
            else:
                print(f"   📝 PAPER TRADE (AI INTEGRATED)\n")
                
                risk_manager.add_trade()
                data['open_trades'] += 1
                
                log_trade(
                    candle_time, price, f"{symbol} PAPER_AI {direction}",
                    [final_decision['type'], final_decision.get('source', 'UNKNOWN')], 
                    rr, position_size, "PAPER"
                )
        
        # Status update
        if iteration % 10 == 0:
            stats = risk_manager.get_stats()
            print(f"\n📊 Status: PnL ${stats['daily_pnl']:.2f} | "
                  f"Trades {stats['daily_trades']}/{MAX_DAILY_TRADES} | "
                  f"Open {stats['open_positions']}/{MAX_CONCURRENT_TRADES}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n🛑 Shutdown signal received...")
    print("="*80)
    
    performance.print_summary()
    
    if ENABLE_EXECUTION:
        print("\nDisconnecting from MT5...")
        disconnect()
    
    print("\n✅ AI-integrated system stopped")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    if ENABLE_EXECUTION:
        disconnect()
    
    raise

finally:
    print("AI-integrated trading system shutdown complete")
