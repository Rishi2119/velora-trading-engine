"""
Support/Resistance Rejection Strategy
Multi-timeframe strategy with H1 trend and M15 execution
"""

import pandas as pd


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


def trend_ok(df_h1, side):
    """Check H1 trend alignment"""
    if len(df_h1) < 200:
        return False
    
    ema50 = ema(df_h1['close'], 50).iloc[-1]
    ema200 = ema(df_h1['close'], 200).iloc[-1]
    close = df_h1['close'].iloc[-1]
    
    if side == "BUY":
        return close > ema200 and ema50 > ema200
    if side == "SELL":
        return close < ema200 and ema50 < ema200
    
    return False


def find_support_zones(df, lookback=100, tolerance=0.0002):
    """Find support zones"""
    if len(df) < lookback:
        return []
    
    recent = df.tail(lookback)
    lows = recent['low'].values
    
    zones = []
    for i in range(2, len(lows) - 2):
        if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
            lows[i] < lows[i+1] and lows[i] < lows[i+2]):
            
            zone_price = lows[i]
            zones.append({
                'low': zone_price * (1 - tolerance),
                'high': zone_price * (1 + tolerance),
                'center': zone_price,
                'type': 'support'
            })
    
    return merge_zones(zones, tolerance)


def find_resistance_zones(df, lookback=100, tolerance=0.0002):
    """Find resistance zones"""
    if len(df) < lookback:
        return []
    
    recent = df.tail(lookback)
    highs = recent['high'].values
    
    zones = []
    for i in range(2, len(highs) - 2):
        if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
            highs[i] > highs[i+1] and highs[i] > highs[i+2]):
            
            zone_price = highs[i]
            zones.append({
                'low': zone_price * (1 - tolerance),
                'high': zone_price * (1 + tolerance),
                'center': zone_price,
                'type': 'resistance'
            })
    
    return merge_zones(zones, tolerance)


def merge_zones(zones, tolerance):
    """Merge nearby zones"""
    if not zones:
        return []
    
    merged = []
    zones = sorted(zones, key=lambda x: x['center'])
    
    current = zones[0]
    for zone in zones[1:]:
        if zone['low'] <= current['high'] * (1 + tolerance):
            current['low'] = min(current['low'], zone['low'])
            current['high'] = max(current['high'], zone['high'])
            current['center'] = (current['low'] + current['high']) / 2
        else:
            merged.append(current)
            current = zone
    
    merged.append(current)
    return merged


def price_in_zone(price, zone):
    """Check if price is in zone"""
    return zone['low'] <= price <= zone['high']


def bullish_rejection(df):
    """Detect bullish rejection candles"""
    if len(df) < 2:
        return False
    
    c = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(c.close - c.open)
    lower_wick = min(c.open, c.close) - c.low
    
    # Pin bar
    pin_bar = lower_wick >= 2 * body and c.close > c.open
    
    # Bullish engulfing
    engulf = c.close > prev.open and c.open < prev.close
    
    return pin_bar or engulf


def bearish_rejection(df):
    """Detect bearish rejection candles"""
    if len(df) < 2:
        return False
    
    c = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(c.close - c.open)
    upper_wick = c.high - max(c.open, c.close)
    
    # Pin bar
    pin_bar = upper_wick >= 2 * body and c.close < c.open
    
    # Bearish engulfing
    engulf = c.close < prev.open and c.open > prev.close
    
    return pin_bar or engulf


def rsi_ok(df, side):
    """Check RSI filter"""
    if len(df) < 14:
        return False
    
    r = rsi(df['close']).iloc[-1]
    
    if side == "BUY":
        return r > 40
    if side == "SELL":
        return r < 60
    
    return False


def auto_detect_sr_setup(df_h1, df_m15, lookback=100):
    """
    Automatically detect S/R setups
    
    Returns:
        Setup dict or None
    """
    price = df_m15['close'].iloc[-1]
    
    # Find zones
    support_zones = find_support_zones(df_m15, lookback)
    resistance_zones = find_resistance_zones(df_m15, lookback)
    
    # Check support (BUY setup)
    for zone in support_zones:
        if price_in_zone(price, zone):
            if bullish_rejection(df_m15) and trend_ok(df_h1, "BUY") and rsi_ok(df_m15, "BUY"):
                sl = zone['low'] * 0.9995
                risk = abs(price - sl)
                tp = price + (risk * 2)
                
                return {
                    'side': 'BUY',
                    'zone': zone,
                    'entry': price,
                    'sl': sl,
                    'tp': tp,
                    'type': 'support_rejection'
                }
    
    # Check resistance (SELL setup)
    for zone in resistance_zones:
        if price_in_zone(price, zone):
            if bearish_rejection(df_m15) and trend_ok(df_h1, "SELL") and rsi_ok(df_m15, "SELL"):
                sl = zone['high'] * 1.0005
                risk = abs(sl - price)
                tp = price - (risk * 2)
                
                return {
                    'side': 'SELL',
                    'zone': zone,
                    'entry': price,
                    'sl': sl,
                    'tp': tp,
                    'type': 'resistance_rejection'
                }
    
    return None


def resample_to_h1(df_m15):
    """Convert M15 data to H1"""
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
