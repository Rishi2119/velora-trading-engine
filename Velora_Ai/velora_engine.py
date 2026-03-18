"""
Velora AI Trading Engine — Main Orchestrator
=============================================
Production inference loop that wires together all modules.

Usage:
    python velora_engine.py [--paper] [--symbol EURUSD] [--interval 60]

Architecture:
    MarketDataEngine
        → FeatureExtractionEngine
            → StrategyDetectionEngine
                → AIDecisionModel
                    → AIConfidenceFilter
                        → RiskManagementEngine
                            → TradeExecutionEngine
"""

import sys
import os
import time
import argparse
import csv
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import (CONFIDENCE_THRESHOLD, SYMBOLS, TIMEFRAME, JOURNAL_PATH)
from core.models          import Action, Regime
from core.market_data_engine   import MarketDataEngine
from core.feature_extraction   import FeatureExtractionEngine
from core.strategy_detection   import StrategyDetectionEngine
from core.risk_management      import RiskManagementEngine
from core.execution_engine     import TradeExecutionEngine
from train_model               import AIDecisionModel
from core.llm_decision_model   import LLMDecisionModel
from utils.logger              import get_logger
from backend.config.settings   import settings


log = get_logger("VeloraEngine")



# ─────────────────────────────────────────────────────────────────────────────
# TRADE JOURNAL
# ─────────────────────────────────────────────────────────────────────────────
# ── Global Locks ─────────────────────────────────────────────────────────────
JOURNAL_LOCK = threading.Lock()

def init_journal():
    os.makedirs("logs", exist_ok=True)
    if not os.path.exists(JOURNAL_PATH):
        with open(JOURNAL_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "symbol", "action", "strategy", "regime",
                "confidence", "entry", "sl", "tp", "lots", "ticket"
            ])
            writer.writeheader()

def log_trade(signal, regime: Regime, ticket):
    with JOURNAL_LOCK:
        with open(JOURNAL_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "symbol", "action", "strategy", "regime",
                "confidence", "entry", "sl", "tp", "lots", "ticket"
            ])
            writer.writerow({
                "timestamp":  datetime.utcnow().isoformat(),
                "symbol":     signal.symbol,
                "action":     signal.action.value,
                "strategy":   signal.strategy,
                "regime":     regime.value,
                "confidence": signal.confidence,
                "entry":      signal.entry_price,
                "sl":         signal.stop_loss,
                "tp":         signal.take_profit,
                "lots":       signal.lot_size,
                "ticket":     ticket,
            })


