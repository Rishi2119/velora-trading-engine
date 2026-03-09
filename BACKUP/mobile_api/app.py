"""
Trading Engine Mobile API — Live MT5 Edition
Flask REST API that reads REAL data from MetaTrader 5.
When MT5 is not connected it falls back to demo data automatically.
"""

import sys
import io
# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import json
import csv
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KILL_SWITCH_PATH  = os.path.join(BASE_DIR, "mobile_api", "KILL_SWITCH.txt")
MT5_CONFIG_PATH   = os.path.join(BASE_DIR, "mobile_api", "mt5_config.json")
CONFIG_OVERRIDE_PATH = os.path.join(BASE_DIR, "mobile_api", "config_overrides.json")

# Import the MT5 session manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mt5_manager import mt5_manager

app = Flask(__name__)
CORS(app)


# ─── Startup: auto-connect if credentials exist ───────────────────────────


def _autoconnect():
    if not os.path.exists(MT5_CONFIG_PATH):
        return
    try:
        with open(MT5_CONFIG_PATH) as f:
            cfg = json.load(f)
        acct = cfg.get("account")
        pwd  = cfg.get("password")
        srv  = cfg.get("server")
        if acct and pwd and srv and str(acct) != "0":
            print(f"[API] Auto-connecting to MT5: account={acct} server={srv}")
            result = mt5_manager.connect(int(acct), pwd, srv)
            if result.get("connected"):
                print(f"[API] MT5 connected! Balance: {result['info'].get('balance')}")
            else:
                print(f"[API] MT5 auto-connect failed: {result.get('error')}")
    except Exception as e:
        print(f"[API] Auto-connect error: {e}")


# ─── Helpers ──────────────────────────────────────────────────────────────


def load_config_overrides():
    if os.path.exists(CONFIG_OVERRIDE_PATH):
        with open(CONFIG_OVERRIDE_PATH) as f:
            return json.load(f)
    return {}


def save_config_overrides(data):
    existing = load_config_overrides()
    existing.update(data)
    with open(CONFIG_OVERRIDE_PATH, "w") as f:
        json.dump(existing, f, indent=2)


def load_mt5_config():
    if os.path.exists(MT5_CONFIG_PATH):
        with open(MT5_CONFIG_PATH) as f:
            return json.load(f)
    return {"account": 0, "password": "", "server": "", "enable_execution": False}


def save_mt5_config(data):
    existing = load_mt5_config()
    existing.update(data)
    with open(MT5_CONFIG_PATH, "w") as f:
        json.dump(existing, f, indent=2)


# ─── Demo Fallback Data ───────────────────────────────────────────────────


def _demo_trades():
    base = datetime.now()
    strategies = ["VOLATILITY_BREAKOUT", "LONDON_BREAKOUT", "AGGRESSIVE_TREND", "MEAN_REVERSION"]
    pairs = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
    pnl_values = [45.5, -15.0, 62.3, -22.1, 88.4, -30.0, 55.2, 41.0, -18.5, 73.0,
                  -12.0, 95.6, 28.0, -40.2, 66.7, 33.4, -25.0, 80.1, 47.8, -19.3]
    trades = []
    for i, pnl in enumerate(pnl_values):
        t = base - timedelta(hours=i * 3)
        direction = "LONG" if pnl > 0 else "SHORT"
        entry = 1.0900 + (i * 0.0013)
        sl_dist = 0.0050
        trades.append({
            "trade_id": f"T{1000 + i}",
            "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": pairs[i % len(pairs)],
            "strategy": strategies[i % 4],
            "direction": direction,
            "entry": round(entry, 5),
            "stop_loss": round(entry - sl_dist, 5),
            "take_profit": round(entry + sl_dist * 3.5, 5),
            "lots": 0.05,
            "pnl": pnl,
            "status": "CLOSED" if i > 2 else "OPEN",
            "rr_ratio": 3.5,
        })
    return trades


def _demo_performance():
    base = datetime.now()
    daily = []
    balance = 500.0
    for i in range(30, -1, -1):
        d = base - timedelta(days=i)
        change = (hash(str(d.date())) % 60) - 25
        balance += change
        daily.append({"date": d.strftime("%Y-%m-%d"), "pnl": round(change, 2), "balance": round(balance, 2)})
    return {
        "total_trades": 87, "winning_trades": 54, "losing_trades": 33,
        "total_pnl": round(balance - 500, 2), "win_rate": 62.1,
        "avg_rr": 3.2, "max_drawdown": -145.0, "profit_factor": 2.1,
        "balance": 500, "equity": 500, "profit": 0, "currency": "USD",
        "daily": daily,
    }


