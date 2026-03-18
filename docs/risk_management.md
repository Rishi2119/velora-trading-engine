# Risk Management Framework

Velora employs a multi-layered risk validation system to protect your capital and ensure compliance with institutional-grade trading practices.

## The 9 Risk Layers

Before a signal is passed to the execution engine, it must be approved by the `RiskManager`.

1.  **Session Filter**: Prevents trading outside liquid market hours (London/NY overlap).
2.  **News Filter**: Blocks trades during high-impact economic events (±15 mins).
3.  **Circuit Breaker**: Halts the engine if daily realized drawdown exceeds a threshold (e.g. 5%).
4.  **Spread Filter**: Rejects trades if the broker's spread is wider than allowed (e.g. 2 pips).
5.  **Regime Filter**: Blocks specific strategies if the market regime is incompatible (e.g. Trending vs. Volatile).
6.  **Daily Trade Limit**: Caps the total number of trades per symbol per day.
7.  **Concurrency Limit**: Prevents opening too many simultaneous positions across all symbols.
8.  **Lot Sizing**: Dynamically calculates lot sizes based on 1% per-trade risk and pip distance to SL.
9.  **Margin Check**: Ensures the account has sufficient free margin to support the new leverage.

## Dynamic Lot Sizing Formula

Lot size is calculated as:
`Lots = (Account Balance * Risk %) / (SL Distance in Pips * Pip Value)`

The engine automatically fetches the broker's `tick_value` and `contract_size` to ensure accuracy on all pairs (Forex, Metals, Crypto).

## Kill Switch

The global `Kill Switch` (`backend/app/core/kill_switch.py`) is the ultimate emergency brake. When activated:
- All open positions are immediate closed at market price.
- The Autonomous Loop is paused.
- No new signals are processed.
- Active alerts are sent to Telegram and Dashboard WebSockets.
