import urllib.request, json, time

def test():
    print("--- 1. Getting Initial Agent Status ---")
    try:
        r = urllib.request.urlopen("http://localhost:5050/api/agent/status")
        print(json.loads(r.read()))
    except Exception as e:
        print(e)
        
    print("\n--- 2. Starting Agent ---")
    try:
        req = urllib.request.Request("http://localhost:5050/api/agent/start", method="POST")
        r = urllib.request.urlopen(req)
        print(json.loads(r.read()))
    except Exception as e:
        print(e)
        
    print("\n--- 3. Waiting 3 seconds for loop to tick ---")
    time.sleep(3)
    
    print("\n--- 4. Polling Agent Status (should have thoughts) ---")
    try:
        r = urllib.request.urlopen("http://localhost:5050/api/agent/status")
        print(json.dumps(json.loads(r.read()), indent=2))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test()
