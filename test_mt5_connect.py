"""Test the /api/mt5/connect endpoint directly."""
import urllib.request, json

url = "http://192.168.1.5:5050/api/mt5/connect"
payload = json.dumps({
    "account": "10009823282",
    "password": "TestPassword123",
    "server": "MetaQuotes-Demo",
}).encode()

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f"Status: {r.status}")
        data = json.loads(r.read())
        print(f"Response: {json.dumps(data, indent=2)}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Body: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
