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

## File users (dashboard admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users` | List file users |
| POST | `/api/users` | Create file user + Linux/Samba sync |
| GET | `/api/users/{id}` | Get file user |
| PATCH | `/api/users/{id}` | Update display name, password, super-user, quota, folder permissions |
| DELETE | `/api/users/{id}` | Delete file user + system cleanup |

### POST `/api/users`

```json
{
  "username": "alice",
  "display_name": "Alice",
  "password": "employee-pass",
  "is_superuser": false,
  "quota_bytes": null
}
```

Usernames: 3–32 chars, lowercase letter first, letters/digits/underscore. Creates `/data/users/{username}` (btrfs subvolume), Linux account, and Samba password. Super-users join `frogswork-superuser` (read-only on others' private folders).

### PATCH `/api/users/{id}` — folder permissions (optional)

```json
{
  "folder_permissions": [
    { "folder_id": 1, "access": "read" },
    { "folder_id": 2, "access": "read_write" }
  ]
}
```

Replaces all folder permissions for that user. Access is `read` or `read_write`.

## Shared folders (dashboard admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/folders` | List shared folders with permission summary |
| POST | `/api/folders` | Create folder on disk + Samba fragment |
| GET | `/api/folders/{id}` | Get folder |
| PATCH | `/api/folders/{id}` | Rename folder |
| DELETE | `/api/folders/{id}` | Delete empty folder |
| PUT | `/api/folders/{id}/permissions` | Replace permission matrix for folder |

SMB share names follow `shared-{FolderName}` (e.g. `\\frogswork.local\shared-Projects`). Permissions sync to POSIX ACLs (`read` → `r-x`, `read_write` → `rwx`) and Samba `valid users`.

### PUT `/api/folders/{id}/permissions`

```json
{
  "permissions": [
    { "user_id": 1, "access": "read" },
    { "user_id": 2, "access": "read_write" }
  ]
}
```

Returns the updated permission list with usernames.

## Storage (dashboard admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/storage` | Data volume usage + counts |

### GET `/api/storage`

```json
{
  "mount": "/data",
  "total_bytes": 330000000000,
  "used_bytes": 1200000000,
  "free_bytes": 328800000000,
  "file_user_count": 2,
  "shared_folder_count": 3
}
```

## Snapshots (dashboard admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/snapshots` | List snapshots |
| POST | `/api/snapshots` | Create manual daily snapshot |
| GET | `/api/snapshots/settings` | Schedule hour + retention counts |
| PATCH | `/api/snapshots/settings` | Update schedule/retention |
| GET | `/api/snapshots/{id}/browse` | List files/folders inside snapshot |
| GET | `/api/snapshots/{id}/restore-token` | Get confirmation token for restore |
| POST | `/api/snapshots/{id}/restore` | Restore file or folder path |

Restore requires the `confirm_token` from the restore-token endpoint (prevents accidental overwrites).

## System (dashboard admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/info` | Hostname, IPs, uptime, disk usage, version |
| GET | `/api/system/ssh` | Remote SSH enabled state |
| POST | `/api/system/ssh` | `{ "enabled": true \| false }` |
| POST | `/api/system/reboot` | `{ "confirm": true }` |
| POST | `/api/system/shutdown` | `{ "confirm": true }` |

Remote SSH is **off by default** on new setups (`AllowUsers` drop-in). Upgraded appliances keep existing SSH until toggled in the dashboard.

## Helper (Windows app + file users)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/helper/mounts` | Drive list for signed-in file user (HTTP Basic auth) |
| GET | `/api/helper/download` | Download `FrogsWork.Helper.exe` |

### GET `/api/helper/mounts`

Authenticate with file user credentials (`Authorization: Basic …`). Returns private home (`U:`) and shared folders (`S:`, `T:`, …) with UNC paths and suggested drive letters.

Build the helper on Windows: `scripts/dev/build-helper.sh --deploy`

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
