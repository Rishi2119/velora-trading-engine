import traceback
from agent.utils.logger import logger
from agent.utils.errors import ExecutionError
from agent.execution.safety import RiskControlSystem
import sys
import os

# Import the MT5 manager from the mobile_api directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "mobile_api"))
try:
    from mt5_manager import mt5_manager
except ImportError:
    mt5_manager = None
    logger.warning("Could not import mt5_manager. Trading tools will be disabled.")

class ExecutionLayer:
    def __init__(self, config):
        self.safety = RiskControlSystem(config)
        self.tools = {
            "write_file": self._write_file,
            "read_file": self._read_file,
            "math_eval": self._math_eval,
            "get_market_data": self._get_market_data,
            "execute_trade": self._execute_trade,
            "get_open_positions": self._get_open_positions
        }
        
    def execute(self, action):
        """
        Executes an action dict: {"tool": "tool_name", "args": {...}}
        """
        tool_name = action.get("tool")
        args = action.get("args", {})
        
        logger.info(f"Executing tool: {tool_name} with args: {args}")
        self.safety.validate_action(tool_name, args)
        
        if tool_name not in self.tools:
            raise ExecutionError(f"Unknown tool requested: {tool_name}")
            
        try:
            result = self.tools[tool_name](**args)
            logger.info(f"Execution successful. Result: {result}")
            return {"status": "success", "output": result}
        except Exception as e:
            logger.error(f"Execution failed: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

    def _write_file(self, filepath, content):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File {filepath} written successfully."

    def _read_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
            
    def _math_eval(self, expression):
        # Restricted eval for math
        allowed_chars = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed_chars):
            raise ExecutionError("Invalid characters in math expression.")
        return eval(expression)
        
    def _get_market_data(self, symbol):
        if not mt5_manager or not mt5_manager.connected:
            return {"error": "MT5 is not connected."}
        try:
            return mt5_manager.get_symbol_info(symbol)
        except Exception as e:
            return {"error": str(e)}
            
    def _execute_trade(self, symbol, action, volume):
        if not mt5_manager or not mt5_manager.connected:
            return {"error": "MT5 is not connected."}
        try:
            from mt5_manager import mt5
            order_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL
            return mt5_manager.execute_trade(symbol, action.upper(), float(volume), order_type)
        except Exception as e:
            return {"error": str(e)}
            
    def _get_open_positions(self):
        if not mt5_manager or not mt5_manager.connected:
            return {"error": "MT5 is not connected."}
        try:
            return mt5_manager.get_open_positions()
        except Exception as e:
            return {"error": str(e)}
