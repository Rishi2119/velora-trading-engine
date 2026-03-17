"""
Velora Backend — API Tests
Run with: cd trading_engins && python -m pytest backend/tests/ -v
"""
import os

# Override settings BEFORE any backend imports so the Settings singleton
# picks up the in-memory database and test keys.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

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
    # Explicitly initialize the database tables (lifespan is not triggered by ASGITransport)
    from backend.database.database import init_db
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "mt5_connected" in data


# ── Root ─────────────────────────────────────────────────────────────────────


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
        "password": "mypassword",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@velora.com",
        "password": "mypassword",
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
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_auth(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "me@velora.com",
        "password": "mypassword",
    })
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@velora.com"


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "short@velora.com",
        "password": "abc123",  # only 6 chars — below minimum of 8
    })
    assert resp.status_code == 400
    assert "8" in resp.json()["detail"]


# ── Trading input validation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_trade_invalid_direction(client):
    """Direction must be BUY or SELL."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "trader1@velora.com",
        "password": "securepass",
    })
    token = reg.json()["access_token"]
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "EURUSD", "direction": "LONG", "lots": 0.01},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_trade_invalid_lots(client):
    """Lots must be > 0."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "trader2@velora.com",
        "password": "securepass",
    })
    token = reg.json()["access_token"]
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "EURUSD", "direction": "BUY", "lots": -0.5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_trade_missing_symbol(client):
    """Symbol is required."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "trader3@velora.com",
        "password": "securepass",
    })
    token = reg.json()["access_token"]
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"direction": "BUY", "lots": 0.01},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_trade_no_mt5(client):
    """Without MT5 connected the endpoint returns 400."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "trader4@velora.com",
        "password": "securepass",
    })
    token = reg.json()["access_token"]
    resp = await client.post(
        "/api/v1/trading/execute",
        json={"symbol": "EURUSD", "direction": "BUY", "lots": 0.01},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "MT5" in resp.json()["detail"]


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
