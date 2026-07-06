import json
import urllib.request

req = urllib.request.Request(
    "http://localhost/api/auth/login",
    data=json.dumps({"password": "FrogsWork-Dev-2026"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
token = json.load(urllib.request.urlopen(req))["access_token"]
req2 = urllib.request.Request(
    "http://localhost/api/folders",
    headers={"Authorization": f"Bearer {token}"},
)
folders = json.load(urllib.request.urlopen(req2))
print("folders:", [f["name"] for f in folders])
req3 = urllib.request.Request(
    "http://localhost/api/users",
    headers={"Authorization": f"Bearer {token}"},
)
users = json.load(urllib.request.urlopen(req3))
print("users:", [u["username"] for u in users])
