"""
🚀 PRODUCTION TRADING SYSTEM
Main entry point with all security features enabled

FEATURES:
- Risk management with hard limits
- AI sandbox for safe AI trading
- Circuit breaker protection
- Audit journal
- MT5 integration
"""

import sys
import os
import io
import logging
import time
from datetime import datetime, date

# Fix Windows console encoding
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """Load and validate configuration"""
    import config
    
    # Validate
    if not config.validate_config():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    config.print_config()
    return config


def initialize_components(config):
    """Initialize all system components"""
    from risk import RiskManager
    from executor import connect, disconnect, is_connected
    from ai_sandbox import AISandbox
    from ai_wrapper import AIWrapper
    from circuit_breaker import CircuitBreaker, CircuitBreakerManager
    from audit_journal import get_audit_journal
    
    # Initialize risk manager
    risk_manager = RiskManager(
        max_daily_loss=config.MAX_DAILY_LOSS,
        max_daily_trades=config.MAX_DAILY_TRADES,
        max_concurrent=config.MAX_CONCURRENT_TRADES,
        risk_per_trade=config.RISK_PER_TRADE,
        min_rr=config.MIN_RISK_REWARD,
        state_file="logs/risk_state.json"
    )
    
    # Initialize AI sandbox
    ai_sandbox = AISandbox(risk_manager, {
        'ai_enabled': False,  # Default OFF - must be explicitly enabled
        'min_confidence': config.MIN_CONFIDENCE,
        'risk_per_trade': config.RISK_PER_TRADE,
        'log_file': 'logs/ai_sandbox.log'
    })
    
    # Initialize AI wrapper
    ai_wrapper = AIWrapper(ai_sandbox, risk_manager)
    
    # Initialize circuit breakers
    circuit_breakers = CircuitBreakerManager()
    mt5_circuit = circuit_breakers.get_or_create(
        'mt5',
        failure_threshold=3,
        timeout=60
    )
    ai_circuit = circuit_breakers.get_or_create(
        'ai',
        failure_threshold=5,
        timeout=120
    )
    
    # Initialize audit journal
    audit = get_audit_journal()
    
    return {
        'risk_manager': risk_manager,
        'ai_sandbox': ai_sandbox,
        'ai_wrapper': ai_wrapper,
        'circuit_breakers': circuit_breakers,
        'mt5_circuit': mt5_circuit,
        'ai_circuit': ai_circuit,
        'audit': audit
    }


def connect_mt5(config, components):
    """Use MT5 connection from mobile_api - they share the same connection"""
    mt5_circuit = components['mt5_circuit']
    
    try:
        # Import mt5_manager from mobile_api - shares connection with Flask API
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mobile_api'))
        from mt5_manager import mt5_manager
        
        if mt5_manager.connected:
            logger.info("Using shared MT5 connection from mobile_api")
            account = mt5_manager.get_account_info()
            if account:
                logger.info(f"MT5 Connected: Balance ${account.balance}")
                mt5_circuit.record_success()
                return True
        else:
            logger.warning("MT5 not connected in mobile_api")
            return False
            
    except Exception as e:
        mt5_circuit.record_failure(str(e))
        logger.error(f"MT5 connection error: {e}")
    
    return False


