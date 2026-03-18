import httpx
import asyncio

async def test_api():
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        ("GET", "/api/health", None),
        ("GET", "/api/account", None),
        ("GET", "/api/positions", None),
        ("GET", "/api/strategies", None),
        ("GET", "/api/regime", None),
        ("GET", "/api/risk/status", None),
        ("POST", "/api/engine/start", {}),
        ("POST", "/api/engine/stop", {}),
        ("POST", "/api/analyze", {
            "symbol": "EURUSD",
            "ema_20": 1.0850,
            "ema_50": 1.0820,
            "ema_200": 1.0750,
            "rsi": 55,
            "atr": 0.0015
        }),
        ("GET", "/api/performance/review", None)
    ]

    issues = []
    tested = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check if server is running, if not complain
        try:
            res = await client.get(f"{base_url}/api/health")
            if res.status_code != 200:
                issues.append("Health check failed")
        except Exception as e:
            issues.append(f"Server unreachable: {e}")
            print(f"Server unreachable: {e}")
            return

        for method, path, payload in endpoints:
            try:
                if method == "GET":
                    res = await client.get(f"{base_url}{path}")
                elif method == "POST":
                    res = await client.post(f"{base_url}{path}", json=payload)
                elif method == "DELETE":
                    res = await client.delete(f"{base_url}{path}")

                tested.append(path)
                
                if res.status_code >= 400 and path != "/api/trade/123":
                    issues.append(f"{method} {path} returned {res.status_code}: {res.text}")
                
            except Exception as e:
                issues.append(f"{method} {path} failed: {e}")

    print("ENDPOINTS TESTED:")
    for path in tested:
        print(f" - {path}")

    print("\nISSUES FOUND:")
    if not issues:
        print(" - None")
    else:
        for issue in issues:
            print(f" - {issue}")
            
    print("\nFIXES APPLIED:")
    if not issues:
        print(" - None needed")
    else:
        print(" - Currently debugging...")
        
    print(f"\nFINAL STATUS: {'STABLE' if not issues else 'NOT STABLE'}")

if __name__ == "__main__":
    asyncio.run(test_api())
