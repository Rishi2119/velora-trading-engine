# Strategy Development Guide

The Velora engine is designed to be strategy-agnostic. New strategies can be added by implementing the `BaseStrategy` interface and registering them in the `StrategyManager`.

## Creating a Strategy

1.  **Inherit from `BaseStrategy`**:
    Located in `backend/app/strategies/strategy_manager.py`.

2.  **Define `evaluate(symbol, features)`**:
    - `symbol`: The string name of the pair (e.g. "EURUSD").
    - `features`: A `FeatureSet` dataclass containing computed indicators for the current candle.
    - Return a `SignalResult` if a trade should fire, or `None`.

### Example: Simple SMA Crossover
```python
from .strategy_manager import BaseStrategy, SignalResult, FeatureSet

class SmaCrossoverStrategy(BaseStrategy):
    def evaluate(self, symbol: str, features: FeatureSet) -> Optional[SignalResult]:
        # Buy if SMA20 crosses above SMA50
        if features.sma20 > features.sma50 and features.prev_sma20 <= features.prev_sma50:
            return SignalResult(
                symbol=symbol,
                direction="BUY",
                entry=features.close,
                sl=features.close - features.atr * 2,
                tp=features.close + features.atr * 3,
                confidence=0.75,
                strategy_name="SmaCross"
            )
        return None
```

## Strategy Registration

In `backend/app/strategies/strategy_manager.py`, add your strategy instance to the `strategies` list:

```python
self.strategies: List[BaseStrategy] = [
    EmaRsiStrategy(),
    BosStrategy(),
    SmaCrossoverStrategy() # Add here
]
```

## Tips for Reliable Strategies

- **Use ATR for Stops**: Hardcoded pip values are fragile. Always use ATR-based SL/TP to normalize for volatility.
- **Check the Regime**: Use `features.regime` to prevent trend strategies from firing in range-bound markets.
- **Statelessness**: Indicators are already computed in the `FeatureSet`. Avoid storing state inside the strategy class if possible; rely on `features.prev_close`, etc.
