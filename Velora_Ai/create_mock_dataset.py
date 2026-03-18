import pandas as pd
import os

data = {
    "trend_direction": ["uptrend", "downtrend", "sideways", "uptrend", "downtrend"],
    "structure_break": [True, False, True, False, True],
    "liquidity_sweep": [False, True, False, True, False],
    "pullback": [True, True, False, False, True],
    "momentum_strength": [0.8, 0.2, 0.5, 0.9, 0.1],
    "volatility": [0.6, 0.7, 0.4, 0.8, 0.5],
    "support_resistance_strength": [0.7, 0.8, 0.6, 0.9, 0.7],
    "session": ["London", "NewYork", "Asia", "London", "NewYork"],
    "spread": [0.1, 0.2, 0.15, 0.1, 0.2],
    "strategy_type": ["pullback_trend", "liquidity_reversal", "blackbox_trap", "structure_bos", "pullback_trend"],
    "action": ["BUY", "SELL", "NO_TRADE", "BUY", "SELL"]
}

df = pd.DataFrame(data)
os.makedirs('data', exist_ok=True)
df.to_csv('data/training_dataset.csv', index=False)
print("Created mock training_dataset.csv")
