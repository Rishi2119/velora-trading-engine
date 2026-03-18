# // turbo
"""
Velora AI Engine — MT5 Broker Connection
Fixed: handles all connection edge cases, retries, and disconnects.
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import time
from loguru import logger
from config.settings import config
from typing import Optional, List


class MT5Connector:
    def __init__(self):
        self.connected = False
        self.account_info = None
        self._retry_count = 0
        self._max_retries = 3

    def connect(self) -> bool:
        for attempt in range(self._max_retries):
            try:
                kwargs = {
                    "login": config.MT5_LOGIN,
                    "password": config.MT5_PASSWORD,
                    "server": config.MT5_SERVER,
                }
                if config.MT5_PATH:
                    kwargs["path"] = config.MT5_PATH

                if not mt5.initialize(**kwargs):
                    err = mt5.last_error()
                    logger.warning(f"[MT5] Init attempt {attempt+1} failed: {err}")
                    time.sleep(2 ** attempt)
                    continue

                info = mt5.account_info()
                if info is None:
                    logger.warning(f"[MT5] Connected but no account info (attempt {attempt+1})")
                    time.sleep(2)
                    continue

                self.connected = True
                self.account_info = info
                logger.success(f"[MT5] Connected — Account: {info.login} | Balance: {info.balance:.2f} {info.currency}")
                return True

            except Exception as e:
                logger.error(f"[MT5] Connection exception (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)

        logger.error("[MT5] All connection attempts failed")
        self.connected = False
        return False

    def ensure_connected(self) -> bool:
        if not self.connected or not mt5.terminal_info():
            logger.warning("[MT5] Lost connection — reconnecting...")
            return self.connect()
        return True

    def disconnect(self):
        mt5.shutdown()
        self.connected = False
        logger.info("[MT5] Disconnected")

    def get_account(self) -> dict:
        if not self.ensure_connected():
            return {}
        info = mt5.account_info()
        if info is None:
            return {}
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "profit": info.profit,
            "currency": info.currency,
            "leverage": info.leverage,
            "login": info.login
        }

    def get_ohlcv(self, symbol: str, timeframe_minutes: int, bars: int = 200) -> Optional[pd.DataFrame]:
        if not self.ensure_connected():
            return None
        tf_map = {
            1: mt5.TIMEFRAME_M1, 5: mt5.TIMEFRAME_M5, 15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30, 60: mt5.TIMEFRAME_H1, 240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1, 10080: mt5.TIMEFRAME_W1
        }
        tf = tf_map.get(timeframe_minutes, mt5.TIMEFRAME_H4)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            logger.warning(f"[MT5] No data for {symbol} TF={timeframe_minutes}")
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                            "close": "Close", "tick_volume": "Volume"}, inplace=True)
        df.set_index("time", inplace=True)
        return df

    def get_symbol_info(self, symbol: str) -> dict:
        if not self.ensure_connected():
            return {}
        info = mt5.symbol_info(symbol)
        if info is None:
            mt5.symbol_select(symbol, True)
            time.sleep(0.5)
            info = mt5.symbol_info(symbol)
        if info is None:
            return {}
        return {
            "symbol": symbol,
            "bid": info.bid,
            "ask": info.ask,
            "spread": info.spread,
            "point": info.point,
            "digits": info.digits,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
            "contract_size": info.trade_contract_size
        }

    def place_order(self, symbol: str, order_type: str, lots: float,
                    sl: float, tp: float, comment: str = "Velora AI") -> dict:
        if not self.ensure_connected():
            return {"success": False, "error": "Not connected"}

        info = mt5.symbol_info(symbol)
        if info is None:
            return {"success": False, "error": f"Symbol {symbol} not found"}

        price = info.ask if order_type == "BUY" else info.bid
        mt5_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL

        lots = round(max(lots, info.volume_min), 2)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lots,
            "type": mt5_type,
            "price": price,
            "sl": round(sl, info.digits),
            "tp": round(tp, info.digits),
            "deviation": 20,
            "magic": 20260318,
            "comment": comment[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            err = mt5.last_error()
            logger.error(f"[MT5] order_send returned None: {err}")
            return {"success": False, "error": str(err)}

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"[MT5] Order failed: {result.retcode} — {result.comment}")
            return {"success": False, "error": result.comment, "retcode": result.retcode}

        logger.success(f"[MT5] Order placed: {order_type} {lots} {symbol} @ {price} SL={sl} TP={tp}")
        return {
            "success": True,
            "ticket": result.order,
            "price": result.price,
            "volume": result.volume,
            "symbol": symbol,
            "type": order_type
        }

    def close_trade(self, ticket: int) -> dict:
        if not self.ensure_connected():
            return {"success": False, "error": "Not connected"}
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return {"success": False, "error": "Position not found"}
        pos = positions[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        info = mt5.symbol_info(pos.symbol)
        price = info.bid if close_type == mt5.ORDER_TYPE_SELL else info.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 20260318,
            "comment": "Velora Close",
        }
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.success(f"[MT5] Closed ticket {ticket}")
            return {"success": True, "ticket": ticket, "price": price}
        return {"success": False, "error": result.comment if result else "Unknown error"}

    def get_open_positions(self) -> List[dict]:
        if not self.ensure_connected():
            return []
        positions = mt5.positions_get(magic=20260318)
        if positions is None:
            return []
        return [
            {
                "ticket": p.ticket, "symbol": p.symbol, "type": "BUY" if p.type == 0 else "SELL",
                "volume": p.volume, "open_price": p.price_open, "sl": p.sl, "tp": p.tp,
                "profit": p.profit, "comment": p.comment, "time": p.time
            }
            for p in positions
        ]

    def modify_sl_tp(self, ticket: int, new_sl: float, new_tp: float) -> bool:
        if not self.ensure_connected():
            return False
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return False
        pos = positions[0]
        info = mt5.symbol_info(pos.symbol)
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": round(new_sl, info.digits),
            "tp": round(new_tp, info.digits),
        }
        result = mt5.order_send(request)
        return result is not None and result.retcode == mt5.TRADE_RETCODE_DONE

connector = MT5Connector()
