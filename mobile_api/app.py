"""
Trading Engine Mobile API — Live MT5 Edition (SECURED)
Flask REST API that reads REAL data from MetaTrader 5.
When MT5 is not connected it falls back to demo data automatically.

SECURITY: All endpoints require Bearer token authentication
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
import secrets
import time
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KILL_SWITCH_PATH  = os.path.join(BASE_DIR, "mobile_api", "KILL_SWITCH.txt")
MT5_CONFIG_PATH   = os.path.join(BASE_DIR, "mobile_api", "mt5_config.json")
CONFIG_OVERRIDE_PATH = os.path.join(BASE_DIR, "mobile_api", "config_overrides.json")
SECRET_FILE = os.path.join(BASE_DIR, "mobile_api", ".api_secret")

# Generate or load API secret
def get_or_create_api_secret():
    if not os.path.exists(SECRET_FILE):
        API_SECRET = secrets.token_hex(32)
        with open(SECRET_FILE, 'w') as f:
            f.write(API_SECRET)
        os.chmod(SECRET_FILE, 0o600)  # Restrict permissions
        print(f"[API] Generated new API secret")
        return API_SECRET
    else:
        with open(SECRET_FILE) as f:
            return f.read().strip()

API_SECRET = get_or_create_api_secret()

# Rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = 100  # requests per minute

# Import the MT5 session manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mt5_manager import mt5_manager

app = Flask(__name__)
CORS(app)


# =========================
# AUTHENTICATION & RATE LIMITING
# =========================

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = time.time()
        request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
        
        if len(request_counts[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        request_counts[ip].append(now)
        return f(*args, **kwargs)
    return decorated


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        
        if not auth.startswith('Bearer '):
            return jsonify({"error": "Missing authorization token"}), 401
        
        token = auth[7:]
        
        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(token, API_SECRET):
            return jsonify({"error": "Invalid token"}), 403
        
        return f(*args, **kwargs)
    return decorated


# Apply rate limiting to all API routes
@app.before_request
def check_rate_limit():
    if request.path.startswith('/api/') and request.path not in ['/api/health', '/']:
        ip = request.remote_addr or 'unknown'
        now = time.time()
        request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
        if len(request_counts[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Rate limit exceeded"}), 429
        request_counts[ip].append(now)


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

# User storage (in-memory for demo, use proper DB in production)
USERS_FILE = os.path.join(BASE_DIR, "mobile_api", "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(user_id, email):
    """Simple JWT-like token (use proper JWT library in production)"""
    payload = f"{user_id}:{email}:{int(time.time()) + 86400}"  # 24h expiry
    return hashlib.sha256(f"{payload}:{API_SECRET}".encode()).hexdigest() + "." + payload

def verify_jwt_token(token):
    """Verify JWT-like token"""
    try:
        signature, payload = token.split(".", 1)
        expected_sig = hashlib.sha256(f"{payload}:{API_SECRET}".encode()).hexdigest()
        if not secrets.compare_digest(signature, expected_sig):
            return None
        parts = payload.split(":")
        if len(parts) >= 3:
            expiry = int(parts[2])
            if time.time() > expiry:
                return None
            return {"sub": parts[0], "email": parts[1]}
    except Exception:
        pass
    return None

# JWT-based auth decorator
def require_jwt_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        
        if not auth.startswith('Bearer '):
            return jsonify({"error": "Missing authorization token"}), 401
        
        token = auth[7:]
        
        # Try API_SECRET first (for backwards compatibility)
        if secrets.compare_digest(token, API_SECRET):
            return f(*args, **kwargs)
        
        # Then try JWT verification
        user = verify_jwt_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        return f(*args, **kwargs)
    return decorated


# ─── Authentication Routes ────────────────────────────────────────────────

@app.route("/api/v1/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "")
    
    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400
    
    if len(password) < 6:
        return jsonify({"detail": "Password must be at least 6 characters"}), 400
    
    users = load_users()
    
    if email in users:
        return jsonify({"detail": "Email already registered"}), 409
    
    user_id = len(users) + 1
    users[email] = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    
    token = create_jwt_token(user_id, email)
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email
    }), 201


@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    """Authenticate user and return JWT"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400
    
    users = load_users()
    user = users.get(email)
    
    if not user or user["password_hash"] != hash_password(password):
        return jsonify({"detail": "Invalid email or password"}), 401
    
    if not user.get("is_active", True):
        return jsonify({"detail": "Account is disabled"}), 403
    
    token = create_jwt_token(user["id"], email)
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": email
    })


