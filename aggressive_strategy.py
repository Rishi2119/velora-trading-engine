"""
High Risk / High Reward Multi-Strategy System
Combines: Breakout + Mean Reversion + Trend Following
For aggressive traders seeking maximum returns
"""

import pandas as pd
import numpy as np


def ema(series, period):
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    """Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    """Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def bollinger_bands(series, period=20, std_dev=2):
    """Bollinger Bands"""
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return upper, sma, lower


# =========================
# STRATEGY 1: BREAKOUT
# =========================

def detect_london_breakout(df, lookback=5):
    """
    London Breakout Strategy
    High reward: catches strong moves
    High risk: prone to false breakouts
    
    Entry: Break of recent high/low during London session
    """
    if len(df) < lookback + 1:
        return None
    
    recent = df.tail(lookback + 1)
    current = recent.iloc[-1]
    
    # Get London session range (previous 5 candles)
    london_high = recent.iloc[:-1]['high'].max()
    london_low = recent.iloc[:-1]['low'].min()
    
    # Breakout conditions
    bullish_breakout = current['close'] > london_high
    bearish_breakout = current['close'] < london_low
    
    # Volume confirmation (if available)
    volume_spike = True
    if 'volume' in df.columns:
        avg_volume = recent.iloc[:-1]['volume'].mean()
        volume_spike = current['volume'] > avg_volume * 1.2
    
    if bullish_breakout and volume_spike:
        # Aggressive SL below breakout level
        sl = london_low * 0.9995
        risk = abs(current['close'] - sl)
        tp = current['close'] + (risk * 3)  # 3:1 RR
        
        return {
            'side': 'BUY',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'london_breakout_long',
            'strength': 'HIGH'
        }
    
    if bearish_breakout and volume_spike:
        sl = london_high * 1.0005
        risk = abs(sl - current['close'])
        tp = current['close'] - (risk * 3)
        
        return {
            'side': 'SELL',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'london_breakout_short',
            'strength': 'HIGH'
        }
    
    return None


# =========================
# STRATEGY 2: MEAN REVERSION
# =========================

def detect_mean_reversion(df):
    """
    Bollinger Band Mean Reversion
    High reward: catches reversals
    High risk: trend can continue
    
    Entry: Price touches outer bands + RSI extreme
    """
    if len(df) < 20:
        return None
    
    current = df.iloc[-1]
    
    # Calculate indicators
    upper_bb, mid_bb, lower_bb = bollinger_bands(df['close'], 20, 2.5)
    rsi_val = rsi(df['close']).iloc[-1]
    
    upper = upper_bb.iloc[-1]
    lower = lower_bb.iloc[-1]
    mid = mid_bb.iloc[-1]
    
    # Mean reversion from oversold
    if current['close'] <= lower and rsi_val < 25:
        sl = current['close'] * 0.997  # Tight SL
        tp = mid  # Target mean
        
        return {
            'side': 'BUY',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'mean_reversion_long',
            'strength': 'MEDIUM'
        }
    
    # Mean reversion from overbought
    if current['close'] >= upper and rsi_val > 75:
        sl = current['close'] * 1.003
        tp = mid
        
        return {
            'side': 'SELL',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'mean_reversion_short',
            'strength': 'MEDIUM'
        }
    
    return None


# =========================
# STRATEGY 3: AGGRESSIVE TREND
# =========================

