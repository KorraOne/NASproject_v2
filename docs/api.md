# API conventions

The FrogsWork control-plane API is served at `/api/*` behind nginx.

- **Format:** JSON request/response bodies
- **Errors:** `{ "detail": "plain-language message" }` (FastAPI default)
- **Auth:** Dashboard admin session/JWT (M2+) — separate from SMB file user credentials
- **OpenAPI:** Available at `/api/docs` when the API is running (FastAPI auto-docs)

Endpoint reference will be documented here as routes land in M2–M7.
