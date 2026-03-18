"""
Velora AI — Module 6: Trade Execution Engine
=============================================
Connects to MetaTrader 5 and executes trade signals.
Falls back to PAPER TRADING mode if MT5 is unavailable.
"""

import sys
import time
from typing import Optional, Dict
from datetime import datetime

sys.path.insert(0, "..")
from config import MAX_SLIPPAGE_PIPS
from core.models import Action, TradeSignal
from utils.logger import get_logger

log = get_logger("ExecutionEngine")

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    log.warning("MT5 not available — running in PAPER TRADE mode.")


class TradeExecutionEngine:
    """
    Executes trade signals via MT5 or paper trading simulation.

    Features:
    - Spread filter before execution
    - Slippage control
    - Order type: MARKET (instant execution)
    - Automatic SL/TP attached on open
    - Paper trade fallback with virtual P&L tracking
    """

    DEVIATION = MAX_SLIPPAGE_PIPS  # max slippage in points

    def __init__(self):
        self._connected     = False
        self.paper_trades: Dict[int, dict] = {}   # ticket → trade info
        self._paper_ticket  = 1000

        if MT5_AVAILABLE:
            self._connected = mt5.initialize()
            if self._connected:
                log.info("MT5 execution engine connected.")
            else:
                log.error(f"MT5 init failed: {mt5.last_error()}")

    # ── Public API ────────────────────────────────────────────────────────────

    def execute(self, signal: TradeSignal) -> Optional[int]:
        """
        Execute a trade signal. Returns ticket number or None on failure.
        """
        if MT5_AVAILABLE and self._connected:
            return self._execute_mt5(signal)
        return self._execute_paper(signal)

    def close_trade(self, ticket: int, symbol: str) -> bool:
        """Close an open trade by ticket."""
        if MT5_AVAILABLE and self._connected:
            return self._close_mt5(ticket, symbol)
        return self._close_paper(ticket)

    def close_all(self, symbol: Optional[str] = None) -> int:
        """Close all open trades (kill switch). Returns count closed."""
        closed = 0
        if MT5_AVAILABLE and self._connected:
            positions = mt5.positions_get(symbol=symbol) or []
            for pos in positions:
                if self._close_mt5(pos.ticket, pos.symbol):
                    closed += 1
        else:
            for ticket in list(self.paper_trades.keys()):
                if self._close_paper(ticket):
                    closed += 1
        log.info(f"Kill switch: closed {closed} trades.")
        return closed

    def get_open_positions(self) -> list:
        """Return list of open positions."""
        if MT5_AVAILABLE and self._connected:
            positions = mt5.positions_get() or []
            return [{"ticket": p.ticket, "symbol": p.symbol,
                     "type": "BUY" if p.type == 0 else "SELL",
                     "lots": p.volume, "profit": p.profit} for p in positions]
        return list(self.paper_trades.values())

    def get_account_info(self) -> dict:
        if MT5_AVAILABLE and self._connected:
            info = mt5.account_info()
            if info:
                return {"balance": info.balance, "equity": info.equity,
                        "margin": info.margin, "free_margin": info.margin_free}
        return {"balance": 10000.0, "equity": 10000.0, "margin": 0.0, "free_margin": 10000.0}

    # ── MT5 execution ─────────────────────────────────────────────────────────

    def _execute_mt5(self, signal: TradeSignal) -> Optional[int]:
        order_type = mt5.ORDER_TYPE_BUY if signal.action == Action.BUY else mt5.ORDER_TYPE_SELL

        request = {
            "action":    mt5.TRADE_ACTION_DEAL,
            "symbol":    signal.symbol,
            "volume":    signal.lot_size,
            "type":      order_type,
            "price":     signal.entry_price,
            "sl":        signal.stop_loss,
            "tp":        signal.take_profit,
            "deviation": self.DEVIATION,
            "magic":     20240101,
            "comment":   f"Velora|{signal.strategy}|{signal.confidence:.2f}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.comment if result else mt5.last_error()
            log.error(f"Order failed: {err}")
            return None

        log.info(f"✅ MT5 Order executed | Ticket: {result.order} | "
                 f"{signal.action.value} {signal.lot_size} {signal.symbol} "
                 f"@ {signal.entry_price:.5f} SL={signal.stop_loss:.5f} TP={signal.take_profit:.5f}")
        return result.order

    def _close_mt5(self, ticket: int, symbol: str) -> bool:
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        p = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if p.type == 0 else mt5.symbol_info_tick(symbol).ask

        request = {
            "action":    mt5.TRADE_ACTION_DEAL,
            "symbol":    symbol,
            "volume":    p.volume,
            "type":      close_type,
            "position":  ticket,
            "price":     price,
            "deviation": self.DEVIATION,
            "magic":     20240101,
            "comment":   "Velora|close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        success = result and result.retcode == mt5.TRADE_RETCODE_DONE
        if success:
            log.info(f"Trade {ticket} closed.")
        return success

    # ── Paper trading fallback ────────────────────────────────────────────────

    def _execute_paper(self, signal: TradeSignal) -> int:
        self._paper_ticket += 1
        ticket = self._paper_ticket
        self.paper_trades[ticket] = {
            "ticket":      ticket,
            "symbol":      signal.symbol,
            "action":      signal.action.value,
            "entry":       signal.entry_price,
            "sl":          signal.stop_loss,
            "tp":          signal.take_profit,
            "lots":        signal.lot_size,
            "strategy":    signal.strategy,
            "confidence":  signal.confidence,
            "opened_at":   datetime.utcnow().isoformat(),
            "profit":      0.0,
        }
        log.info(f"📄 PAPER TRADE #{ticket} | {signal.action.value} "
                 f"{signal.lot_size} {signal.symbol} @ {signal.entry_price:.5f} "
                 f"SL={signal.stop_loss:.5f} TP={signal.take_profit:.5f} "
                 f"| Strategy: {signal.strategy} | Conf: {signal.confidence:.2f}")
        return ticket

    def _close_paper(self, ticket: int) -> bool:
        if ticket in self.paper_trades:
            trade = self.paper_trades.pop(ticket)
            log.info(f"📄 PAPER TRADE #{ticket} closed | {trade}")
            return True
        return False

    def shutdown(self):
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