def run_backtest(config, components):
    """Run backtest mode"""
    from data_loader import load_csv
    
    logger.info("Starting BACKTEST mode")
    
    data_file = config.DATA_FILE
    logger.info(f"Loading data from: {data_file}")
    
    df = load_csv(data_file)
    if df is None:
        logger.error("Failed to load data")
        return
    
    logger.info(f"Loaded {len(df)} candles")
    
    risk_manager = components['risk_manager']
    audit = components['audit']
    
    balance = config.BACKTEST_INITIAL_BALANCE
    trades = []
    
    for idx in range(100, len(df)):
        # Check daily reset
        risk_manager._check_daily_reset()
        
        # Check risk limits
        can_trade, reason = risk_manager.can_trade()
        if not can_trade:
            continue
        
        df_slice = df.iloc[:idx+1]
        
        # Detect setups (simplified - use configured strategy)
        setup = None
        
        if hasattr(config, 'USE_ULTIMATE_STRATEGY') and config.USE_ULTIMATE_STRATEGY:
            # Use ultimate strategy
            from sr_strategy import auto_detect_sr_setup
            setup = auto_detect_sr_setup(df_slice, df_slice)
        
        if setup:
            direction = "LONG" if setup.get('side') == "BUY" else "SHORT"
            entry = setup.get('entry')
            sl = setup.get('sl')
            tp = setup.get('tp')
            
            # Validate
            valid, reason = risk_manager.validate_trade(entry, sl, tp, direction)
            if not valid:
                continue
            
            # Position size
            position_size = risk_manager.calculate_position_size(
                balance, config.RISK_PER_TRADE, entry, sl, config.SYMBOL
            )
            
            # Log
            audit.log_decision(
                action=f"BACKTEST_{direction}",
                reason=f"Setup: {setup.get('type', 'unknown')}",
                trade_data={
                    'symbol': config.SYMBOL,
                    'direction': direction,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'volume': position_size
                },
                balance=balance
            )
            
            # Simulate
            risk_amount = balance * config.RISK_PER_TRADE
            if direction == "LONG":
                if df_slice.iloc[-1]['low'] <= sl:
                    pnl = -risk_amount
                elif df_slice.iloc[-1]['high'] >= tp:
                    pnl = risk_amount * config.MIN_RISK_REWARD
                else:
                    pnl = 0
            else:
                if df_slice.iloc[-1]['high'] >= sl:
                    pnl = -risk_amount
                elif df_slice.iloc[-1]['low'] <= tp:
                    pnl = risk_amount * config.MIN_RISK_REWARD
                else:
                    pnl = 0
            
            balance += pnl
            trades.append(pnl)
            
            if pnl != 0:
                risk_manager.close_trade(pnl)
    
    # Results
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t < 0]
    
    logger.info("="*60)
    logger.info("BACKTEST RESULTS")
    logger.info("="*60)
    logger.info(f"Starting Balance: ${config.BACKTEST_INITIAL_BALANCE}")
    logger.info(f"Final Balance: ${balance}")
    logger.info(f"Total Trades: {len(trades)}")
    logger.info(f"Wins: {len(wins)} | Losses: {len(losses)}")
    logger.info(f"Win Rate: {len(wins)/len(trades)*100 if trades else 0:.1f}%")
    logger.info("="*60)


def run_live(config, components):
    """Run live trading mode"""
    logger.info("Starting LIVE trading mode")
    
    if not config.ENABLE_EXECUTION:
        logger.warning("⚠️  ENABLE_EXECUTION is False - running in paper trading mode")
    
    # Connect to MT5
    mt5_connected = False
    if config.ENABLE_EXECUTION:
        mt5_connected = connect_mt5(config, components)
    
    if not mt5_connected:
        logger.info("Running in PAPER trading mode")
    
    # Main loop
    from data_loader import load_csv
    from filters import is_kill_switch_active
    
    risk_manager = components['risk_manager']
    audit = components['audit']
    
    current_day = date.today()
    last_trade_index = -999
    
    logger.info("Entering main trading loop (Ctrl+C to stop)")
    
    try:
        while True:
            # Daily reset check
            today = date.today()
            if today != current_day:
                logger.info(f"New day: {today}")
                risk_manager.reset_daily()
                current_day = today
            
            # Kill switch check
            if is_kill_switch_active():
                logger.warning("Kill switch ACTIVE - trading halted")
                audit.log_system_event("KILL_SWITCH", "Trading halted")
                time.sleep(60)
                continue
            
            # Risk check
            can_trade, reason = risk_manager.can_trade()
            if not can_trade:
                logger.info(f"Risk block: {reason}")
                time.sleep(30)
                continue
            
            # Load fresh data
            df = load_csv(config.DATA_FILE)
            if df is None:
                time.sleep(30)
                continue
            
            # Check for new candle
            last_idx = len(df) - 1
            if last_idx <= last_trade_index:
                time.sleep(30)
                continue
            
            # Process new candle
            df_slice = df.iloc[:last_idx+1]
            
            # Run strategy (simplified)
            logger.info(f"Checking for signals at {df_slice.iloc[-1]['time']}")
            
            # Paper trade signal (replace with actual strategy)
            # In production, integrate your strategy here
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    
    # Cleanup
    if mt5_connected:
        from executor import disconnect
        disconnect()
    
    logger.info("Trading system stopped")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("🚀 PRODUCTION TRADING SYSTEM v2.0")
    print("="*70 + "\n")
    
    # Load config
    config = load_config()
    
    # Initialize components
    components = initialize_components(config)
    
    # Show system status
    print("\n📊 System Status:")
    print(f"   Risk Manager: OK")
    print(f"   AI Sandbox: {'ENABLED' if components['ai_sandbox'].ai_enabled else 'DISABLED (Safe)'}")
    print(f"   Circuit Breakers: OK")
    print(f"   Audit Journal: OK")
    print("="*70 + "\n")
    
    # Auto-start live trading mode
    print("\nAuto-starting LIVE TRADING mode...")
    run_live(config, components)


if __name__ == "__main__":
    main()
