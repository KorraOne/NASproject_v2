# Known issues and manual test checklist

Automated coverage: `backend/tests/` (pytest) and `scripts/dev/smoke-m9.sh` on the appliance.

Run this checklist on a **real NUC** after dashboard or API changes.

## P0 — must pass before shipping

| # | Flow | Steps | Pass? |
|---|------|-------|-------|
| 1 | Fresh setup | Reset DB / new unit → complete wizard → lands on Dashboard signed in | Manual (nuc1 already configured) |
| 2 | Add file user | Users → Add user → archetype assigned → appears in list | **Pass** (nuc1 smoke-m4, Jul 2026) |
| 3 | Helper + SMB | Download helper → sign in → `W:` maps → read/write team folder | **Partial** — SMB share + download OK on nuc1; Windows helper mount manual |
| 4 | Permissions | Change archetype matrix → user access updates on SMB | **Pass** (nuc1 ACL sync, Jul 2026) |
| 5 | Backup create | Backups → Create backup now → appears in list | **Pass** (nuc1 smoke-m9, Jul 2026) |
| 6 | Backup browse/restore | Browse backup → restore a test file → file appears on disk | **Partial** — browse API OK on nuc1; restore UI manual |
| 7 | Reboot survival | Reboot NUC → all services up → dashboard loads without SSH | Manual |
| 8 | Helper download | `/api/helper/download` returns 200 with exe body | **Pass** (163 MB, nuc1 Jul 2026) |

## P1 — polish / UX

| # | Flow | Notes |
|---|------|-------|
| 9 | More menu nav | Permissions, Backups, System reachable from More drawer | Deployed on nuc1 (`index-B3NdLK99.js`); browser verify |
| 10 | Delete confirms | Users, Folders, Archetypes use modal (not browser alert) | Deployed; browser verify |
| 11 | Toast feedback | Save permissions, create backup, delete user shows toast | Deployed; browser verify |
| 12 | Backups layout | Master–detail browse; close panel; `..` up navigation | Deployed; browser verify |
| 13 | Mobile width | More menu and backups layout usable below 900px | Browser verify |

## NUC automated validation (`nuc1`, Jul 2026)

Run from laptop:

```bash
scp scripts/dev/nuc-smoke-remote.sh nuc1:/tmp/
ssh nuc1 "bash /tmp/nuc-smoke-remote.sh"
```

Or on appliance: `bash /opt/frogswork/scripts/dev/smoke-m9.sh`

Dev admin password reset (smoke only): `sudo /opt/frogswork/venv/bin/python3 scripts/dev/reset-admin-pass.py FrogsWork-Dev-2026`

Results (Jul 2026): health OK, all services active, M4 user/folder smoke OK, archetypes + effective permissions OK, dashboard 200, helper download 200, snapshots create/list OK, backup browse API OK.

## Open issues (update as found)

| ID | Area | Issue | Status |
|----|------|-------|--------|
| Q1 | User quota | "Path not found: …/Personal/username" when setting max size — API user could not traverse Personal ACL | **Fixed** — quota checks use sudo `test -e` |

## Fixed in commercial polish sprint

- Cluttered 8-item top nav → Dashboard / Users / Folders / More
- Setup forced extra login → auto sign-in after wizard
- Dashboard “Create backup” misleading link → “Manage backups”
- Snapshots browse poor UX → master–detail layout with modal restore
- Native `confirm()` on deletes → shared ConfirmDialog
- Unused PermissionMatrix component removed
- User max-size quota failed on existing users → API path check now uses sudo (Personal ACL blocks `frogswork` user)
