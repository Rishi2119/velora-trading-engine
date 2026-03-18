"""
Velora AI — Module 9: Backtesting Engine
==========================================
Replays historical data through the full Velora pipeline
and computes institutional-grade performance metrics.

Usage:
    python backtesting/backtest_engine.py
"""

import sys
import os
import numpy as np
import pandas as pd
from typing import List, Optional
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (CONFIDENCE_THRESHOLD, RISK_PER_TRADE,
                    MIN_RR_RATIO, DATA_PATH)
from core.models import (Action, MarketState, Features, TradeSignal,
                         BacktestResult, Regime)
from train_model import AIDecisionModel, ALL_FEATURES
from utils.logger import get_logger

log = get_logger("Backtester")


# ─────────────────────────────────────────────────────────────────────────────
# SIMPLE TRADE SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

class SimulatedTrade:
    def __init__(self, action: Action, entry: float, sl: float, tp: float,
                 lot: float, risk_usd: float):
        self.action   = action
        self.entry    = entry
        self.sl       = sl
        self.tp       = tp
        self.lot      = lot
        self.risk_usd = risk_usd
        self.closed   = False
        self.pnl      = 0.0
        self.result   = "open"

    def update(self, high: float, low: float) -> bool:
        """Check if TP or SL was hit. Returns True if trade closed."""
        if self.closed:
            return True

        if self.action == Action.BUY:
            if low <= self.sl:
                self.pnl    = -self.risk_usd
                self.result = "loss"
                self.closed = True
            elif high >= self.tp:
                self.pnl    = self.risk_usd * MIN_RR_RATIO
                self.result = "win"
                self.closed = True

        elif self.action == Action.SELL:
            if high >= self.sl:
                self.pnl    = -self.risk_usd
                self.result = "loss"
                self.closed = True
            elif low <= self.tp:
                self.pnl    = self.risk_usd * MIN_RR_RATIO
                self.result = "win"
                self.closed = True

        return self.closed


