"""
MT5 Trade Executor — Production Safe Trade Execution Module
===========================================================
Used by the autonomous agent to execute real trades via MetaTrader 5.

Pipeline:
  AI Decision → Risk Manager → MT5 Trade Executor → MT5 Terminal → Confirmation

Safety guarantees:
  - Kill switch file check before every order
  - Risk manager validation before every order
  - Spread filter (max 2 pips default)
  - Slippage protection (max 3 pip deviation)
  - Audit trail logging for every action
"""

import os
import sys
import json
import logging
import threading
from datetime import datetime

# ─── MT5 Import ─────────────────────────────────────────────────────────────

MT5_AVAILABLE = False
mt5 = None

try:
    import MetaTrader5 as _mt5
    mt5 = _mt5
    MT5_AVAILABLE = True
except ImportError:
    pass

# ─── Logger ─────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mt5_trade_executor")

# ─── Path Setup ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KILL_SWITCH_PATH = os.path.join(BASE_DIR, "mobile_api", "KILL_SWITCH.txt")
AUDIT_LOG_PATH = os.path.join(BASE_DIR, "logs", "trade_audit.log")

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)


# ─── Audit Logger ───────────────────────────────────────────────────────────

def _audit(event: str, details: dict):
    """Append an audit record to the trade audit log."""
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **details
        }
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Audit log error: {e}")


# ─── Main Class ─────────────────────────────────────────────────────────────

