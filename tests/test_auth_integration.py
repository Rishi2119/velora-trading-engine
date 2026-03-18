import pytest
import httpx
import time
import os

# Note: This test assumes Backend is running on 8000 and Mobile API on 5050
BACKEND_URL = "http://localhost:8000/api/v1"
MOBILE_API_URL = "http://localhost:5050/api/v1"

@pytest.fixture
def test_user():
    return {
        "email": f"test_int_{int(time.time())}@velora.com",
        "password": "securepassword123",
        "full_name": "Integration Test"
    }

@pytest.mark.asyncio
async def test_cross_service_auth_flow(test_user):
    """Verify registration in Backend -> Login in Backend -> Auth in Mobile API."""
    async with httpx.AsyncClient() as client:
        # 1. Register in Backend
        reg_resp = await client.post(f"{BACKEND_URL}/auth/register", json=test_user)
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        
        # 2. Verify with Mobile API (which should proxy to Backend)
        me_resp = await client.get(
            f"{MOBILE_API_URL}/auth/me", 
            headers={"Authorization": f"Bearer {token}"}
        )
        # If the proxy works, this should return the user profile from the backend
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == test_user["email"]
        print(f"\n[PASS] Auth Unification Verified: {test_user['email']}")

if __name__ == "__main__":
    # If run directly, try to execute the test logic
    import asyncio
    user = {
        "email": f"manual_{int(time.time())}@velora.com",
        "password": "password",
        "full_name": "Manual Proxy Test"
    }
    asyncio.run(test_cross_service_auth_flow(user))
