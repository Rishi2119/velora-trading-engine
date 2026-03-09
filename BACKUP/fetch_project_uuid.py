"""
Fetch the real Expo project UUID for @rishi_2119/velora using the GraphQL API,
then patch app.json with the correct projectId.
"""
import json, urllib.request, os

SESSION_SECRET = '{"id":"2b61a157-fb55-499d-8941-17ea4b2689d8","version":1,"expires_at":2087510400000}'
APP_JSON_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_app", "app.json")

QUERY = """
query GetProject($accountName: String!, $slug: String!) {
  project {
    byAccountNameAndSlug(accountName: $accountName, slug: $slug) {
      id
      name
      slug
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"accountName": "rishi_2119", "slug": "velora"}
}).encode()

req = urllib.request.Request(
    "https://api.expo.dev/graphql",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "expo-session": SESSION_SECRET,
    }
)

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    project = data.get("data", {}).get("project", {}).get("byAccountNameAndSlug")
    if project:
        uuid = project["id"]
        print(f"[OK] Found project UUID: {uuid}")
        # Patch app.json
        with open(APP_JSON_PATH) as f:
            app = json.load(f)
        app["expo"]["extra"] = {"eas": {"projectId": uuid}}
        with open(APP_JSON_PATH, "w") as f:
            json.dump(app, f, indent=2)
        print(f"[OK] app.json updated with projectId: {uuid}")
    else:
        print("[ERR] Project not found in API response.")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"[ERR] {e}")
