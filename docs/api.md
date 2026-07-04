# API conventions

The FrogsWork control-plane API is served at `/api/*` behind nginx.

- **Format:** JSON request/response bodies
- **Errors:** `{ "detail": "plain-language message" }` (FastAPI default)
- **Auth:** Dashboard admin Bearer JWT (see below) — separate from SMB file user credentials
- **OpenAPI:** `/api/docs` when the API is running

## Public endpoints (no auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | `{ "status": "ok", "version": "..." }` |
| GET | `/api/setup/status` | `{ "setup_complete": bool }` |
| POST | `/api/setup` | First-run wizard (once only) |

### POST `/api/setup`

```json
{ "password": "your-admin-password", "timezone": "Australia/Sydney" }
```

Creates dashboard admin, seeds shared folders (Projects, Invoices, Shared), sets snapshot defaults.

## Auth endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | `{ "password": "..." }` → `{ "access_token", "token_type": "bearer" }` |
| POST | `/api/auth/logout` | Requires Bearer token |
| GET | `/api/auth/me` | Requires Bearer token |

Protected routes use header: `Authorization: Bearer <access_token>`

## Example flow (curl)

```bash
curl http://frogswork.local/api/setup/status
curl -X POST http://frogswork.local/api/setup \
  -H "Content-Type: application/json" \
  -d '{"password":"test-admin-pass","timezone":"UTC"}'
curl -X POST http://frogswork.local/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"test-admin-pass"}'
```
