"""
Velora Backend — API Tests
Run with: cd trading_engins && python -m pytest backend/tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

# Use in-memory SQLite for tests
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


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
