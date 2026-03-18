"""
Autonomous Engine Loop.
Orchestrates the entire trading process in a background thread.
"""
import logging
import threading
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC

from backend.app.core.config import config
from backend.app.execution.mt5_connection import mt5_conn
from backend.app.engine.feature_engine import feature_engine
from backend.app.strategies.strategy_manager import strategy_manager, SignalResult
from backend.app.risk.risk_manager import risk_manager, RiskDecision
from backend.app.execution.trade_executor import trade_executor
from backend.app.analytics.journal import trade_journal
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AutonomousEngine:
    """
    The central autonomous trading loop.
    Controls the lifecycle of data extraction, feature engineering,
    strategy evaluation, risk management, and order execution.
    """
    
    def __init__(self):
        self._shutdown_event = threading.Event()
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False
        
        # In-memory tracking to prevent multiple trades on the same candle
        self._last_processed_candle: Dict[str, datetime] = {}
        
    @property
    def is_running(self) -> bool:
        return self._running
        
    def start(self) -> bool:
        """Start the autonomous engine loop in a new thread."""
        if self._running:
            logger.warning("Engine is already running.")
            return False
            
        logger.info("Starting Autonomous Engine...")
        
        # Pre-flight check: Try to connect to MT5 (unless paper)
        if config.engine_mode != "paper":
            if not mt5_conn.is_connected:
                success = mt5_conn.connect(retries=3)
                if not success:
                    logger.error("Failed to connect to MT5. Cannot start Engine in LIVE mode.")
                    return False
            # Start the MT5 connection watchdog
            mt5_conn.start_watchdog()
            
        self._shutdown_event.clear()
        self._running = True
        
        self._loop_thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="AutonomousLoop"
        )
        self._loop_thread.start()
        logger.info("Autonomous Engine started successfully.")
        return True
        
    def stop(self) -> None:
        """Gracefully stop the autonomous engine."""
        if not self._running:
            return
            
        logger.info("Stopping Autonomous Engine...")
        self._shutdown_event.set()
        
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5.0)
            
        self._running = False
        logger.info("Autonomous Engine stopped gracefully.")
        
    def _run_loop(self) -> None:
        """The main execution loop."""
        
        # We check symbol info and account periodically instead of every sub-second tick
        stats_update_counter = 0
        
        while not self._shutdown_event.is_set():
            try:
                # 1. MT5 Connectivity Check
                if config.engine_mode != "paper" and not mt5_conn.is_connected:
                    logger.warning("Engine loop paused: MT5 disconnected. Waiting for watchdog to reconnect...")
                    time.sleep(5)
                    continue
                    
                # 2. Account & State Sync
                acc_info = self._get_account_balance()
                if acc_info is None:
                    time.sleep(1)
                    continue
                    
                balance = acc_info.get("balance", config.demo_account_balance)
                free_margin = acc_info.get("margin_free", balance)
                
                # Daily reset (Midnight clear constraints)
                risk_manager.reset_daily_if_needed(balance=balance)
                
                # Sync MT5 Open Positions
                live_positions = mt5_conn.get_positions()
                risk_manager.sync_open_positions(live_positions)
                
                # 3. Process each authorized symbol
                symbols = config.active_symbols
                max_workers = min(len(symbols) if symbols else 1, 10)
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for symbol in symbols:
                        if self._shutdown_event.is_set():
                            break
                        futures.append(executor.submit(self._process_symbol, symbol, balance, free_margin))
                    
                    # Await completion
                    for f in futures:
                        try:
                            f.result()
                        except Exception as e:
                            logger.error(f"Error in parallel symbol processing: {e}", exc_info=True)
                    
                # Rate limit the main loop (1 second loop is generally fast enough)
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Critical error in AutonomousLoop: {e}", exc_info=True)
                time.sleep(5)  # Backoff on critical failure to prevent rapid crashing
                
    def _get_account_balance(self) -> Optional[Dict[str, float]]:
        if config.engine_mode == "paper":
            # Return demo info
            return {
                "balance": config.demo_account_balance,
                "margin_free": config.demo_account_balance,
            }
        else:
            acc = mt5_conn.get_account_info()
            if acc:
                return {
                    "balance": acc.get("balance", 0.0),
                    "margin_free": acc.get("margin_free", 0.0)
                }
            return None

    def _process_symbol(self, symbol: str, balance: float, free_margin: float) -> None:
        """Process the trading loop for a single symbol."""
        # A. Fetch Data
        # We need historical bars. 250 is usually enough for EMA200 + buffers
        df = mt5_conn.get_rates(symbol, config.timeframe, 250)
        
        if df is None or df.empty:
            if config.engine_mode == "paper":
                # In strict paper mode without MT5, mock a single data point if absolutely needed for tests
                # This should ideally be handled by a historical mock broker, but for the basic pipeline:
                pass 
            return
            
        current_candle_time = df.iloc[-1]['time']
        
        # B. New Candle Gating
        # Strictly run signals only once per closed bar (avoid multiple orders on same candle noise)
        last_processed = self._last_processed_candle.get(symbol)
        if last_processed and current_candle_time <= last_processed:
            # We already processed this candle.
            # We skip. We might want to allow TP/SL trailing here later.
            return
            
        # C. Feature Engineering
        features = feature_engine.compute(symbol, df)
        if features is None:
            return
            
        # D. Strategy Evaluation
        signal = strategy_manager.evaluate_all(symbol, features)
        
        if not signal:
            # No signal fired. We update the processed time to prevent re-evaluating until next candle.
            self._last_processed_candle[symbol] = current_candle_time
            return
            
        logger.info(f"Signal Generated: {signal.direction} {symbol} by {signal.strategy_name} (Conf: {signal.confidence:.1f}%)")
        
        # E. Risk Management Gate
        # Fetch symbol specifics
        sym_info = mt5_conn.get_symbol_info(symbol) if config.engine_mode == "live" else {}
        point_size = sym_info.get("point", 0.00001)
        tick_value = sym_info.get("trade_tick_value", 1.0)
        contract_size = sym_info.get("trade_contract_size", 100000.0)
        
        if config.engine_mode == "paper":
            # mock values if MT5 is missing
            point_size = 0.00001
            tick_value = 1.0
            contract_size = 100000.0
            
        risk_decision = risk_manager.validate(
            signal=signal,
            balance=balance,
            free_margin=free_margin,
            tick_value=tick_value,
            point_size=point_size,
            contract_size=contract_size
        )
        
        if not risk_decision.approved:
            logger.info(f"Risk Rejected: {risk_decision.reason}")
            # Do NOT update last_processed_candle, maybe price changes and Risk approves later in the same bar?
            # Actually, usually safer to wait for next bar to avoid spam logs.
            self._last_processed_candle[symbol] = current_candle_time
            return
            
        # F. Execution
        exec_result = trade_executor.execute_trade(signal, risk_decision)
        
        if exec_result.get("status") == "FILLED":
            logger.info(f"TRADE SUCCESS: {exec_result}")
            # Mark processed
            self._last_processed_candle[symbol] = current_candle_time
            
            # G. Journaling (placeholder for Phase 9 / supabase write)
            self._journal_trade(signal, risk_decision, exec_result)
        else:
            logger.warning(f"TRADE FAILED: {exec_result.get('reason')}")
            # If rejected by broker, mark processed to avoid hammering the broker with failing orders
            self._last_processed_candle[symbol] = current_candle_time
            
    def _journal_trade(self, signal: SignalResult, decision: RiskDecision, exec_result: Dict[str, Any]) -> None:
        """Write trade to SQLite / Supabase using resilient journal."""
        trade_data = {
            "ticket": exec_result.get("ticket"),
            "symbol": signal.symbol,
            "direction": signal.direction,
            "lots": decision.approved_lots,
            "entry_price": exec_result.get("entry_price", signal.entry),
            "exit_price": 0.0,
            "sl": decision.adjusted_sl,
            "tp": decision.adjusted_tp,
            "pnl": 0.0,
            "strategy_name": signal.strategy_name,
            "entry_time": datetime.now(UTC).isoformat(),
            "exit_time": None
        }
        
        # We can't use await securely inside a non-async loop without creating a task via asyncio loop
        # But log_trade returns an async task/coroutine, TradeJournal already wraps it in asyncio.create_task internally if it's sync. Wait, log_trade is "async def".
        
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(trade_journal.log_trade(trade_data))
        except RuntimeError:
            # If no event loop in this thread, just run it
            asyncio.run(trade_journal.log_trade(trade_data))


# Singleton
engine = AutonomousEngine()