class MT5TradeExecutor:
    """
    Thread-safe MT5 trade executor with full risk validation chain.

    Execution order:
      1. Kill switch check
      2. MT5 connection check
      3. Symbol existence check
      4. Spread check
      5. Risk manager validation (optional)
      6. Order construction & submission
      7. Result confirmation
      8. Audit log
    """

    # Magic number for all orders placed by this executor
    MAGIC = 234001

    def __init__(self, max_spread_pips: float = 2.0, max_slippage_pips: float = 3.0):
        self._lock = threading.Lock()
        self.max_spread_pips = max_spread_pips
        self.max_slippage_pips = max_slippage_pips
        logger.info(f"MT5TradeExecutor ready. Spread limit: {max_spread_pips}p, "
                    f"Slippage limit: {max_slippage_pips}p")

    # ─── Kill Switch ──────────────────────────────────────────────────────

    def _is_kill_switch_active(self) -> bool:
        return os.path.exists(KILL_SWITCH_PATH)

    # ─── Connection Check ─────────────────────────────────────────────────

    def _ensure_mt5(self) -> tuple[bool, str]:
        """Verify MT5 is installed and connected."""
        if not MT5_AVAILABLE:
            return False, "MetaTrader5 package not installed. Run: pip install MetaTrader5"

        # Check raw MT5 terminal connection
        try:
            if not mt5.initialize():
                return False, "MT5 terminal could not be initialized."
                
            info = mt5.account_info()
            if info is None:
                return False, "MT5 account info unavailable — terminal may be disconnected."
        except Exception as e:
            return False, f"MT5 connection error: {e}"

        return True, "OK"

    # ─── Symbol Helpers ───────────────────────────────────────────────────

    def _get_pip_multiplier(self, symbol: str) -> float:
        """Return the pip multiplier for a given symbol."""
        return 100.0 if "JPY" in symbol.upper() else 10000.0

    def _get_spread_pips(self, symbol: str) -> float:
        """Return current spread in pips."""
        try:
            tick = mt5.symbol_info_tick(symbol)
            sym_info = mt5.symbol_info(symbol)
            if tick is None or sym_info is None:
                return 999.0
            spread_points = tick.ask - tick.bid
            return round(spread_points * self._get_pip_multiplier(symbol), 1)
        except Exception:
            return 999.0

    def _get_current_price(self, symbol: str, direction: str) -> float:
        """Return ASK for BUY orders or BID for SELL orders."""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return 0.0
            return tick.ask if direction.upper() in ("BUY", "LONG") else tick.bid
        except Exception:
            return 0.0

    def _normalize_lots(self, symbol: str, volume: float) -> float:
        """Clamp volume to the broker's allowed min/max/step."""
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return volume
            step = info.volume_step or 0.01
            min_v = info.volume_min or 0.01
            max_v = info.volume_max or 100.0
            # Round to step
            volume = round(round(volume / step) * step, 2)
            return max(min_v, min(max_v, volume))
        except Exception:
            return max(0.01, round(volume, 2))

    # ─── Order Placement ─────────────────────────────────────────────────

    def place_order(
        self,
        symbol: str,
        direction: str,          # "BUY" or "SELL"
        volume: float,           # Lots
        sl: float = 0.0,         # Stop loss price (0 = none)
        tp: float = 0.0,         # Take profit price (0 = none)
        comment: str = "Velora-AI",
        risk_manager=None        # Optional RiskManager instance
    ) -> dict:
        """
        Place a market order with full safety checks.

        Returns:
            {
                "success": bool,
                "ticket": int | None,
                "price": float,
                "symbol": str,
                "direction": str,
                "volume": float,
                "sl": float,
                "tp": float,
                "error": str | None
            }
        """
        with self._lock:
            # 1. Kill switch
            if self._is_kill_switch_active():
                msg = "KILL SWITCH active — no orders allowed."
                logger.warning(f"[BLOCKED] {msg}")
                _audit("ORDER_BLOCKED", {"reason": "kill_switch", "symbol": symbol})
                return {"success": False, "ticket": None, "error": msg}

            # 2. MT5 connection
            ok, err = self._ensure_mt5()
            if not ok:
                _audit("ORDER_BLOCKED", {"reason": "mt5_disconnected", "error": err})
                return {"success": False, "ticket": None, "error": err}

            direction = direction.upper()
            if direction == "LONG":
                direction = "BUY"
            elif direction == "SHORT":
                direction = "SELL"

            if direction not in ("BUY", "SELL"):
                return {"success": False, "ticket": None, "error": f"Invalid direction: {direction}"}

            # 3. Symbol check
            sym_info = mt5.symbol_info(symbol)
            if sym_info is None:
                err = f"Symbol {symbol} not found in MT5. Ensure it is in Market Watch."
                _audit("ORDER_BLOCKED", {"reason": "symbol_not_found", "symbol": symbol})
                return {"success": False, "ticket": None, "error": err}

            if not sym_info.visible:
                mt5.symbol_select(symbol, True)

            # 4. Spread check
            spread_pips = self._get_spread_pips(symbol)
            if spread_pips > self.max_spread_pips:
                err = f"Spread too wide: {spread_pips:.1f} pips (max {self.max_spread_pips})"
                logger.warning(f"[BLOCKED] {err}")
                _audit("ORDER_BLOCKED", {"reason": "spread_too_wide", "spread": spread_pips, "symbol": symbol})
                return {"success": False, "ticket": None, "error": err}

            # 5. Risk manager check
            if risk_manager is not None:
                can_trade, reason = risk_manager.can_trade()
                if not can_trade:
                    _audit("ORDER_BLOCKED", {"reason": "risk_manager", "detail": reason, "symbol": symbol})
                    return {"success": False, "ticket": None, "error": f"Risk block: {reason}"}

            # 6. Normalize volume
            volume = self._normalize_lots(symbol, volume)

            # 7. Get current price
            price = self._get_current_price(symbol, direction)
            if price == 0.0:
                return {"success": False, "ticket": None, "error": "Could not get current price from MT5."}

            # 8. Build order request
            order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
            deviation = int(self.max_slippage_pips * 10)  # points

            # Determine the broker-supported filling mode dynamically
            filling_mode_mask = sym_info.filling_mode
            if filling_mode_mask & 1:
                filling = mt5.ORDER_FILLING_FOK
            elif filling_mode_mask & 2:
                filling = mt5.ORDER_FILLING_IOC
            else:
                filling = mt5.ORDER_FILLING_RETURN

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": deviation,
                "magic": self.MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling,
            }
            if sl > 0:
                request["sl"] = sl
            if tp > 0:
                request["tp"] = tp

            # 9. Submit order
            logger.info(f"Placing {direction} {volume} {symbol} @ {price} SL={sl} TP={tp}")
            result = mt5.order_send(request)

            # 10. Process result
            if result is None:
                err_code = mt5.last_error()
                err = f"order_send returned None. MT5 error: {err_code}"
                _audit("ORDER_FAILED", {"symbol": symbol, "direction": direction, "error": err})
                return {"success": False, "ticket": None, "error": err}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                err = f"Order rejected: retcode={result.retcode}, comment={result.comment}"
                logger.error(f"[FAILED] {err}")
                _audit("ORDER_FAILED", {
                    "symbol": symbol, "direction": direction,
                    "retcode": result.retcode, "comment": result.comment
                })
                return {"success": False, "ticket": None, "error": err}

            # 11. Register with risk manager
            if risk_manager is not None:
                risk_manager.add_trade()

            # 12. Audit
            ticket = result.order
            _audit("ORDER_PLACED", {
                "ticket": ticket, "symbol": symbol, "direction": direction,
                "volume": volume, "price": result.price,
                "sl": sl, "tp": tp, "spread_pips": spread_pips
            })
            logger.info(f"[SUCCESS] Order #{ticket} placed: {direction} {volume} {symbol} @ {result.price}")

            return {
                "success": True,
                "ticket": ticket,
                "price": result.price,
                "symbol": symbol,
                "direction": direction,
                "volume": volume,
                "sl": sl,
                "tp": tp,
                "error": None
            }

    # ─── Close Position ──────────────────────────────────────────────────

    def close_position(self, ticket: int, volume: float = None, comment: str = "Velora-AI-Close") -> dict:
        """Close an open position by ticket number."""
        with self._lock:
            if self._is_kill_switch_active():
                pass  # Closing is always allowed even if kill switch active

            ok, err = self._ensure_mt5()
            if not ok:
                return {"success": False, "error": err}

            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": f"Position #{ticket} not found."}

            pos = position[0]
            vol = volume or pos.volume
            # Close is opposite of open direction
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            symbol = pos.symbol
            price = self._get_current_price(symbol, "SELL" if pos.type == 0 else "BUY")

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": vol,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": self.MAGIC,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                err = f"Close failed: {result.retcode if result else 'None'}"
                _audit("CLOSE_FAILED", {"ticket": ticket, "error": err})
                return {"success": False, "error": err}

            _audit("POSITION_CLOSED", {"ticket": ticket, "price": result.price, "volume": vol})
            logger.info(f"[SUCCESS] Position #{ticket} closed @ {result.price}")
            return {"success": True, "ticket": ticket, "price": result.price}

    # ─── Modify Position SL/TP ───────────────────────────────────────────

    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> dict:
        """Modify stop loss and/or take profit of an open position."""
        with self._lock:
            ok, err = self._ensure_mt5()
            if not ok:
                return {"success": False, "error": err}

            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": f"Position #{ticket} not found."}

            pos = position[0]
            new_sl = sl if sl is not None else pos.sl
            new_tp = tp if tp is not None else pos.tp

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": pos.symbol,
                "sl": new_sl,
                "tp": new_tp,
            }

            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                err = f"Modify failed: {result.retcode if result else 'None'}"
                _audit("MODIFY_FAILED", {"ticket": ticket, "error": err})
                return {"success": False, "error": err}

            _audit("POSITION_MODIFIED", {"ticket": ticket, "sl": new_sl, "tp": new_tp})
            logger.info(f"[SUCCESS] Position #{ticket} modified: SL={new_sl} TP={new_tp}")
            return {"success": True, "ticket": ticket, "sl": new_sl, "tp": new_tp}

    # ─── Close All Positions ─────────────────────────────────────────────

    def close_all_positions(self, comment: str = "Velora-KillSwitch") -> list:
        """Emergency: close all open positions (used by kill switch handler)."""
        ok, err = self._ensure_mt5()
        if not ok:
            return [{"success": False, "error": err}]

        positions = mt5.positions_get()
        if not positions:
            return []

        results = []
        for pos in positions:
            r = self.close_position(pos.ticket, comment=comment)
            results.append(r)
        return results


# Singleton
mt5_trade_executor = MT5TradeExecutor()
