# // turbo
"""
Velora AI Engine — Institutional Risk Manager
These rules CANNOT be overridden. They are hardcoded guardrails.
"""
import math
from datetime import datetime, date
from loguru import logger
from config.settings import config
from typing import Optional


class RiskManager:
    def __init__(self):
        self.daily_loss_tracker: dict[str, float] = {}
        self.daily_trade_count: dict[str, int] = {}

    def _today(self) -> str:
        return date.today().isoformat()

    def record_trade_result(self, pnl: float):
        today = self._today()
        self.daily_loss_tracker[today] = self.daily_loss_tracker.get(today, 0) + pnl
        self.daily_trade_count[today] = self.daily_trade_count.get(today, 0) + 1

    def get_daily_pnl(self) -> float:
        return self.daily_loss_tracker.get(self._today(), 0.0)

    def calculate_position_size(self, account_balance: float, sl_pips: float,
                                 pip_value: float, symbol: str) -> float:
        risk_amount = account_balance * config.MAX_RISK_PER_TRADE
        if sl_pips <= 0 or pip_value <= 0:
            return 0.01
        lots = risk_amount / (sl_pips * pip_value)
        lots = max(0.01, round(lots, 2))
        lots = min(lots, 10.0)  # hard cap
        return lots

    def check_trade_allowed(self, account: dict, open_positions: list) -> dict:
        balance = account.get("balance", 0)
        equity = account.get("equity", balance)
        daily_pnl = self.get_daily_pnl()

        # Rule 1: Max concurrent trades
        if len(open_positions) >= config.MAX_CONCURRENT_TRADES:
            return {"allowed": False, "reason": f"Max concurrent trades reached ({config.MAX_CONCURRENT_TRADES})"}

        # Rule 2: Daily loss limit
        if balance > 0:
            daily_loss_pct = abs(min(daily_pnl, 0)) / balance
            if daily_loss_pct >= config.MAX_DAILY_LOSS:
                return {"allowed": False, "reason": f"Daily loss limit hit ({daily_loss_pct:.1%})"}

        # Rule 3: Max drawdown
        if balance > 0:
            drawdown = (balance - equity) / balance
            if drawdown >= config.MAX_DRAWDOWN:
                return {"allowed": False, "reason": f"Max drawdown circuit breaker ({drawdown:.1%})"}

        return {"allowed": True, "reason": "All risk checks passed"}

    def calculate_sl_tp(self, entry: float, direction: str, atr: float,
                         digits: int, rr: float = 2.0) -> dict:
        sl_distance = atr * 1.5
        tp_distance = sl_distance * rr
        multiplier = 1 if direction == "BUY" else -1
        sl = round(entry - multiplier * sl_distance, digits)
        tp1 = round(entry + multiplier * tp_distance * 0.6, digits)
        tp2 = round(entry + multiplier * tp_distance, digits)
        sl_pips = round(sl_distance / (10 ** -digits), 1)
        return {"sl": sl, "tp1": tp1, "tp2": tp2, "sl_pips": sl_pips, "rr": rr}

    def is_news_blackout(self) -> bool:
        # Placeholder — integrate ForexFactory calendar API for real news filter
        # Returns False by default (no blackout) — extend with real calendar data
        return False

risk_manager = RiskManager()
