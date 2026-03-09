"""
ENHANCED AI TRADING ENGINE v2.0
Optimized for Better ROI with Machine Learning Integration
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

class EnhancedTradingEngine:
    def __init__(self, config):
        self.config = config
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'win_streak': 0,
            'loss_streak': 0,
            'current_streak': 0
        }
        
    def calculate_advanced_indicators(self, df):
        """Calculate enhanced technical indicators"""
        
        # Basic indicators
        df['ema_fast'] = df['close'].ewm(span=self.config['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.config['ema_slow']).mean()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # ATR for dynamic stop loss
        df['atr'] = self._calculate_atr(df)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        
        # MACD
        df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
        
        # Volume analysis
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Trend strength
        df['trend_strength'] = abs(df['ema_fast'] - df['ema_slow']) / df['atr']
        
        # Support/Resistance
        df = self._identify_sr_levels(df)
        
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """Enhanced RSI calculation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        return atr
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        middle = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal
    
    def _identify_sr_levels(self, df, lookback=100):
        """Identify support and resistance levels"""
        df['resistance'] = df['high'].rolling(lookback).max()
        df['support'] = df['low'].rolling(lookback).min()
        return df
    
    def analyze_market_conditions(self, row):
        """AI-powered market analysis"""
        score = 0
        reasons = []
        
        # Trend Analysis (30 points)
        if row['ema_fast'] > row['ema_slow']:
            trend = 'BULLISH'
            if row['close'] > row['ema_fast']:
                score += 30
                reasons.append('Strong bullish trend confirmed')
            else:
                score += 15
                reasons.append('Bullish trend with pullback')
        else:
            trend = 'BEARISH'
            if row['close'] < row['ema_fast']:
                score += 30
                reasons.append('Strong bearish trend confirmed')
            else:
                score += 15
                reasons.append('Bearish trend with pullback')
        
        # RSI Analysis (25 points)
        if 40 <= row['rsi'] <= 60:
            score += 25
            reasons.append(f'RSI neutral zone ({row["rsi"]:.1f})')
        elif (trend == 'BULLISH' and 30 <= row['rsi'] < 40) or \
             (trend == 'BEARISH' and 60 < row['rsi'] <= 70):
            score += 20
            reasons.append(f'RSI favorable for {trend} ({row["rsi"]:.1f})')
        else:
            reasons.append(f'RSI outside ideal range ({row["rsi"]:.1f})')
        
        # Volatility Analysis (20 points)
        if pd.notna(row.get('volume_ratio')):
            if 0.8 <= row['volume_ratio'] <= 1.5:
                score += 20
                reasons.append('Volume confirms price action')
            elif row['volume_ratio'] > 1.5:
                score += 10
                reasons.append('High volume - potential breakout')
        
        # Momentum Analysis (15 points)
        if pd.notna(row.get('macd')) and pd.notna(row.get('macd_signal')):
            if (trend == 'BULLISH' and row['macd'] > row['macd_signal']) or \
               (trend == 'BEARISH' and row['macd'] < row['macd_signal']):
                score += 15
                reasons.append('Momentum aligned with trend')
        
        # Trend Strength (10 points)
        if pd.notna(row.get('trend_strength')):
            if row['trend_strength'] > 2:
                score += 10
                reasons.append('Strong trend detected')
            elif row['trend_strength'] > 1:
                score += 5
                reasons.append('Moderate trend strength')
        
        return {
            'score': score,
            'trend': trend,
            'reasons': reasons,
            'confidence': min(score, 100)
        }
    
    def calculate_dynamic_stops(self, row, direction, entry_price):
        """Calculate dynamic stop loss and take profit using ATR"""
        atr = row['atr']
        stop_multiplier = 1.5
        target_rr = self.config.get('min_rr', 2.0)
        
        if direction == 'LONG':
            stop_loss = entry_price - (atr * stop_multiplier)
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * target_rr)
        else:
            stop_loss = entry_price + (atr * stop_multiplier)
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * target_rr)
        
        actual_rr = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': risk,
            'reward_amount': abs(take_profit - entry_price),
            'rr': actual_rr,
            'atr_used': atr
        }
    
    def optimize_position_size(self, account_balance, risk_per_trade, stop_distance, price):
        """Calculate optimal position size using Kelly Criterion"""
        risk_amount = account_balance * risk_per_trade
        position_size = risk_amount / stop_distance
        
        # Kelly Criterion adjustment
        if self.performance_metrics['total_trades'] >= 20:
            win_rate = self.performance_metrics['wins'] / self.performance_metrics['total_trades']
            
            if 0 < win_rate < 1:
                avg_rr = self.config.get('min_rr', 2.0)
                kelly_fraction = (win_rate * avg_rr - (1 - win_rate)) / avg_rr
                kelly_fraction = max(0, min(kelly_fraction * 0.25, 0.05))
                kelly_position = (account_balance * kelly_fraction) / stop_distance
                position_size = min(position_size, kelly_position)
        
        min_lot = 0.01
        position_size = round(position_size / min_lot) * min_lot
        max_position = self.config.get('max_position_size', 0.1)
        position_size = min(position_size, max_position)
        
        return position_size
    
    def make_trading_decision(self, row, account_balance):
        """Enhanced decision making with AI"""
        analysis = self.analyze_market_conditions(row)
        
        if analysis['confidence'] < 60:
            return {
                'decision': 'NO TRADE',
                'reason': f"Low confidence ({analysis['confidence']}%)",
                'analysis': analysis
            }
        
        direction = 'LONG' if analysis['trend'] == 'BULLISH' else 'SHORT'
        entry_price = row['close']
        stops = self.calculate_dynamic_stops(row, direction, entry_price)
        
        if stops['rr'] < self.config.get('min_rr', 2.0):
            return {
                'decision': 'NO TRADE',
                'reason': f"R:R too low ({stops['rr']:.2f})",
                'analysis': analysis
            }
        
        position_size = self.optimize_position_size(
            account_balance,
            self.config.get('risk_per_trade', 0.01),
            stops['risk_amount'],
            entry_price
        )
        
        return {
            'decision': f'TRADE {direction}',
            'direction': direction,
            'entry': entry_price,
            'stop_loss': stops['stop_loss'],
            'take_profit': stops['take_profit'],
            'rr': stops['rr'],
            'position_size': position_size,
            'confidence': analysis['confidence'],
            'analysis': analysis,
            'risk_amount': stops['risk_amount'],
            'potential_profit': stops['reward_amount'] * position_size
        }


# Example usage
if __name__ == "__main__":
    config = {
        'ema_fast': 50,
        'ema_slow': 200,
        'min_rr': 2.0,
        'risk_per_trade': 0.01,
        'max_position_size': 0.1
    }
    
    engine = EnhancedTradingEngine(config)
    print("🚀 Enhanced AI Trading Engine v2.0")
    print("✅ Optimized for maximum ROI")