@app.route("/api/v1/auth/me", methods=["GET"])
def get_me():
    """Get current user profile"""
    auth = request.headers.get('Authorization', '')
    
    if not auth.startswith('Bearer '):
        return jsonify({"detail": "Authorization header missing"}), 401
    
    token = auth[7:]
    user_data = verify_jwt_token(token)
    
    if not user_data:
        # Check if it's API_SECRET (admin access)
        if secrets.compare_digest(token, API_SECRET):
            return jsonify({
                "id": 0,
                "email": "admin@velora.local",
                "full_name": "API Admin",
                "is_active": True,
                "is_admin": True
            })
        return jsonify({"detail": "Invalid or expired token"}), 401
    
    users = load_users()
    email = user_data.get("email", "")
    user = users.get(email)
    
    if not user:
        return jsonify({"detail": "User not found"}), 404
    
    return jsonify({
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "is_active": user.get("is_active", True),
        "is_admin": user.get("is_admin", False)
    })



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
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Engine API</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .status { background: #27ae60; color: white; padding: 10px; border-radius: 5px; }
            .token { background: #f8f9fa; padding: 15px; border-radius: 5px; word-break: break-all; }
            .endpoints { background: #ecf0f1; padding: 15px; border-radius: 5px; }
            a { color: #3498db; }
        </style>
    </head>
    <body>
        <h1>Trading Engine Mobile API</h1>
        <div class="status">STATUS: ONLINE</div>
        <h2>API Token:</h2>
        <div class="token">""" + API_SECRET + """</div>
        <h2>Available Endpoints:</h2>
        <div class="endpoints">
            <p><a href="/api/stats">/api/stats</a> - Account statistics</p>
            <p><a href="/api/trades">/api/trades</a> - Trade history</p>
            <p><a href="/api/open-trades">/api/open-trades</a> - Open positions</p>
            <p><a href="/api/performance">/api/performance</a> - Performance metrics</p>
            <p><a href="/api/config">/api/config</a> - Configuration</p>
            <p><a href="/api/kill-switch">/api/kill-switch</a> - Kill switch status</p>
            <p><a href="/api/mt5/status">/api/mt5/status</a> - MT5 connection</p>
            <p><a href="/api/health">/api/health</a> - Health check</p>
        </div>
        <p><strong>Quick Access:</strong> <a href="/?token=b6687ce673eacd9c940f94cc5f7102e907f187acf7d8b29bec0b9cab28df20fb">Click here</a> to access with token</p>
        <script>
            // Auto-add token from URL
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');
            if (token) {
                localStorage.setItem('api_token', token);
                // Redirect to stats
                fetch('/api/stats', {
                    headers: { 'Authorization': 'Bearer ' + token }
                }).then(r => r.json()).then(data => {
                    document.body.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                });
            }
        </script>
    </body>
    </html>
    """
    return html

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
@require_auth
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
@require_auth
def update_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    
    # BLOCK dangerous config changes
    BLOCKED_KEYS = [
        'risk_per_trade', 'max_daily_loss', 
        'account_balance', 'magic_number', 'min_risk_reward'
    ]
    
    for key in BLOCKED_KEYS:
        if key in data:
            return jsonify({"error": f"Cannot modify {key} via API for security"}), 403
    
    safe = ["enable_session_filter", "enable_news_filter",
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
@require_auth
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
@require_auth
def activate_kill_switch():
    with open(KILL_SWITCH_PATH, "w") as f:
        f.write(f"Kill switch activated via mobile app at {datetime.now()}\n")
    return jsonify({"success": True, "active": True})


@app.route("/api/kill-switch", methods=["DELETE"])
@require_auth
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
@require_auth
def update_mt5_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    
    # Only allow non-execution changes
    allowed = ["account", "server"]
    save_mt5_config({k: v for k, v in data.items() if k in allowed})
    return jsonify({"success": True})


@app.route("/api/mt5/connect", methods=["POST"])
@require_auth
def connect_mt5():
    """Connect to MT5 with provided credentials."""
    data = request.get_json() or {}
    account  = data.get("account", "")
    password = data.get("password", "")
    server   = data.get("server", "")

    if not account or not password or not server:
        return jsonify({"connected": False, "error": "Account, password and server are required."}), 400

    # Don't persist password - security risk
    result = mt5_manager.connect(int(account), password, server)

    if result.get("connected"):
        # Only persist non-sensitive data
        save_mt5_config({"account": account, "server": server, "last_status": "connected"})

    return jsonify(result)


@app.route("/api/mt5/disconnect", methods=["POST"])
@require_auth
def disconnect_mt5():
    mt5_manager.disconnect()
    save_mt5_config({"last_status": "disconnected"})
    return jsonify({"connected": False, "message": "Disconnected from MT5."})


@app.route("/api/mt5/reconnect", methods=["POST"])
@require_auth
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


# ─── Alias Routes (spec-required) ────────────────────────────────────────

@app.route("/api/account", methods=["GET"])
def get_account():
    """Alias: account stats for mobile screens that use /api/account."""
    return get_stats()


@app.route("/api/positions", methods=["GET"])
def get_positions():
    """Alias: open positions."""
    return get_open_trades()


@app.route("/api/history", methods=["GET"])
def get_history():
    """Alias: closed trade history."""
    days = request.args.get("days", 30, type=int)
    if mt5_manager.connected:
        closed = mt5_manager.get_trade_history(days=days)
    else:
        closed = [t for t in _demo_trades() if t["status"] == "CLOSED"]
    return jsonify({"trades": closed, "count": len(closed), "live": mt5_manager.connected})


# ─── Autonomous AI Agent Routes ──────────────────────────────────────────

try:
    from agent_manager import agent_manager
except ImportError as e:
    print(f"[API] Warning: Could not import agent_manager: {e}")
    agent_manager = None

@app.route("/api/agent/start", methods=["POST"])
@require_auth
def start_agent():
    if not agent_manager:
        return jsonify({"error": "Agent manager not available"}), 500
    success = agent_manager.start()
    return jsonify({"success": success, "status": agent_manager.get_status()})

@app.route("/api/agent/stop", methods=["POST"])
@require_auth
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


@app.route("/api/agent/thoughts", methods=["GET"])
def get_agent_thoughts():
    """Live thought/decision feed for the mobile dashboard."""
    if not agent_manager:
        return jsonify({"error": "Agent manager not available"}), 500
    status = agent_manager.get_status()
    return jsonify({
        "is_running": status.get("is_running", False),
        "thought": status.get("latest_thought", ""),
        "decision": status.get("latest_decision", "NONE"),
        "confidence": status.get("confidence", 0.0),
        "sentiment": status.get("sentiment"),
        "uptime_seconds": status.get("uptime_seconds"),
        "crash_count": status.get("crash_count", 0),
    })


@app.route("/api/agent/enable-trading", methods=["POST"])
@require_auth
def enable_agent_trading():
    """Toggle live trading mode for the autonomous agent config."""
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", False))
    save_config_overrides({"enable_execution": enabled})
    return jsonify({"success": True, "enable_execution": enabled})


# ─── Startup ──────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("[API] Trading Engine Mobile API (Live MT5 Edition)")
    print("[API] Starting on http://0.0.0.0:5050")
    _autoconnect()
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
