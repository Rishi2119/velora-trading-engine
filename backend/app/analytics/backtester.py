"""
Historical Backtesting Engine.
Replays OHLCV data through the FeatureEngine and StrategyManager.
Calculates performance metrics, win rate, and drawdown.
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.app.engine.feature_engine import FeatureEngine
from backend.app.strategies.strategy_manager import StrategyManager
from backend.app.strategies.regime_detector import RegimeDetector

logger = logging.getLogger(__name__)


class Backtester:
    """Offline engine for testing strategies against historical OHLCV."""
    
    def __init__(self, initial_balance: float = 10000.0, risk_per_trade: float = 0.01):
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        
        # We instantiate fresh engines to avoid polluting the live cache
        self.feature_engine = FeatureEngine()
        self.strategy_manager = StrategyManager()
        
    def run_backtest(self, symbol: str, df: pd.DataFrame, point_size: float = 0.00001) -> Dict[str, Any]:
        """
        Main backtest loop.
        Expects a DataFrame with ['time', 'open', 'high', 'low', 'close', 'tick_volume']
        """
        if len(df) < 250:
            return {"error": "Not enough data points. Need at least 250 rows for initial EMA/RSI buffering."}
            
        logger.info(f"Starting backtest on {symbol} with {len(df)} candles...")
        
        balance = self.initial_balance
        equity_curve = [balance]
        trades = []
        
        # For simplicity, we step through the DataFrame in chunks so the FeatureEngine 
        # calculates rolling indicators correctly, mimicking real-time bar closures.
        # Starting from index 250 since we need warmup data.
        
        # Optimizing feature calculation: Calculate features for the whole DF at once
        features_df = df.copy()
        
        features_df['ema_fast'] = FeatureEngine._ema(features_df['close'], 50)
        features_df['ema_slow'] = FeatureEngine._ema(features_df['close'], 200)
        features_df['ema_spread_pct'] = (features_df['ema_fast'] - features_df['ema_slow']) / features_df['ema_slow'].abs() * 100
        
        features_df['rsi'] = FeatureEngine._rsi(features_df['close'], 14)
        features_df['atr'] = FeatureEngine._atr(features_df['high'], features_df['low'], features_df['close'], 14)
        features_df['atr_pct'] = features_df['atr'] / features_df['close'] * 100
        
        adx, pdi, mdi = FeatureEngine._adx(features_df['high'], features_df['low'], features_df['close'], 14)
        features_df['adx'] = adx
        features_df['plus_di'] = pdi
        features_df['minus_di'] = mdi
        
        features_df['volatility_pct'] = features_df['close'].rolling(20).std() / features_df['close'] * 100
        
        spread_pct = features_df['ema_spread_pct']
        features_df['trend_direction'] = np.where(spread_pct > 0.05, "UP", np.where(spread_pct < -0.05, "DOWN", "FLAT"))
        
        signs = np.sign(features_df['ema_fast'] - features_df['ema_slow'])
        crosses = signs != signs.shift(1)
        features_df['bars_since_ema_cross'] = features_df.groupby(crosses.cumsum()).cumcount()
        
        active_trade = None
        
        for i in range(250, len(df)):
            row = features_df.iloc[i]
            candle_time = row['time']
            high_price = row['high']
            low_price = row['low']
            
            # 1. Check if we have an active trade to manage
            if active_trade is not None:
                # Did we hit SL or TP on THIS candle?
                direction = active_trade['direction']
                sl = active_trade['sl']
                tp = active_trade['tp']
                entry = active_trade['entry']
                lots = active_trade['lots']
                
                trade_closed = False
                pnl = 0.0
                
                # Check hits (Pessimistic: If both SL and TP are hit in same candle, assume SL hit first)
                if direction == "BUY":
                    if low_price <= sl:
                        pnl = -self.risk_per_trade * balance  # Full 1R loss
                        trade_closed = True
                    elif high_price >= tp:
                        rr = (tp - entry) / (entry - sl)
                        pnl = (self.risk_per_trade * balance) * rr
                        trade_closed = True
                
                elif direction == "SELL":
                    if high_price >= sl:
                        pnl = -self.risk_per_trade * balance
                        trade_closed = True
                    elif low_price <= tp:
                        rr = (entry - tp) / (sl - entry)
                        pnl = (self.risk_per_trade * balance) * rr
                        trade_closed = True
                        
                if trade_closed:
                    balance += pnl
                    active_trade['exit_time'] = candle_time
                    active_trade['pnl'] = pnl
                    active_trade['balance_after'] = balance
                    trades.append(active_trade)
                    active_trade = None
                    equity_curve.append(balance)
                    
            # 2. Look for new signals if no active trade
            if active_trade is None:
                # We need to construct a FeatureSet for the current row
                # (Re-using the logic from feature_engine, but applied to the pre-computed DF row)
                from backend.app.engine.feature_engine import FeatureSet
                from backend.app.strategies.regime_detector import MarketRegime
                
                try:
                    features = FeatureSet(
                        symbol=symbol,
                        timeframe="H1",
                        timestamp=candle_time,
                        close=row['close'],
                        ema_fast=row['ema_fast'],
                        ema_slow=row['ema_slow'],
                        ema_spread_pct=row['ema_spread_pct'],
                        rsi=row['rsi'],
                        atr=row['atr'],
                        atr_pct=row['atr_pct'],
                        adx=row['adx'],
                        plus_di=row['plus_di'],
                        minus_di=row['minus_di'],
                        volatility_pct=row['volatility_pct'],
                        trend_direction=row['trend_direction'],
                        bars_since_ema_cross=row['bars_since_ema_cross']
                    )
                    
                    signal = self.strategy_manager.evaluate_all(symbol, features)
                    
                    if signal:
                        # Enter trade (ignoring spread/slippage for basic backtest, but could be added)
                        # Assume execution at the Close price of the signal candle
                        entry_price = features.close
                        
                        # Calculate lots based on risk and sl distance
                        sl_dist = abs(entry_price - signal.sl)
                        if sl_dist > 0:
                            active_trade = {
                                'entry_time': candle_time,
                                'direction': signal.direction,
                                'strategy': signal.strategy_name,
                                'entry': entry_price,
                                'sl': signal.sl,
                                'tp': signal.tp,
                                'lots': 1.0, # Placeholder
                                'confidence': signal.confidence
                            }
                except KeyError:
                    # Occurs if indicator math resulted in NaNs at the beginning of the dataset
                    continue

        return self._generate_report(trades, equity_curve)
        
    def _generate_report(self, trades: List[Dict], equity_curve: List[float]) -> Dict[str, Any]:
        """Aggregate trade list into a summary report."""
        if not trades:
            return {"status": "NO_TRADES_TAKEN"}
            
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
        
        # Drawdown calculation
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.cummax()
        drawdown = equity_series / rolling_max - 1.0
        max_drawdown_pct = abs(drawdown.min()) * 100
        
        # Return on Investment
        roi_pct = (equity_curve[-1] - self.initial_balance) / self.initial_balance * 100
        
        return {
            "status": "COMPLETED",
            "initial_balance": self.initial_balance,
            "final_balance": round(equity_curve[-1], 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate * 100, 2),
            "total_pnl_usd": round(total_pnl, 2),
            "roi_pct": round(roi_pct, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "trades": trades
        }

# For dependency injection / shared instance
backtester = Backtester()
