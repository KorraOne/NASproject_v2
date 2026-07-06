# Post-v1 commercial roadmap

Features deferred after v1.0.0. Not required for first hand-sold unit; plan before scale.

## 4.1 Code-signed helper installer

**Why:** Reduces Windows SmartScreen warnings and support calls.

**Approach:**

- Obtain code signing certificate (self-signed for dev; EV/OV cert for commercial)
- Sign `FrogsWork.Helper.exe` in CI after `dotnet publish`
- Optional: wrap in MSI with signed installer

**Status:** Deferred — unsigned helper acceptable for v1 per PROJECT_CONTEXT.

---

## 4.2 In-place software updates

**Why:** Patch security and bugs without manual SSH.

**Approach:**

- Dashboard **System → Updates** page
- Download tagged tarball from KorraOne or apply USB update package
- `scripts/install/02-deploy-app.sh` in upgrade mode (preserve `/data` and SQLite)
- Version check API + release notes

**Status:** Backlog — see [dashboard-post-v1-backlog.md](dashboard-post-v1-backlog.md).

---

## 4.3 Factory reset

**Why:** RMA refurbish and customer handoff.

**Approach:**

- Dashboard destructive action with typed confirmation
- Wipe SQLite, `/data` business files (optional keep snapshots policy)
- Reset `device_identity.claimed_at` only via factory reflash
- Return to setup wizard

**Status:** Backlog.

---

## 4.4 Email password reset

**Why:** Owner forgets dashboard password.

**Depends on:** Claim/onboarding email (implemented in v1.0.0 for factory units).

**Approach:**

- Magic link when appliance has internet (optional cloud relay)
- Offline: support verifies serial + purchase, issues one-time recovery code

**Status:** Design after first retail sales volume.

---

## 4.5 Remote VPN add-on (paid)

**Why:** Staff access files off-LAN.

**Approach:** LAN pairing + WireGuard or KorraOne relay. See reviewer architecture notes.

**Status:** Out of v1 scope; separate product track.

---

## 4.6 HTTPS on LAN

**Why:** Encrypt dashboard credentials on untrusted LANs.

**Approach:** Local CA or manual cert upload; nginx TLS termination.

**Status:** Out of v1 scope per PROJECT_CONTEXT.