# ─────────────────────────────────────────────────────────────────────────────
# BACKTESTING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class BacktestEngine:
    """
    Dataset-based backtester that feeds each row through the AI model
    and simulates trade outcomes using fixed RR logic.
    """

    def __init__(self, model: AIDecisionModel, initial_balance: float = 10_000.0):
        self.model           = model
        self.initial_balance = initial_balance

    # ── Main entry ────────────────────────────────────────────────────────────

    def run(self, data_path: str = DATA_PATH,
            confidence_threshold: float = CONFIDENCE_THRESHOLD) -> BacktestResult:
        """
        Run backtest on the training/test dataset.
        Returns BacktestResult with all metrics.
        """
        df = pd.read_csv(data_path)
        log.info(f"Backtesting on {len(df)} rows...")

        balance      = self.initial_balance
        equity_curve = [balance]
        trades: List[dict] = []

        for _, row in df.iterrows():
            features = self._row_to_features(row)
            pred     = self.model.predict(features)

            action_str = pred["action"]
            confidence = pred["confidence"]

            if action_str == "NO_TRADE" or confidence < confidence_threshold:
                continue

            action = Action(action_str)
            risk   = balance * RISK_PER_TRADE
            reward = risk * MIN_RR_RATIO

            # Simulate outcome: use actual label as ground truth
            actual_action = row.get("action", "NO_TRADE")

            if actual_action == action_str:
                pnl    = reward
                result = "win"
            elif actual_action == "NO_TRADE":
                # Predicted trade but actual was no-trade — penalise
                pnl    = -risk * 0.5
                result = "scratch"
            else:
                pnl    = -risk
                result = "loss"

            balance += pnl
            equity_curve.append(balance)
            trades.append({
                "action":     action_str,
                "actual":     actual_action,
                "confidence": confidence,
                "result":     result,
                "pnl":        pnl,
                "balance":    balance,
                "strategy":   row.get("strategy_type", "unknown"),
            })

        return self._compute_metrics(trades, equity_curve)

    # ── Metric computation ────────────────────────────────────────────────────

    def _compute_metrics(self, trades: List[dict],
                         equity_curve: List[float]) -> BacktestResult:
        if not trades:
            log.warning("No trades in backtest.")
            return BacktestResult(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        total   = len(trades)
        wins    = sum(1 for t in trades if t["result"] == "win")
        losses  = sum(1 for t in trades if t["result"] == "loss")
        win_rate = wins / total if total else 0

        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
        gross_loss   = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Max drawdown
        eq = np.array(equity_curve)
        running_max = np.maximum.accumulate(eq)
        drawdowns   = (running_max - eq) / running_max
        max_drawdown = float(drawdowns.max())

        # Sharpe ratio (daily-ish returns)
        pnls   = np.array([t["pnl"] for t in trades])
        mean_r = pnls.mean()
        std_r  = pnls.std() + 1e-9
        sharpe = (mean_r / std_r) * np.sqrt(252)   # annualised

        total_pnl = equity_curve[-1] - self.initial_balance

        result = BacktestResult(
            total_trades  = total,
            wins          = wins,
            losses        = losses,
            win_rate      = round(win_rate, 4),
            profit_factor = round(profit_factor, 4),
            max_drawdown  = round(max_drawdown, 4),
            sharpe_ratio  = round(float(sharpe), 4),
            total_pnl     = round(total_pnl, 2),
            equity_curve  = equity_curve,
        )

        log.info(f"\n{'='*50}")
        log.info(f"BACKTEST RESULTS")
        log.info(f"{'='*50}")
        log.info(f"Total Trades:   {total}")
        log.info(f"Win Rate:       {win_rate*100:.1f}%")
        log.info(f"Profit Factor:  {profit_factor:.2f}")
        log.info(f"Max Drawdown:   {max_drawdown*100:.1f}%")
        log.info(f"Sharpe Ratio:   {sharpe:.2f}")
        log.info(f"Total PnL:      ${total_pnl:+.2f}")
        log.info(f"{'='*50}")

        return result

    def _row_to_features(self, row) -> Features:
        """Convert a CSV row (dict/Series) back to a Features object."""
        def to_bool(v):
            if isinstance(v, bool): return v
            if isinstance(v, str):  return v.lower() == "true"
            return bool(v)

        return Features(
            trend_direction             = str(row.get("trend_direction", "sideways")),
            structure_break             = to_bool(row.get("structure_break", False)),
            liquidity_sweep             = to_bool(row.get("liquidity_sweep", False)),
            pullback                    = to_bool(row.get("pullback", False)),
            momentum_strength           = float(row.get("momentum_strength", 0.5)),
            volatility                  = float(row.get("volatility", 0.5)),
            support_resistance_strength = float(row.get("support_resistance_strength", 0.5)),
            session                     = str(row.get("session", "Asia")),
            spread                      = float(row.get("spread", 0.1)),
            strategy_type               = str(row.get("strategy_type", "intraday_momentum")),
        )

    def print_strategy_breakdown(self, data_path: str = DATA_PATH,
                                  confidence_threshold: float = CONFIDENCE_THRESHOLD):
        """Print per-strategy performance breakdown."""
        df = pd.read_csv(data_path)
        strategy_stats = {}

        for _, row in df.iterrows():
            features = self._row_to_features(row)
            pred     = self.model.predict(features)
            strat    = row.get("strategy_type", "unknown")
            actual   = row.get("action", "NO_TRADE")

            if strat not in strategy_stats:
                strategy_stats[strat] = {"correct": 0, "total": 0}

            if pred["confidence"] >= confidence_threshold:
                strategy_stats[strat]["total"] += 1
                if pred["action"] == actual:
                    strategy_stats[strat]["correct"] += 1

        log.info("\nStrategy Breakdown:")
        for strat, stats in strategy_stats.items():
            acc = stats["correct"] / max(stats["total"], 1)
            log.info(f"  {strat:<22} | Trades: {stats['total']:>4} | "
                     f"Accuracy: {acc*100:.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
if __name__ == "__main__":
    from backend.config.settings import settings
    
    if settings.AI_ENGINE_TYPE == "openrouter":
        from core.llm_decision_model import LLMDecisionModel
        model = LLMDecisionModel()
        model.load()
    else:
        model = AIDecisionModel()
        model.load()

        if not model.is_ready:
            print("❌  Model not found. Run: python train_model.py")
            sys.exit(1)

    engine = BacktestEngine(model)
    result = engine.run()
    engine.print_strategy_breakdown()
