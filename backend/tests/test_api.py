"""
Velora Backend — API Tests
Run with: cd trading_engins && python -m pytest backend/tests/ -v
"""
# Set test environment BEFORE importing app modules so Settings() picks them up.
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def client():
    from backend.database.database import init_db
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Auth token helper ─────────────────────────────────────────────────────────

async def _register_and_token(client, email: str, password: str = "securepass123") -> str:
    """Register a user (or skip if already exists) and return a JWT."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": email, "password": password, "full_name": "Test",
    })
    if resp.status_code == 409:
        resp = await client.post("/api/v1/auth/login", json={
            "email": email, "password": password,
        })
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["access_token"]


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "name" in resp.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@velora.com",
        "password": "testpass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["email"] == "test@velora.com"


@pytest.mark.asyncio
async def test_register_password_too_short(client):
    """Password shorter than 8 characters must be rejected."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "short@velora.com",
        "password": "abc",
    })
    assert resp.status_code == 400
    assert "8" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@velora.com",
        "password": "testpass123",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@velora.com",
        "password": "anotherpass",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@velora.com",
        "password": "mypassword1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@velora.com",
        "password": "mypassword1",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@velora.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_password_exact_minimum(client):
    """Exactly 8 characters must be accepted."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "exact8@velora.com",
        "password": "abcd1234",
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_auth(client):
    token = await _register_and_token(client, "me@velora.com")
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@velora.com"


# ── Trading (demo mode) ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trading_stats(client):
    resp = await client.get("/api/v1/trading/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "account_balance" in data or "demo_mode" in data


@pytest.mark.asyncio
async def test_trading_open_positions(client):
    resp = await client.get("/api/v1/trading/open-positions")
    assert resp.status_code == 200
    data = resp.json()
    assert "trades" in data


@pytest.mark.asyncio
async def test_kill_switch_status(client):
    resp = await client.get("/api/v1/trading/kill-switch")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_kill_switch_requires_auth(client):
    """Activating kill switch without JWT must return 401."""
    resp = await client.post("/api/v1/trading/kill-switch/activate")
    assert resp.status_code == 401


# ── Risk endpoint ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_risk_stats(client):
    resp = await client.get("/api/v1/trading/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert "max_daily_loss" in data
    assert "risk_per_trade" in data
    assert "kill_switch_active" in data


# ── Trade execution input validation ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_trade_requires_auth(client):
    resp = await client.post("/api/v1/trading/execute", json={
        "symbol": "EURUSD", "direction": "BUY", "lots": 0.01,
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_execute_trade_invalid_direction(client):
    token = await _register_and_token(client, "trader@velora.com")
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "EURUSD", "direction": "HOLD", "lots": 0.01},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_trade_invalid_lots(client):
    token = await _register_and_token(client, "trader@velora.com")
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "EURUSD", "direction": "BUY", "lots": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_trade_invalid_symbol(client):
    token = await _register_and_token(client, "trader@velora.com")
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "", "direction": "BUY", "lots": 0.01},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ── Trade history symbol filter ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trade_history(client):
    resp = await client.get("/api/v1/trading/history")
    assert resp.status_code == 200
    assert "trades" in resp.json()


@pytest.mark.asyncio
async def test_trade_history_with_symbol_filter(client):
    resp = await client.get("/api/v1/trading/history?symbol=EURUSD")
    assert resp.status_code == 200
    data = resp.json()
    assert "trades" in data
    for t in data["trades"]:
        assert t["symbol"].upper() == "EURUSD"


# ── Strategies ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_strategies(client):
    resp = await client.get("/api/v1/trading/strategies")
    assert resp.status_code == 200
    data = resp.json()
    assert "volatility_breakout" in data
    assert "london_breakout" in data


@pytest.mark.asyncio
async def test_update_strategies_requires_auth(client):
    resp = await client.put("/api/v1/trading/strategies", json={"london_breakout": False})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_strategies_persisted(client):
    token = await _register_and_token(client, "strat@velora.com")
    resp = await client.put(
        "/api/v1/trading/strategies",
        json={"london_breakout": False, "volatility_breakout": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "london_breakout" in data["updated"]

    # Verify change is reflected in GET
    resp2 = await client.get("/api/v1/trading/strategies")
    assert resp2.status_code == 200
    assert resp2.json()["london_breakout"] is False


# ── Analytics ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_performance(client):
    resp = await client.get("/api/v1/analytics/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data or "demo_mode" in data


@pytest.mark.asyncio
async def test_equity_curve(client):
    resp = await client.get("/api/v1/analytics/equity-curve")
    assert resp.status_code == 200
    assert "curve" in resp.json()


# ── Market  ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_market_prices(client):
    resp = await client.get("/api/v1/market/prices")
    assert resp.status_code == 200
    data = resp.json()
    assert "prices" in data
    assert len(data["prices"]) > 0
