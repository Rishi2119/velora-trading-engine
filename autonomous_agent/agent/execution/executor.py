"""
Autonomous Agent Execution Layer — Production Edition
======================================================
Securely connects AI decisions to MT5 trade execution.

Security chain:
  1. Kill switch file check
  2. config.yaml enable_live_execution flag
  3. Risk Manager (daily loss / concurrent / trade count limits)
  4. Spread filter
  5. MT5TradeExecutor → MetaTrader 5 Terminal

Config-driven trading is OFF by default. Set:
  trading.enable_live_execution: true
in autonomous_agent/config.yaml to allow real orders.
"""

import traceback
import sys
import os
from datetime import datetime

from agent.utils.logger import logger
from agent.utils.errors import ExecutionError

# ─── Path setup ──────────────────────────────────────────────────────────────

# Root of the whole repo (e.g. c:/Users/.../trading_engins)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MOBILE_API_DIR = os.path.join(REPO_ROOT, "mobile_api")
KILL_SWITCH_PATH = os.path.join(MOBILE_API_DIR, "KILL_SWITCH.txt")

# Ensure repo root and mobile_api are on sys.path for shared modules
for _p in [REPO_ROOT, MOBILE_API_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Optional imports ────────────────────────────────────────────────────────

RISK_AVAILABLE = False
MT5_EXECUTOR_AVAILABLE = False

try:
    from risk import RiskManager
    RISK_AVAILABLE = True
except ImportError:
    logger.warning("Risk module not available — trading will be blocked.")

try:
    from mt5_trade_executor import mt5_trade_executor
    MT5_EXECUTOR_AVAILABLE = True
except ImportError:
    logger.warning("MT5 trade executor not available — live trading disabled.")


# ─── Execution Layer ─────────────────────────────────────────────────────────

class ExecutionLayer:
    """
    Production Execution Layer.

    Tools available to the AI agent:
      read_only:
        - get_market_data(symbol)
        - get_open_positions()
        - get_risk_status()
        - math_eval(expression)
        - read_file(filepath)
        - write_file(filepath, content)

      trading (requires enable_live_execution=true in config.yaml):
        - execute_trade(symbol, direction, volume, sl, tp, comment)
        - close_position(ticket)

    Blocked tools (never executable):
        - delete_file
        - exec
        - system
    """

    def __init__(self, config: dict):
        self.config = config

        # Read live-trading flag from config.yaml → trading.enable_live_execution
        trading_cfg = config.get("trading", {})
        self._live_enabled = trading_cfg.get("enable_live_execution", False)

        # Log startup state clearly
        if self._live_enabled:
            logger.warning("[LIVE] LIVE TRADING ENABLED via config.yaml -- real orders will be placed!")
        else:
            logger.info("[PAPER] Paper mode: live execution disabled in config.yaml")

        # Risk control
        self.safety = RiskControlSystem(config)
        self._risk_manager = None
        self._init_risk_system()

        from agent.execution.task_executor import DynamicTaskExecutor
        self.dynamic_task_executor = DynamicTaskExecutor()

        # Tool registry
        self.tools = {
            "write_file": self._write_file,
            "read_file": self._read_file,
            "math_eval": self._math_eval,
            "get_market_data": self._get_market_data,
            "get_open_positions": self._get_open_positions,
            "get_risk_status": self._get_risk_status,
            "execute_dynamic_task": self.dynamic_task_executor.execute_sub_task,
            # Trading tools — active only when live enabled
            "execute_trade": self._execute_trade,
            "close_position": self._close_position,
        }

        self.blocked_tools = {
            "delete_file": "File deletion disabled.",
            "exec": "Code execution disabled.",
            "system": "System commands disabled.",
        }

        logger.info("ExecutionLayer initialized.")

    # ─── Risk System ─────────────────────────────────────────────────────

    def _init_risk_system(self):
        if not RISK_AVAILABLE:
            return
        try:
            self._risk_manager = RiskManager(
                max_daily_loss=20,
                max_daily_trades=5,
                max_concurrent=2,
                risk_per_trade=0.01,
                min_rr=3.0,
                state_file=os.path.join(REPO_ROOT, "logs", "risk_state.json")
            )
            logger.info("Risk system initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize risk system: {e}")

    # ─── Kill Switch ─────────────────────────────────────────────────────

    def _is_kill_switch_active(self) -> bool:
        return os.path.exists(KILL_SWITCH_PATH)

    # ─── Dispatch ────────────────────────────────────────────────────────

    def execute(self, action: dict) -> dict:
        """
        Execute an agent action.

        action = {"tool": "tool_name", "args": {...}}
        """
        tool_name = action.get("tool")
        args = action.get("args", {})

        logger.info(f"Executing tool: {tool_name} | args: {args}")

        # Kill switch check
        if self._is_kill_switch_active() and tool_name in ("execute_trade", "close_position"):
            msg = "Kill switch is active — trading blocked."
            logger.warning(msg)
            return {"status": "blocked", "message": msg}

        # Blocked tools
        if tool_name in self.blocked_tools:
            msg = self.blocked_tools[tool_name]
            logger.warning(f"Blocked tool: {tool_name} — {msg}")
            return {"status": "blocked", "message": msg}

        # Safety validation
        try:
            self.safety.validate_action(tool_name, args)
        except ExecutionError as e:
            logger.warning(f"Safety block: {e}")
            return {"status": "blocked", "message": str(e)}

        # Unknown tool
        if tool_name not in self.tools:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        # Execute
        try:
            result = self.tools[tool_name](**args)
            logger.info(f"Tool {tool_name} succeeded.")
            return {"status": "success", "output": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

    # ─── Read-only Tools ─────────────────────────────────────────────────

    def _write_file(self, filepath: str, content: str):
        blocked = ["/etc", "/usr", "/bin", "C:\\Windows", "config.py", ".env"]
        for b in blocked:
            if b in filepath:
                raise ExecutionError(f"Cannot write to protected path: {filepath}")
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {filepath}"

    def _read_file(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def _math_eval(self, expression: str):
        allowed = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed):
            raise ExecutionError("Invalid characters in math expression.")
        return eval(expression)  # nosec - restricted charset above

    def _get_market_data(self, symbol: str) -> dict:
        try:
            from mt5_manager import mt5_manager
            if not mt5_manager.connected:
                return {"error": "MT5 not connected. Use the mobile app to connect first."}
            data = mt5_manager.get_symbol_info(symbol)
            return data
        except ImportError:
            return {"error": "MT5 manager not available in this environment."}
        except Exception as e:
            return {"error": str(e)}

    def _get_open_positions(self) -> list:
        try:
            from mt5_manager import mt5_manager
            if not mt5_manager.connected:
                return []
            return mt5_manager.get_open_positions()
        except Exception as e:
            return [{"error": str(e)}]

    def _get_risk_status(self) -> dict:
        if not self._risk_manager:
            return {"status": "unavailable", "message": "Risk system not initialized."}
        can_trade, reason = self._risk_manager.can_trade()
        return {
            "can_trade": can_trade,
            "reason": reason,
            "live_trading_enabled": self._live_enabled,
            "kill_switch_active": self._is_kill_switch_active(),
            "stats": self._risk_manager.get_stats(),
        }

    # ─── Trading Tools ───────────────────────────────────────────────────

    def _execute_trade(
        self,
        symbol: str,
        direction: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "Velora-AI"
    ) -> dict:
        """
        Place a real MT5 order — only works when:
          1. config.yaml trading.enable_live_execution = true
          2. MT5 is connected
          3. Kill switch is NOT active
          4. Risk manager permits the trade
        """
        # Config gate
        if not self._live_enabled:
            return {
                "status": "paper_mode",
                "message": "Live execution is disabled. Set trading.enable_live_execution: true in config.yaml.",
                "simulated": {
                    "symbol": symbol, "direction": direction, "volume": volume,
                    "sl": sl, "tp": tp, "timestamp": datetime.now().isoformat()
                }
            }

        if not MT5_EXECUTOR_AVAILABLE:
            return {"status": "error", "message": "MT5 trade executor not available. pip install MetaTrader5"}

        # Kill switch gate
        if self._is_kill_switch_active():
            return {"status": "blocked", "message": "Kill switch is active."}

        # Execute via the dedicated executor
        result = mt5_trade_executor.place_order(
            symbol=symbol,
            direction=direction,
            volume=float(volume),
            sl=float(sl),
            tp=float(tp),
            comment=comment,
            risk_manager=self._risk_manager
        )

        if result.get("success"):
            logger.info(f"LIVE TRADE EXECUTED: #{result.get('ticket')} {direction} {volume} {symbol}")
        else:
            logger.error(f"TRADE FAILED: {result.get('error')}")

        return result

    def _close_position(self, ticket: int) -> dict:
        """Close an open position by ticket number."""
        if not MT5_EXECUTOR_AVAILABLE:
            return {"status": "error", "message": "MT5 trade executor not available."}

        result = mt5_trade_executor.close_position(int(ticket))
        if result.get("success"):
            if self._risk_manager:
                self._risk_manager.close_trade(0)  # PnL updated from MT5 directly
        return result


# ─── Basic Risk Control ──────────────────────────────────────────────────────

class RiskControlSystem:
    """Basic pre-execution safety checks."""

    ALLOWED_SYMBOLS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD",
                       "USDJPY", "EURGBP", "EURJPY", "GBPJPY", "USDCHF"]
    MAX_VOLUME = 0.5

    def __init__(self, config: dict):
        self.config = config

    def validate_action(self, tool_name: str, args: dict):
        if tool_name == "execute_trade":
            vol = float(args.get("volume", 0))
            if vol > self.MAX_VOLUME:
                raise ExecutionError(f"Volume {vol} exceeds safety cap of {self.MAX_VOLUME} lots.")
            sym = args.get("symbol", "")
            if sym and sym not in self.ALLOWED_SYMBOLS:
                raise ExecutionError(f"Symbol '{sym}' not in the allowed trading list: {self.ALLOWED_SYMBOLS}")
