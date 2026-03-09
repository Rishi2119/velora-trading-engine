import MetaTrader5 as mt5
import pandas as pd

def connect_mt5():
    mt5.shutdown()
    if not mt5.initialize():
        raise RuntimeError("MT5 connection failed")

def get_live_data(symbol, timeframe, bars=300):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df
