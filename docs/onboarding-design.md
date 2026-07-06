# Customer onboarding design (device claim + email admin)

**Status:** Implemented in v1.0.0 (factory units require claim code; dev units skip via no `device_identity` row or `FROGSWORK_SKIP_CLAIM=1`).

Replaces password-only setup ([`SetupPage.tsx`](../dashboard/src/pages/SetupPage.tsx), [`setup/router.py`](../backend/frogswork_api/setup/router.py)).

## Goals

- Prevent a neighbour on the LAN from claiming an unconfigured box
- Store owner **email** for future password reset
- Optional backup email / phone for support
- One-time purchase — no cloud account required for daily use

## Identifiers

| Field | Example | Who sees it | Purpose |
|-------|---------|-------------|---------|
| Serial | `FW-2026-00042` | Label + support | Warranty, RMA, factory logs |
| Claim code | `FW-7K3M-9P2Q` | Card in box | One-time owner claim at setup |

Claim code is random, single-use, stored as hash in DB (like passwords). Serial is sequential or structured but not secret.

## Setup wizard (new steps)

1. Welcome — “Claim your FrogsWork box”
2. **Claim code** — enter sticker/card code
3. **Owner account** — email, password, confirm
4. **Recovery** — optional backup email, optional phone
5. **Timezone** — existing list
6. Complete → JWT → Dashboard

## Database schema (proposed)

### `device_identity`

```sql
CREATE TABLE device_identity (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    serial TEXT NOT NULL UNIQUE,
    claim_code_hash TEXT NOT NULL,
    manufactured_at TEXT NOT NULL,
    software_version TEXT NOT NULL,
    claimed_at TEXT,
    claim_attempts INTEGER NOT NULL DEFAULT 0
);
```

Factory seeds one row per unit via `factory-install.sh`.

### `dashboard_admin` (extend)

```sql
-- Add columns to existing table:
email TEXT NOT NULL UNIQUE,
backup_email TEXT,
backup_phone TEXT,
device_serial TEXT NOT NULL
```

Migration: current single-row admin becomes claimed device after upgrade path for dev units.

## API changes (proposed)

### `POST /api/setup`

```json
{
  "claim_code": "FW-7K3M-9P2Q",
  "email": "owner@example.com",
  "password": "…",
  "backup_email": "optional@example.com",
  "backup_phone": "+61…",
  "timezone": "Australia/Perth"
}
```

- Validate claim code against hash; rate-limit attempts
- On success: create admin, set `claimed_at`, invalidate claim code
- Return JWT (auto sign-in)

### `POST /api/auth/login`

```json
{ "email": "owner@example.com", "password": "…" }
```

Replaces password-only login.

### `GET /api/system/info` (extend)

Add read-only `serial` for support calls (“read the number on the back of your box”).

## Security

- Claim code: 8–12 chars, ambiguous chars avoided (no `0`/`O`)
- Max 5 failed claim attempts per hour per device
- Email stored for recovery only; no marketing without consent
- Password reset (future): magic link when internet available; offline = support + serial verification

## System page UI (future)

- Show serial (read-only)
- Show “Account email” with change flow (future)

## Dev / migration path

Existing dev NUCs with password-only admin:

1. Migration sets `device_identity` with dev serial + skips claim on next setup if `setup_complete`
2. Or one-time `FROGSWORK_SKIP_CLAIM=1` for pytest

## Implementation files (when ready)

- [`backend/frogswork_api/db.py`](../backend/frogswork_api/db.py) — schema
- [`backend/frogswork_api/setup/router.py`](../backend/frogswork_api/setup/router.py) — claim validation
- [`backend/frogswork_api/auth/router.py`](../backend/frogswork_api/auth/router.py) — email login
- [`dashboard/src/pages/SetupPage.tsx`](../dashboard/src/pages/SetupPage.tsx) — new wizard steps
- [`scripts/factory/factory-install.sh`](../scripts/factory/factory-install.sh) — seed identity