# ─── Routes ───────────────────────────────────────────────────────────────


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "message": "Trading Engine Mobile API is running.",
        "version": "1.0.0"
    })

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Overall stats — uses live MT5 data when connected."""
    kill_active = os.path.exists(KILL_SWITCH_PATH)
    is_live = mt5_manager.connected

    if is_live:
        perf = mt5_manager.get_performance_summary(days=30) or _demo_performance()
        open_positions = mt5_manager.get_open_positions()
        info = mt5_manager.get_account_info()
        balance  = info.balance  if info else perf.get("balance", 500)
        equity   = info.equity   if info else perf.get("equity", 500)
        profit   = info.profit   if info else perf.get("profit", 0)
        currency = info.currency if info else "USD"
    else:
        perf = _demo_performance()
        open_positions = []
        balance  = perf["balance"]
        equity   = perf["equity"]
        profit   = perf["profit"]
        currency = "USD"

    return jsonify({
        "account_balance": balance,
        "equity": equity,
        "open_pnl": profit,
        "currency": currency,
        "total_pnl": perf.get("total_pnl", 0),
        "win_rate": perf.get("win_rate", 0),
        "total_trades": perf.get("total_trades", 0),
        "winning_trades": perf.get("winning_trades", 0),
        "losing_trades": perf.get("losing_trades", 0),
        "open_trades_count": len(open_positions),
        "avg_rr": perf.get("avg_rr", 0),
        "max_drawdown": perf.get("max_drawdown", 0),
        "profit_factor": perf.get("profit_factor", 0),
        "kill_switch_active": kill_active,
        "mt5_connected": is_live,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/trades", methods=["GET"])
def get_trades():
    """Trade history — real MT5 deal history when connected."""
    status = request.args.get("status")
    days = request.args.get("days", 30, type=int)

    if mt5_manager.connected:
        # Merge open positions + closed history
        closed = mt5_manager.get_trade_history(days=days)
        open_pos = mt5_manager.get_open_positions()
        trades = open_pos + closed
    else:
        trades = _demo_trades()

    if status:
        trades = [t for t in trades if t.get("status", "").upper() == status.upper()]

    return jsonify({"trades": trades, "count": len(trades), "live": mt5_manager.connected})


@app.route("/api/open-trades", methods=["GET"])
def get_open_trades():
    """Live open positions from MT5."""
    if mt5_manager.connected:
        positions = mt5_manager.get_open_positions()
    else:
        positions = [t for t in _demo_trades() if t["status"] == "OPEN"]
    return jsonify({"trades": positions, "count": len(positions), "live": mt5_manager.connected})


@app.route("/api/performance", methods=["GET"])
def get_performance():
    """P&L history — real from MT5 deal history when connected."""
    days = request.args.get("days", 30, type=int)

    if mt5_manager.connected:
        perf = mt5_manager.get_performance_summary(days=days) or _demo_performance()
    else:
        perf = _demo_performance()

    return jsonify({
        "daily": perf.get("daily", [])[-days:],
        "summary": {
            "total_pnl": perf.get("total_pnl", 0),
            "win_rate": perf.get("win_rate", 0),
            "profit_factor": perf.get("profit_factor", 0),
            "avg_rr": perf.get("avg_rr", 0),
            "max_drawdown": perf.get("max_drawdown", 0),
            "balance": perf.get("balance", 500),
            "equity": perf.get("equity", 500),
        },
        "live": mt5_manager.connected,
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    overrides = load_config_overrides()
    defaults = {
        "account_balance": 500, "risk_per_trade": 0.01, "min_risk_reward": 3.0,
        "max_daily_loss": 20, "max_daily_trades": 5, "max_concurrent_trades": 2,
        "symbol": "EURUSD", "timeframe": "M15", "enable_execution": False,
        "enable_session_filter": True, "allowed_sessions": ["LONDON", "NEW_YORK"],
        "enable_news_filter": True, "max_spread_pips": 2.0,
        "breakeven_trigger_pips": 15, "trailing_start_pips": 20, "trailing_distance_pips": 10,
    }
    defaults.update(overrides)
    # Inject live balance
    if mt5_manager.connected:
        info = mt5_manager.get_account_info()
        if info:
            defaults["account_balance"] = info.balance
    return jsonify(defaults)


@app.route("/api/config", methods=["PUT"])
def update_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    safe = ["risk_per_trade", "min_risk_reward", "max_daily_loss", "max_daily_trades",
            "max_concurrent_trades", "enable_session_filter", "enable_news_filter",
            "max_spread_pips", "breakeven_trigger_pips", "trailing_start_pips",
            "trailing_distance_pips", "allowed_sessions"]
    save_config_overrides({k: v for k, v in data.items() if k in safe})
    return jsonify({"success": True})


@app.route("/api/strategies", methods=["GET"])
def get_strategies():
    o = load_config_overrides()
    return jsonify({
        "volatility_breakout": o.get("enable_volatility_breakout", True),
        "london_breakout":     o.get("enable_london_breakout",     True),
        "aggressive_trend":    o.get("enable_aggressive_trend",    True),
        "mean_reversion":      o.get("enable_mean_reversion",      True),
    })


@app.route("/api/strategies", methods=["PUT"])
def update_strategies():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    save_config_overrides({
        "enable_volatility_breakout": data.get("volatility_breakout", True),
        "enable_london_breakout":     data.get("london_breakout",     True),
        "enable_aggressive_trend":    data.get("aggressive_trend",    True),
        "enable_mean_reversion":      data.get("mean_reversion",      True),
    })
    return jsonify({"success": True})


@app.route("/api/kill-switch", methods=["GET"])
def get_kill_switch():
    return jsonify({"active": os.path.exists(KILL_SWITCH_PATH)})


@app.route("/api/kill-switch", methods=["POST"])
def activate_kill_switch():
    with open(KILL_SWITCH_PATH, "w") as f:
        f.write(f"Kill switch activated via mobile app at {datetime.now()}\n")
    return jsonify({"success": True, "active": True})


@app.route("/api/kill-switch", methods=["DELETE"])
def deactivate_kill_switch():
    if os.path.exists(KILL_SWITCH_PATH):
        os.remove(KILL_SWITCH_PATH)
    return jsonify({"success": True, "active": False})


# ─── MT5 Connection Routes ────────────────────────────────────────────────


@app.route("/api/mt5/status", methods=["GET"])
def mt5_status():
    """Live connection status + account summary."""
    if not mt5_manager.connected:
        return jsonify({
            "connected": False,
            "error": mt5_manager.last_error,
            "account": None,
        })
    info = mt5_manager.get_account_info()
    return jsonify({
        "connected": True,
        "account": {
            "broker": info.company   if info else "",
            "login":  str(info.login) if info else "",
            "server": info.server    if info else "",
            "balance": round(info.balance, 2) if info else 0,
            "equity":  round(info.equity,  2) if info else 0,
            "profit":  round(info.profit,  2) if info else 0,
            "currency": info.currency if info else "USD",
            "leverage": info.leverage if info else 0,
            "account_type": "Demo" if info and "demo" in info.server.lower() else "Live",
        },
    })


@app.route("/api/mt5/config", methods=["GET"])
def get_mt5_config():
    cfg = load_mt5_config()
    masked = cfg.copy()
    if masked.get("password"):
        masked["password"] = "•" * len(str(masked["password"]))
    masked["connected"] = mt5_manager.connected
    return jsonify(masked)


@app.route("/api/mt5/config", methods=["PUT"])
def update_mt5_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    save_mt5_config({k: v for k, v in data.items() if k in ["account", "password", "server", "enable_execution"]})
    return jsonify({"success": True})


@app.route("/api/mt5/connect", methods=["POST"])
def connect_mt5():
    """Connect to MT5 with provided credentials."""
    data = request.get_json() or {}
    account  = data.get("account", "")
    password = data.get("password", "")
    server   = data.get("server", "")

    if not account or not password or not server:
        return jsonify({"connected": False, "error": "Account, password and server are required."}), 400

    result = mt5_manager.connect(int(account), password, server)

    if result.get("connected"):
        # Persist credentials
        save_mt5_config({"account": account, "password": password, "server": server, "last_status": "connected"})

    return jsonify(result)


@app.route("/api/mt5/disconnect", methods=["POST"])
def disconnect_mt5():
    mt5_manager.disconnect()
    save_mt5_config({"last_status": "disconnected"})
    return jsonify({"connected": False, "message": "Disconnected from MT5."})


@app.route("/api/mt5/reconnect", methods=["POST"])
def reconnect_mt5():
    result = mt5_manager.reconnect()
    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "mt5_connected": mt5_manager.connected,
        "time": datetime.now().isoformat(),
    })


# ─── Autonomous AI Agent Routes ──────────────────────────────────────────

try:
    from agent_manager import agent_manager
except ImportError as e:
    print(f"[API] Warning: Could not import agent_manager: {e}")
    agent_manager = None

@app.route("/api/agent/start", methods=["POST"])
def start_agent():
    if not agent_manager:
        return jsonify({"error": "Agent manager not available"}), 500
    success = agent_manager.start()
    return jsonify({"success": success, "status": agent_manager.get_status()})

@app.route("/api/agent/stop", methods=["POST"])
def stop_agent():
    if not agent_manager:
        return jsonify({"error": "Agent manager not available"}), 500
    success = agent_manager.stop()
    return jsonify({"success": success, "status": agent_manager.get_status()})

@app.route("/api/agent/status", methods=["GET"])
def get_agent_status():
    if not agent_manager:
        return jsonify({"error": "Agent manager not available"}), 500
    return jsonify(agent_manager.get_status())


# ─── Startup ──────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("[API] Trading Engine Mobile API (Live MT5 Edition)")
    print("[API] Starting on http://0.0.0.0:5050")
    _autoconnect()
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
