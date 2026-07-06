import json
import urllib.request

BASE = "http://localhost"

def api(method, path, token=None, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

login = api("POST", "/api/auth/login", data={"password": "FrogsWork-Dev-2026"})
token = login["access_token"]
snaps = api("GET", "/api/snapshots", token)
print("snapshots:", [s["id"] for s in snaps])
if snaps:
    sid = snaps[0]["id"]
    browse = api("GET", f"/api/snapshots/{sid}/browse?path=", token)
    entries = browse if isinstance(browse, list) else browse.get("entries", [])
    print("browse root entries:", len(entries))
    if entries:
        print("sample:", entries[:3])
