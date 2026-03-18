"""
Execution engine mapping RiskDecision + SignalResult into live MT5 orders.
Handles retries, partial fills, slippage checks, and paper mode.
"""
import logging
import time
from typing import Dict, Any, Optional
import uuid

from backend.app.core.config import config
from backend.app.strategies.strategy_manager import SignalResult
from backend.app.risk.risk_manager import RiskDecision
from backend.app.execution.mt5_connection import mt5_conn

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


logger = logging.getLogger(__name__)


class TradeExecutor:
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def execute_trade(self, signal: SignalResult, decision: RiskDecision) -> Dict[str, Any]:
        """
        Main entrypoint to execute a validated signal.
        Handles both PAPER and LIVE execution.
        """
        if config.engine_mode == "paper":
            return self._execute_paper(signal, decision)
            
        if not MT5_AVAILABLE or not mt5_conn.is_connected:
            return {"status": "ERROR", "reason": "MT5 not connected, cannot execute live"}
            
        return self._execute_live(signal, decision)

    def _execute_paper(self, signal: SignalResult, decision: RiskDecision) -> Dict[str, Any]:
        """Simulate a trade execution for testing/paper mode."""
        logger.info(f"[PAPER] Executing {signal.direction} {decision.normalized_lots} lots on {signal.symbol}")
        
        # Simulate slippage
        slippage = 0.0001 if signal.direction == "BUY" else -0.0001
        fill_price = signal.entry + slippage
        
        return {
            "status": "FILLED",
            "type": "PAPER",
            "ticket": int(time.time()),
            "symbol": signal.symbol,
            "direction": signal.direction,
            "volume": decision.normalized_lots,
            "fill_price": fill_price,
            "sl": signal.sl,
            "tp": signal.tp,
            "comment": f"Velora-Paper-{signal.strategy_name}"
        }

    def _execute_live(self, signal: SignalResult, decision: RiskDecision) -> Dict[str, Any]:
        """Format the MT5 request and handle the order event loop."""
        symbol = signal.symbol
        volume = decision.normalized_lots
        order_type = mt5.ORDER_TYPE_BUY if signal.direction == "BUY" else mt5.ORDER_TYPE_SELL
        
        # Check symbol info for precise spread / tick data before firing
        sym_info = mt5_conn.get_symbol_info(symbol)
        if not sym_info:
            return {"status": "ERROR", "reason": f"Could not get symbol info for {symbol}"}
            
        if sym_info.get("spread", 0) > config.max_spread_pips * 10:
            return {"status": "REJECTED", "reason": f"Spread too wide ({sym_info.get('spread')} points)"}
            
        # Discover proper filling mode dynamically
        filling_mode = self._get_filling_mode(sym_info)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "sl": float(signal.sl),
            "tp": float(signal.tp),
            "deviation": int(config.slippage_tolerance_pips * 10),
            "magic": int(config.mt5_magic_number),
            "comment": f"Velora-{signal.strategy_name}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Sending LIVE order {signal.direction} {symbol} (Attempt {attempt})")
            
            result = mt5_conn.order_send(request)
            
            if result is None:
                logger.error("MT5 order_send returned None")
                return {"status": "ERROR", "reason": "MT5 communication failure"}
                
            retcode = result.retcode
            
            if retcode == mt5.TRADE_RETCODE_DONE: # 10009
                return {
                    "status": "FILLED",
                    "type": "LIVE",
                    "ticket": result.order,
                    "symbol": symbol,
                    "direction": signal.direction,
                    "volume": result.volume,
                    "fill_price": result.price,
                    "sl": signal.sl,
                    "tp": signal.tp,
                    "comment": request["comment"],
                    "deal_id": result.deal
                }
                
            elif retcode == mt5.TRADE_RETCODE_REQUOTE: # 10004
                logger.warning(f"Requote on {symbol}. Retrying...")
                time.sleep(0.5)
                continue
                
            elif retcode == mt5.TRADE_RETCODE_CONNECTION: # 10031
                logger.warning("No connection to broker. Retrying...")
                time.sleep(1.0)
                continue
                
            else:
                # Fatal rejection
                reasons = {
                    10014: "Not enough money",
                    10015: "Price changed/off quotes",
                    10016: "Invalid stops",
                    10018: "Market closed",
                    10027: "Auto-trading disabled by client terminal",
                    10030: "Unsupported filling mode"
                }
                reason = reasons.get(retcode, f"Unknown MT5 error {retcode}")
                logger.error(f"Order rejected: {reason}")
                return {"status": "REJECTED", "reason": reason, "retcode": retcode}
                
        return {"status": "ERROR", "reason": "Max retries exceeded"}

    def _get_filling_mode(self, symbol_info: Dict[str, Any]) -> int:
        """Dynamically fallback on filling modes supported by the broker."""
        filling_flags = symbol_info.get("filling_mode", 0)
        
        # MetaTrader 5 Constants (Hardcoded for safety if bridge is flaky)
        SYM_FOK = 1 # SYMBOL_FILLING_FOK
        SYM_IOC = 2 # SYMBOL_FILLING_IOC
        
        ORD_FOK = 0 # ORDER_FILLING_FOK
        ORD_IOC = 1 # ORDER_FILLING_IOC
        ORD_RET = 2 # ORDER_FILLING_RETURN

        if filling_flags & SYM_FOK:
            return ORD_FOK
        elif filling_flags & SYM_IOC:
            return ORD_IOC
        else:
            return ORD_RET

# Singleton
trade_executor = TradeExecutor()
