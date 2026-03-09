"""
Executor Module - FINAL FIXED VERSION
MT5 Python compatible
Handles connection, execution, stop validation, and position management
"""

import MetaTrader5 as mt5


MAGIC_NUMBER = 234000


# =========================
# CONNECTION
# =========================
def connect(account=None, password=None, server=None):
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return False

    if account and password and server:
        if not mt5.login(account, password=password, server=server):
            print(f"❌ MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False

    acc = mt5.account_info()
    print(f"✅ MT5 Connected | Account: {acc.login} | Balance: {acc.balance}")
    return True


def disconnect():
    mt5.shutdown()
    print("🔌 MT5 Disconnected")


# =========================
# BROKER STOP ADJUSTMENT
# =========================
def adjust_stops_to_broker(symbol, entry, sl, tp, direction):
    info = mt5.symbol_info(symbol)
    if info is None:
        return sl, tp

    point = info.point
    min_stop = info.trade_stops_level * point

    # Broker sometimes reports 0 → use safe default (20 pips)
    if min_stop <= 0:
        min_stop = 20 * point

    if direction == "LONG":
        sl = min(sl, entry - min_stop)
        tp = max(tp, entry + min_stop)
    else:
        sl = max(sl, entry + min_stop)
        tp = min(tp, entry - min_stop)

    return sl, tp


# =========================
# ORDER EXECUTION (SAFE)
# =========================
def place_trade(symbol, direction, volume, sl, tp, comment="AI_ENGINE"):
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"❌ Symbol not found: {symbol}")
        return None

    if not info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"❌ No tick data for {symbol}")
        return None

    if direction == "LONG":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif direction == "SHORT":
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        print(f"❌ Invalid direction: {direction}")
        return None

    # 🔧 Adjust SL / TP to broker rules
    sl, tp = adjust_stops_to_broker(symbol, price, sl, tp, direction)

    # Round to symbol precision
    digits = info.digits
    sl = round(sl, digits)
    tp = round(tp, digits)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 50,
        "magic": MAGIC_NUMBER,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC
        # ❌ NO type_filling (broker decides internally)
    }

    result = mt5.order_send(request)

    if result is None:
        print("❌ order_send returned None")
        return None

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Order failed: {result.retcode} | {result.comment}")
        return None

    print(f"✅ ORDER EXECUTED | Ticket: {result.order}")
    print(f"   Entry: {price} | SL: {sl} | TP: {tp}")
    return result


# =========================
# POSITIONS
# =========================
def get_open_positions(symbol=None):
    positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    if positions is None:
        return []
    return [p for p in positions if p.magic == MAGIC_NUMBER]


def close_trade(ticket):
    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        print(f"❌ Position not found: {ticket}")
        return None

    pos = pos[0]
    symbol = pos.symbol
    volume = pos.volume

    tick = mt5.symbol_info_tick(symbol)
    if pos.type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "position": ticket,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 50,
        "magic": MAGIC_NUMBER,
        "comment": "AI_CLOSE",
        "type_time": mt5.ORDER_TIME_GTC
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Close failed: {result.retcode}")
        return None

    print(f"✅ Position closed: {ticket}")
    return result


# =========================
# ACCOUNT INFO
# =========================
def get_account_info():
    acc = mt5.account_info()
    if acc is None:
        return None

    return {
        "login": acc.login,
        "balance": acc.balance,
        "equity": acc.equity,
        "margin": acc.margin,
        "free_margin": acc.margin_free,
        "profit": acc.profit,
        "leverage": acc.leverage
    }
