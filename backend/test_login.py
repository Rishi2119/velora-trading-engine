import httpx
import asyncio

async def main():
    try:
        async with httpx.AsyncClient() as client:
            print("1. Checking health...")
            r = await client.get("http://127.0.0.1:5050/health")
            print(r.status_code, r.text)

            print("2. Registering...")
            r = await client.post("http://127.0.0.1:5050/api/v1/auth/register", json={
                "email": "tester@test.com", "password": "password123", "full_name": "Test User"
            })
            print(r.status_code, r.text)
            
            print("3. Logging in...")
            r = await client.post("http://127.0.0.1:5050/api/v1/auth/login", json={
                "email": "tester@test.com", "password": "password123"
            })
            print(r.status_code, r.text)

            if r.status_code == 200:
                token = r.json().get("access_token")
                print("4. Testing protected endpoint...")
                r2 = await client.get("http://127.0.0.1:5050/api/v1/trading/stats", headers={"Authorization": f"Bearer {token}"})
                print(r2.status_code, r2.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
