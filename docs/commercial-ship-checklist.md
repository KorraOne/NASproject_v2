# Commercial ship checklist

Ship/no-ship criteria for FrogsWork File Storage v1. See also [factory-deploy.md](factory-deploy.md) and [customer-quick-start.md](customer-quick-start.md).

## Path A — First hand-sold unit

### Release integrity

- [ ] **A1** Working tree clean; ship candidate matches tagged commit
- [ ] **A2** `VERSION` is `1.0.0` and git tag `v1.0.0` exists
- [ ] **A3** `pytest` passes on laptop from tagged commit
- [ ] **A4** Dashboard `npm run build` succeeds
- [ ] **A5** Helper exe matches `/api/helper/download` on appliance

### Fresh install (no dev shortcuts)

- [ ] **A6** Ubuntu Server 26.04 LTS (24.04 also supported) — document which
- [ ] **A7** Install via `scripts/install/install.sh` only (not `sync.sh`)
- [ ] **A8** No passwordless sudo for dev deploy user on shipped unit
- [ ] **A9** `/opt/frogswork` owned by root in production (`FROGSWORK_PRODUCTION=1`)
- [ ] **A10** Remote SSH off after setup (System page)

### Owner journey

- [ ] **A11** `http://frogswork.local` loads without SSH
- [ ] **A12** Fresh setup wizard on clean unit
- [ ] **A13** Auto-signed in after wizard
- [ ] **A14–A19** Users, folders, storage, backups, system page

### Employee journey (Windows)

- [ ] **A20–A24** Helper download, connect, `W:` drive, read/write, permissions
- [ ] **A25** SmartScreen warning documented for customer

### Reliability

- [ ] **A26** `scripts/dev/smoke-m9.sh` passes
- [ ] **A27** Reboot survival — services auto-start
- [ ] **A28** Nightly snapshot timer enabled

### Customer docs

- [ ] **A30–A32** Quick start, support contact, known limitations

**SHIP (hand-sold):** A1–A28 pass; A30–A32 complete.

---

## Path B — First factory batch

All Path A items **plus**:

- [ ] **B1–B3** Release tarball + SHA256; factory needs no git/Node/.NET
- [ ] **B4–B13** `factory-install.sh`, claim codes, burn-in hard-fail, second unit
- [ ] **B14–B19** Retail kit + WiFi USB E2E
- [ ] **B20–B23** Unit registry, warranty/RMA, third-party install test

**SHIP (factory):** Path A + all B items.

Automated partial check on NUC: `bash scripts/dev/run-p0-checklist.sh`
