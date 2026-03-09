"""
MT5 Manager — Persistent MetaTrader 5 connection manager.
Keeps a live session so all Flask endpoints can read real market data.
"""

import os
import json
import threading
from datetime import datetime, timedelta

MT5_AVAILABLE = False
mt5 = None

try:
    import MetaTrader5 as _mt5
    mt5 = _mt5
    MT5_AVAILABLE = True
except ImportError:
    pass


class MT5Manager:
    """Thread-safe MetaTrader 5 session manager."""

    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.account_info_cache = None
        self.last_error = None
        self.credentials = {}

    # ─── Connection ──────────────────────────────────────────────────

    def connect(self, account: int, password: str, server: str) -> dict:
        """Initialize MT5 and log in. Returns status dict."""
        if not MT5_AVAILABLE:
            self.connected = False
            self.last_error = (
                "MetaTrader5 package not installed. Run: pip install MetaTrader5"
            )
            return {"connected": False, "error": self.last_error}

        with self._lock:
            # Shutdown first if already running
            try:
                mt5.shutdown()
            except Exception:
                pass

            if not mt5.initialize():
                err = mt5.last_error()
                self.connected = False
                self.last_error = f"MT5 initialize failed ({err[0]}): {err[1]}. Ensure MetaTrader 5 is running."
                return {"connected": False, "error": self.last_error}

            try:
                ok = mt5.login(login=int(account), password=str(password), server=str(server))
            except Exception as e:
                mt5.shutdown()
                self.connected = False
                self.last_error = str(e)
                return {"connected": False, "error": self.last_error}

            if not ok:
                err = mt5.last_error()
                mt5.shutdown()
                self.connected = False
                self.last_error = f"Login failed ({err[0]}): {err[1]}"
                return {"connected": False, "error": self.last_error}

            self.connected = True
            self.last_error = None
            self.credentials = {"account": account, "password": password, "server": server}
            info = mt5.account_info()
            self.account_info_cache = info
            return {"connected": True, "info": self._format_account_info(info)}

    def disconnect(self):
        with self._lock:
            if MT5_AVAILABLE:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
            self.connected = False
            self.account_info_cache = None

    def reconnect(self):
        if self.credentials:
            return self.connect(**self.credentials)
        return {"connected": False, "error": "No saved credentials to reconnect with."}

    def ensure_connected(self):
        """Verify connection is still alive; reconnect if needed."""
        if not self.connected or not MT5_AVAILABLE:
            return False
        try:
            info = mt5.account_info()
            if info is None:
                self.connected = False
                self.reconnect()
            return self.connected
        except Exception:
            self.connected = False
            return False

    # ─── Account Data ────────────────────────────────────────────────

    def get_account_info(self):
        """Return live account info dict."""
        if not self.ensure_connected():
            return None
        with self._lock:
            info = mt5.account_info()
            if info:
                self.account_info_cache = info
            return info

    def _format_account_info(self, info) -> dict:
        if info is None:
            return {}
        return {
            "broker": info.company,
            "account": str(info.login),
            "server": info.server,
            "currency": info.currency,
            "balance": round(info.balance, 2),
            "equity": round(info.equity, 2),
            "margin": round(info.margin, 2),
            "free_margin": round(info.margin_free, 2),
            "profit": round(info.profit, 2),
            "leverage": info.leverage,
            "account_type": "Demo" if "demo" in str(info.server).lower() else "Live",
        }

    # ─── Open Positions ──────────────────────────────────────────────

    def get_open_positions(self) -> list:
        """Return currently open trades from MT5."""
        if not self.ensure_connected():
            return []
        with self._lock:
            positions = mt5.positions_get()
            if positions is None:
                return []
            result = []
            for p in positions:
                result.append({
                    "trade_id": str(p.ticket),
                    "timestamp": datetime.fromtimestamp(p.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": p.symbol,
                    "strategy": "LIVE",
                    "direction": "LONG" if p.type == 0 else "SHORT",
                    "entry": round(p.price_open, 5),
                    "stop_loss": round(p.sl, 5) if p.sl else 0,
                    "take_profit": round(p.tp, 5) if p.tp else 0,
                    "lots": p.volume,
                    "pnl": round(p.profit, 2),
                    "status": "OPEN",
                    "rr_ratio": self._calc_rr(p),
                    "current_price": round(p.price_current, 5),
                    "swap": round(p.swap, 2),
                    "comment": p.comment,
                })
            return result

    def _calc_rr(self, p) -> float:
        try:
            if p.sl and p.tp:
                risk = abs(p.price_open - p.sl)
                reward = abs(p.tp - p.price_open)
                return round(reward / risk, 2) if risk > 0 else 0
        except Exception:
            pass
        return 0

    # ─── Trade History ───────────────────────────────────────────────

    def get_trade_history(self, days: int = 30) -> list:
        """Return closed deals from MT5 history."""
        if not self.ensure_connected():
            return []
        with self._lock:
            date_from = datetime.now() - timedelta(days=days)
            date_to = datetime.now() + timedelta(hours=1)
            deals = mt5.history_deals_get(date_from, date_to)
            if deals is None:
                return []

            trades = []
            for d in deals:
                # Skip in/balance/deposit entries — only show DEAL_ENTRY_OUT (closed trades)
                if d.entry != 1:   # 1 = DEAL_ENTRY_OUT = closing deal
                    continue
                trades.append({
                    "trade_id": str(d.ticket),
                    "timestamp": datetime.fromtimestamp(d.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": d.symbol,
                    "strategy": d.comment or "MT5",
                    "direction": "LONG" if d.type == 0 else "SHORT",
                    "entry": round(d.price, 5),
                    "lots": d.volume,
                    "pnl": round(d.profit + d.swap + d.commission, 2),
                    "status": "CLOSED",
                    "rr_ratio": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                })
            return sorted(trades, key=lambda x: x["timestamp"], reverse=True)

    # ─── Performance ─────────────────────────────────────────────────

    def get_performance_summary(self, days: int = 30) -> dict:
        """Calculate performance stats from real deal history."""
        if not self.ensure_connected():
            return None

        with self._lock:
            info = mt5.account_info()
            if not info:
                return None

            date_from = datetime.now() - timedelta(days=days)
            date_to = datetime.now() + timedelta(hours=1)
            deals = mt5.history_deals_get(date_from, date_to)

            closed_deals = [d for d in (deals or []) if d.entry == 1 and d.symbol]
            total = len(closed_deals)
            wins = sum(1 for d in closed_deals if d.profit > 0)
            losses = total - wins
            total_pnl = sum(d.profit + d.swap + d.commission for d in closed_deals)
            gross_profit = sum(d.profit for d in closed_deals if d.profit > 0)
            gross_loss = abs(sum(d.profit for d in closed_deals if d.profit < 0))
            profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0
            win_rate = round((wins / total * 100), 1) if total > 0 else 0

            # Build daily P&L map
            daily_map = {}
            for d in closed_deals:
                day = datetime.fromtimestamp(d.time).strftime("%Y-%m-%d")
                daily_map[day] = daily_map.get(day, 0) + d.profit + d.swap + d.commission

            # Fill with zeros for days with no trades
            daily = []
            running_balance = info.balance - total_pnl
            for i in range(days, -1, -1):
                day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                pnl = round(daily_map.get(day, 0), 2)
                running_balance += pnl
                daily.append({"date": day, "pnl": pnl, "balance": round(running_balance, 2)})

            # Max drawdown (simplified)
            peak = running_balance
            max_dd = 0
            bal = info.balance - total_pnl
            for d_entry in daily:
                bal += d_entry["pnl"]
                peak = max(peak, bal)
                dd = bal - peak
                max_dd = min(max_dd, dd)

            return {
                "total_trades": total,
                "winning_trades": wins,
                "losing_trades": losses,
                "total_pnl": round(total_pnl, 2),
                "win_rate": win_rate,
                "avg_rr": 0,
                "max_drawdown": round(max_dd, 2),
                "profit_factor": profit_factor,
                "daily": daily,
                # Live account data
                "balance": round(info.balance, 2),
                "equity": round(info.equity, 2),
                "profit": round(info.profit, 2),
                "currency": info.currency,
            }


# Singleton — imported by app.py
mt5_manager = MT5Manager()