def detect_aggressive_trend(df):
    """
    Aggressive Trend Following
    High reward: rides strong trends
    High risk: late entries
    
    Entry: EMA crossover + momentum + volatility expansion
    """
    if len(df) < 50:
        return None
    
    current = df.iloc[-1]
    
    # Calculate indicators
    ema8 = ema(df['close'], 8).iloc[-1]
    ema21 = ema(df['close'], 21).iloc[-1]
    ema50 = ema(df['close'], 50).iloc[-1]
    
    rsi_val = rsi(df['close']).iloc[-1]
    atr_val = atr(df, 14).iloc[-1]
    
    # Strong uptrend
    uptrend = (ema8 > ema21 > ema50 and 
               current['close'] > ema8 and
               rsi_val > 50 and rsi_val < 70)
    
    # Strong downtrend
    downtrend = (ema8 < ema21 < ema50 and
                 current['close'] < ema8 and
                 rsi_val < 50 and rsi_val > 30)
    
    if uptrend:
        # Wide SL for trend riding
        sl = ema21 - (atr_val * 1.5)
        risk = abs(current['close'] - sl)
        tp = current['close'] + (risk * 4)  # 4:1 RR
        
        return {
            'side': 'BUY',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'aggressive_trend_long',
            'strength': 'HIGH'
        }
    
    if downtrend:
        sl = ema21 + (atr_val * 1.5)
        risk = abs(sl - current['close'])
        tp = current['close'] - (risk * 4)
        
        return {
            'side': 'SELL',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'aggressive_trend_short',
            'strength': 'HIGH'
        }
    
    return None


# =========================
# STRATEGY 4: VOLATILITY BREAKOUT
# =========================

def detect_volatility_breakout(df):
    """
    ATR Volatility Breakout
    High reward: catches explosive moves
    High risk: false breakouts in consolidation
    
    Entry: Price breaks volatility channel
    """
    if len(df) < 20:
        return None
    
    current = df.iloc[-1]
    
    # Calculate volatility channel
    atr_val = atr(df, 14).iloc[-1]
    ema20 = ema(df['close'], 20).iloc[-1]
    
    upper_channel = ema20 + (atr_val * 2.5)
    lower_channel = ema20 - (atr_val * 2.5)
    
    # Volume expansion
    volume_expanding = True
    if 'volume' in df.columns and len(df) > 5:
        avg_vol = df['volume'].tail(5).mean()
        volume_expanding = current['volume'] > avg_vol * 1.5
    
    # Breakout up
    if current['close'] > upper_channel and volume_expanding:
        sl = ema20
        risk = abs(current['close'] - sl)
        tp = current['close'] + (risk * 3.5)
        
        return {
            'side': 'BUY',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'volatility_breakout_long',
            'strength': 'VERY_HIGH'
        }
    
    # Breakout down
    if current['close'] < lower_channel and volume_expanding:
        sl = ema20
        risk = abs(sl - current['close'])
        tp = current['close'] - (risk * 3.5)
        
        return {
            'side': 'SELL',
            'entry': current['close'],
            'sl': sl,
            'tp': tp,
            'type': 'volatility_breakout_short',
            'strength': 'VERY_HIGH'
        }
    
    return None


# =========================
# MASTER STRATEGY SELECTOR
# =========================

def aggressive_multi_strategy(df_h1, df_m15):
    """
    Combines all aggressive strategies
    Takes the highest priority setup
    
    Priority:
    1. Volatility Breakout (VERY_HIGH)
    2. London Breakout (HIGH)
    3. Aggressive Trend (HIGH)
    4. Mean Reversion (MEDIUM)
    
    Returns best setup or None
    """
    setups = []
    
    # Check all strategies
    volatility_setup = detect_volatility_breakout(df_m15)
    if volatility_setup:
        setups.append(volatility_setup)
    
    breakout_setup = detect_london_breakout(df_m15, lookback=10)
    if breakout_setup:
        setups.append(breakout_setup)
    
    trend_setup = detect_aggressive_trend(df_m15)
    if trend_setup:
        setups.append(trend_setup)
    
    reversion_setup = detect_mean_reversion(df_m15)
    if reversion_setup:
        setups.append(reversion_setup)
    
    if not setups:
        return None
    
    # Prioritize by strength
    strength_priority = {
        'VERY_HIGH': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1
    }
    
    best_setup = max(setups, key=lambda x: strength_priority[x['strength']])
    
    return best_setup


# =========================
# HELPER: RESAMPLE TO H1
# =========================

def resample_to_h1(df_m15):
    """Convert M15 to H1 for multi-timeframe analysis"""
    df = df_m15.copy()
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    
    df_h1 = df.resample('1H').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }).dropna()
    
    df_h1.reset_index(inplace=True)
    return df_h1
