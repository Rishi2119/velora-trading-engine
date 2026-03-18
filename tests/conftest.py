import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from datetime import datetime, timedelta

@pytest.fixture
def mock_mt5():
    """Universal MT5 Mock for unit testing without the terminal."""
    mock = MagicMock()
    
    # Mock account info
    mock.account_info.return_value._asdict.return_value = {
        "balance": 10000.0,
        "equity": 10000.0,
        "margin_free": 5000.0,
        "currency": "USD",
        "login": 123456,
        "server": "MetaQuotes-Demo",
    }
    
    # Mock symbol info
    sym_info = MagicMock()
    sym_info._asdict.return_value = {
        "name": "EURUSD",
        "digits": 5,
        "spread": 10,
        "filling_mode": 3,  # FOK | IOC
        "trade_contract_size": 100000,
        "volume_min": 0.01,
        "volume_step": 0.01,
    }
    mock.symbol_info.return_value = sym_info
    
    # Mock order response
    order_res = MagicMock()
    order_res.retcode = 10009  # TRADE_RETCODE_DONE
    order_res.order = 999999
    order_res.price = 1.1000
    order_res.volume = 0.1
    mock.order_send.return_value = order_res
    
    return mock

@pytest.fixture
def sample_ohlcv():
    """Realistic OHLCV data for feature engineering and backtesting tests."""
    np.random.seed(42)
    dates = [datetime.now() - timedelta(minutes=i*15) for i in range(200)]
    dates.reverse()
    
    # Random walk for price
    prices = 1.1000 + np.cumsum(np.random.normal(0, 0.001, 200))
    
    df = pd.DataFrame({
        "time": dates,
        "open": prices - 0.0001,
        "high": prices + 0.0005,
        "low": prices - 0.0005,
        "close": prices,
        "tick_volume": np.random.randint(100, 1000, 200)
    })
    return df

@pytest.fixture
def mock_strategy_manager():
    """Mocks the StrategyManager to return predictable signals."""
    from backend.app.strategies.strategy_manager import SignalResult
    mock = MagicMock()
    mock.evaluate_all.return_value = [
        SignalResult(
            symbol="EURUSD",
            direction="BUY",
            entry=1.1000,
            sl=1.0950,
            tp=1.1100,
            confidence=0.85,
            strategy_name="EmaRsi_Trend",
            metadata={"reason": "Test trend"}
        )
    ]
    return mock
