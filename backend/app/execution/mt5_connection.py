"""
MT5 Connection Manager.
Handles thread-safe MT5 API access, automatic reconnection, and connection state.
"""
import logging
import threading
import time
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from backend.app.core.config import config

logger = logging.getLogger(__name__)


class MT5Connection:
    """Manages thread-safe MT5 operations."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._connected = False
        self._watchdog_thread: Optional[threading.Thread] = None
        self._shutdown_flag = threading.Event()
        
    @property
    def is_connected(self) -> bool:
        """Lightweight cached connection status."""
        return self._connected
        
    def connect(self, retries: int = 5, retry_delay: int = 5) -> bool:
        """Establish connection to MT5 terminal."""
        if not MT5_AVAILABLE:
            if config.engine_mode == "paper":
                logger.warning("MT5 package not available. Running in MT5-less paper mode.")
                return True
            else:
                logger.error("MT5 package missing, cannot run in LIVE mode.")
                return False
                
        with self._lock:
            # If already connected, do a quick sanity check instead of re-init
            if self._connected:
                term_info = mt5.terminal_info()
                if term_info is not None and term_info.connected:
                    return True
                else:
                    self._connected = False
            
            logger.info("Connecting to MT5 terminal...")
            
            for attempt in range(1, retries + 1):
                try:
                    # 1. Detect terminal path for explicit initialization
                    path = None
                    for proc in psutil.process_iter(['name', 'exe']):
                        name = proc.info.get('name')
                        if name and (name.lower() == 'terminal.exe' or name.lower() == 'terminal64.exe'):
                            path = proc.info.get('exe')
                            break

                    # 2. Initialize the terminal first without forcing login
                    if path:
                        logger.info(f"Initializing MT5 (Base) with path: {path}")
                        init_res = mt5.initialize(path=path)
                    else:
                        logger.info("Initializing MT5 (Base)...")
                        init_res = mt5.initialize()
                    
                    if not init_res:
                        logger.error(f"mt5.initialize() failed, error code: {mt5.last_error()}")
                        if attempt < retries:
                            time.sleep(retry_delay)
                            continue
                        return False

                    # Give MT5 a moment to stabilize
                    time.sleep(0.2)
                    
                    # 3. Check if already logged in to the correct account
                    acc_info = mt5.account_info()
                    login_id = int(config.mt5_account) if config.mt5_account else 0
                    if acc_info is not None and acc_info.login == login_id:
                        term_info = mt5.terminal_info()
                        if term_info and term_info.connected:
                            logger.info(f"Already connected to Account {acc_info.login}")
                            self._connected = True
                            return True

                    # 4. Perform explicit login if account is wrong or not connected
                    if config.mt5_account and config.mt5_password:
                        logger.info(f"Explicitly logging into Account {config.mt5_account}...")
                        login_res = mt5.login(
                            login=login_id,
                            password=config.mt5_password,
                            server=config.mt5_server
                        )
                        if not login_res:
                            logger.error(f"mt5.login() failed for {config.mt5_account}, error: {mt5.last_error()}")
                            if attempt < retries:
                                time.sleep(retry_delay)
                                continue
                            return False
                        
                    # Verify login by checking account info
                    acc_info = mt5.account_info()
                    if acc_info is None:
                        logger.error(f"Failed to get account info after init, error code: {mt5.last_error()}")
                        if attempt < retries:
                            time.sleep(retry_delay)
                            continue
                        mt5.shutdown()
                        return False
                        
                    logger.info(f"MT5 Connected successfully on attempt {attempt}")
                    logger.info(f"Account: {acc_info.login}, Broker: {acc_info.company}, Balance: {acc_info.balance}")
                    self._connected = True
                    return True
                    
                except Exception as e:
                    logger.error(f"Exception during MT5 connect: {e}")
                    if attempt < retries:
                        time.sleep(retry_delay)
                        
            return False

    def disconnect(self) -> None:
        """Cleanly shutdown MT5 connection."""
        self._shutdown_flag.set()
        with self._lock:
            if MT5_AVAILABLE and self._connected:
                mt5.shutdown()
                self._connected = False
                logger.info("MT5 connection closed cleanly.")

    def start_watchdog(self, interval: int = 15) -> None:
        """Start background thread to monitor and maintain MT5 connection."""
        if self._watchdog_thread is None or not self._watchdog_thread.is_alive():
            self._shutdown_flag.clear()
            self._watchdog_thread = threading.Thread(
                target=self._watchdog_loop,
                args=(interval,),
                daemon=True,
                name="MT5Watchdog"
            )
            self._watchdog_thread.start()
            logger.info("MT5 Watchdog started.")

    def _watchdog_loop(self, interval: int) -> None:
        while not self._shutdown_flag.is_set():
            if MT5_AVAILABLE and config.engine_mode != "paper":
                with self._lock:
                    term_info = mt5.terminal_info()
                    is_terminal_connected = term_info is not None and term_info.connected
                    
                    if not is_terminal_connected:
                        err = mt5.last_error()
                        logger.error(f"MT5 Watchdog: Connection lost! (terminal_info.connected=False). Last error: {err}")
                        self._connected = False
                        success = self.connect(retries=3, retry_delay=2)
                        if not success:
                            logger.critical("MT5 Watchdog: Reconnection failed. Requires manual intervention.")
                            # TODO: Call notifications.py to send Telegram alert
                        else:
                            logger.info("MT5 Watchdog: Reconnection successful.")
            
            # Sleep in intervals to allow quick shutdown
            for _ in range(interval * 2):
                if self._shutdown_flag.is_set():
                    break
                time.sleep(0.5)

    # ── Thread-safe MT5 Wrappers ──────────────────────────────────────────────

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        if not MT5_AVAILABLE or not self._connected:
            return None
        with self._lock:
            info = mt5.account_info()
            if info:
                return info._asdict()
            return None

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not MT5_AVAILABLE or not self._connected:
            return None
        with self._lock:
            info = mt5.symbol_info(symbol)
            if info:
                return info._asdict()
            return None
            
    def get_symbol_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not MT5_AVAILABLE or not self._connected:
            return None
        with self._lock:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick._asdict()
            return None
            
    def get_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        if not MT5_AVAILABLE or not self._connected:
            return []
        with self._lock:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
                
            if positions is None:
                err = mt5.last_error()
                if err[0] != 1:  # 1 = success, just no positions
                    logger.error(f"Failed to get positions, error code: {err}")
                return []
                
            return [p._asdict() for p in positions]

    def get_rates(self, symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
        """Get OHLCV bars. Returns DataFrame or None."""
        if not MT5_AVAILABLE or not self._connected:
            return None
        with self._lock:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.error(f"Failed to get rates for {symbol}, error code: {mt5.last_error()}")
                return None
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
    def order_send(self, request: Dict[str, Any]) -> Any:
        # Returns MT5 OrderSendResult
        if not MT5_AVAILABLE or not self._connected:
            return None
        with self._lock:
            res = mt5.order_send(request)
            if res is None:
                err = mt5.last_error()
                logger.error(f"mt5.order_send returned None. last_error: {err}")
            return res

# Singleton
mt5_conn = MT5Connection()