# ─────────────────────────────────────────────────────────────────────────────
# VELORA ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class VeloraEngine:
    """
    Main trading engine. Orchestrates all modules in a live inference loop.
    """

    def __init__(
        self,
        symbol:               str   = "EURUSD",
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        account_balance:      float = 10_000.0,
    ):
        self.symbol     = symbol
        self.threshold  = confidence_threshold
        self.running    = False

        log.info("═" * 55)
        log.info("  VELORA AI TRADING ENGINE — INITIALISING")
        log.info("═" * 55)

        # ── Instantiate all modules ───────────────────────────────────────────
        self.market_data = MarketDataEngine(symbol=symbol, timeframe=TIMEFRAME)
        self.feature_eng = FeatureExtractionEngine()
        self.strategy    = StrategyDetectionEngine()
        self.risk        = RiskManagementEngine(account_balance=account_balance)
        self.executor    = TradeExecutionEngine()

        if settings.AI_ENGINE_TYPE == "openrouter":
            log.info(f"Using OPENROUTER (Model: {settings.OPENROUTER_MODEL}) for decision making.")
            self.ai_model = LLMDecisionModel()
        else:
            log.info("Using LOCAL ML model for decision making.")
            self.ai_model = AIDecisionModel()
            
        self.ai_model.load()

        if not self.ai_model.is_ready:
            log.warning("⚠  AI model not ready.")
            if settings.AI_ENGINE_TYPE == "openrouter":
                log.warning("   Check OPENROUTER_API_KEY in .env")
            else:
                log.warning("   Run: python train_model.py to train local model")
            log.warning("   Engine will run in RULE-ONLY mode (NO_TRADE fallback).")


        init_journal()
        log.info(f"Engine ready | Symbol: {symbol} | Threshold: {confidence_threshold}")

    # ── Core inference cycle ──────────────────────────────────────────────────

    def run_once(self) -> dict:
        """
        Execute one full inference cycle.
        Returns a dict with all intermediate outputs (useful for testing/API).
        """
        result = {
            "timestamp":  datetime.utcnow().isoformat(),
            "symbol":     self.symbol,
            "action":     "NO_TRADE",
            "confidence": 0.0,
            "strategy":   None,
            "regime":     None,
            "signal":     None,
            "ticket":     None,
            "reason":     None,
        }

        # ── Step 1: Fetch market data ─────────────────────────────────────────
        state = self.market_data.fetch()
        if state is None:
            result["reason"] = "No market data"
            return result

        # ── Step 2: Extract features ──────────────────────────────────────────
        features = self.feature_eng.extract(state)

        # ── Step 3: Detect strategy + regime ─────────────────────────────────
        strategy_type, regime = self.strategy.detect(features)
        result["strategy"] = strategy_type
        result["regime"]   = regime.value

        # ── Step 4: AI prediction ─────────────────────────────────────────────
        if settings.AI_ENGINE_TYPE == "openrouter":
             pred = self.ai_model.predict(features, state=state)
        else:
             pred = self.ai_model.predict(features) if self.ai_model.is_ready else \
                {"action": "NO_TRADE", "confidence": 0.0}


        action_str = pred["action"]
        confidence = pred["confidence"]

        result["action"]     = action_str
        result["confidence"] = confidence

        log.info(f"[{self.symbol}] {action_str} | conf={confidence:.2f} | "
                 f"strategy={strategy_type} | regime={regime.value}")

        # ── Step 5: AI Confidence Filter ──────────────────────────────────────
        if action_str == "NO_TRADE":
            result["reason"] = "Model predicts NO_TRADE"
            return result

        if confidence < self.threshold:
            result["reason"] = f"Confidence {confidence:.2f} < threshold {self.threshold}"
            log.info(f"  ↳ Filtered out: {result['reason']}")
            return result

        # ── Step 6: Risk management → build signal ────────────────────────────
        action = Action(action_str)
        signal = self.risk.build_signal(
            action=action, state=state, features=features,
            confidence=confidence, strategy=strategy_type,
        )

        if signal is None:
            result["reason"] = "Risk management blocked trade"
            return result

        result["signal"] = signal

        # ── Step 7: Execute ───────────────────────────────────────────────────
        ticket = self.executor.execute(signal)
        if ticket:
            signal.ticket = ticket
            self.risk.on_trade_opened()
            log_trade(signal, regime, ticket)
            result["ticket"] = ticket
            result["reason"] = "Trade executed"
            log.info(f"  ✅ Executed | Ticket #{ticket}")
        else:
            result["reason"] = "Execution failed"

        return result

    # ── Live loop ─────────────────────────────────────────────────────────────

    def run(self, interval_seconds: int = 60):
        """
        Start the live trading loop. Polls every `interval_seconds`.
        Press Ctrl+C to stop cleanly.
        """
        self.running = True
        log.info(f"🚀 Live loop started | Interval: {interval_seconds}s")
        log.info("   Press Ctrl+C to stop.")

        try:
            while self.running:
                try:
                    self.run_once()
                except Exception as e:
                    log.error(f"Cycle error: {e}", exc_info=True)

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            log.info("Shutdown signal received.")
        finally:
            self.shutdown()

    def stop(self):
        self.running = False

    def shutdown(self):
        log.info("Shutting down Velora Engine...")
        self.market_data.shutdown()
        self.executor.shutdown()
        log.info("Engine stopped cleanly.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Velora AI Trading Engine")
    parser.add_argument("--symbol",     default="EURUSD",      help="Trading symbol")
    parser.add_argument("--interval",   default=60, type=int,  help="Poll interval (seconds)")
    parser.add_argument("--threshold",  default=CONFIDENCE_THRESHOLD, type=float,
                        help="AI confidence threshold")
    parser.add_argument("--balance",    default=10000.0, type=float,
                        help="Starting account balance")
    parser.add_argument("--once",       action="store_true",
                        help="Run one inference cycle and exit")
    args = parser.parse_args()

    engine = VeloraEngine(
        symbol               = args.symbol,
        confidence_threshold = args.threshold,
        account_balance      = args.balance,
    )

    if args.once:
        result = engine.run_once()
        print(f"\nResult: {result}")
        engine.shutdown()
    else:
        engine.run(interval_seconds=args.interval)
