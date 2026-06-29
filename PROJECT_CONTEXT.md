# FrogsWork File Storage — Project Context

> Handoff document for a **new, greenfield implementation** in a clean repository.  
> Developed by **KorraOne** as part of the **FrogsWork** product suite (alongside products such as FrogsWork Invoicer).  
> This describes **what to build and why** — not how to build it. See [`docs/development-behaviour.md`](docs/development-behaviour.md) and the implementation plan for how to build it.  
> **Hardware is fixed** (procurement complete). Software choices may evolve.

---

## What this is

**FrogsWork File Storage** is a plug-and-play file-sharing appliance for small businesses. A business buys a small box, plugs it into their network, runs a short setup wizard, and their staff can access shared files through **Windows Explorer** like any normal network drive — no IT knowledge required.

**Business model:** One-time hardware purchase (no subscription for core features). Remote access over the internet may be a paid add-on later.

---

## Who uses it

### Business owner (dashboard admin)

The shop owner or office manager. They use a **web dashboard** in a browser to:

- Complete first-time setup
- Create and remove **file user** accounts (employees, and optionally themselves)
- Create shared folders (e.g. "Projects", "Invoices")
- Control who can read or edit each folder
- Set per-user storage limits on private folders
- Grant **super-user** access when someone needs to view all staff private folders
- See how much storage is used
- Manage backups (snapshots) and restore files if someone deletes something by mistake
- View basic device health (disk space, uptime, network)
- Enable remote SSH temporarily for support (off by default)

The dashboard admin account is **separate from file users**. The owner does **not** get a network drive automatically — if they want files on the appliance, they create a file user account for themselves (like any employee) and use the helper app.

They are the only person who interacts with the appliance directly via the web.

### Employees (file users)

Regular office workers on **Windows PCs** (Mac support is a future nice-to-have, not v1). They:

- Never log into the dashboard
- Never SSH or touch Linux
- Use files through **File Explorer** on mapped network drives
- Install a small **helper app** that finds the appliance on the network, logs them in once, and maps their drives automatically

Each file user gets:

- A **private folder** (visible only to them, plus super-users) — default drive letter `U:`
- Access to **shared folders** they are assigned (read-only or read-write) — default drive letters `S:`, `T:`, etc.

The experience should feel like the company has an internal file server — open Explorer, open a mapped drive, edit documents.

---

## Core product principles

1. **Zero-setup for employees** — owner configures; staff just get drives
2. **Works offline on the LAN** — no cloud dependency for daily file access
3. **Protect against human error** — snapshots let you recover deleted or overwritten files same-day
4. **Quiet, low-power hardware** — sits in a cupboard, runs 24/7
5. **One-time purchase** — appeal to subscription-fatigued small businesses
6. **Owner doesn't need to understand NAS/Linux** — dashboard speaks plain business language

---

## High-level features

### Appliance (the box)

- Runs headless on the network (no monitor needed after initial install)
- Hostname discoverable as `frogswork.local` on the local network
- Serves files via **SMB** (Windows-compatible network sharing)
- Stores all data on a dedicated storage volume with **snapshot-based protection** (not RAID mirroring)
- Automatically takes scheduled snapshots (default: nightly at 02:00) so the owner can roll back
- Survives reboots — all services start automatically
- Serves the admin dashboard and helper app download over HTTP (port 80)

### Admin dashboard (web)

- First-run **setup wizard** (set dashboard admin password, timezone; seeds default shared folders)
- **User management** — add/remove file users, reset passwords, set storage quotas, super-user toggle
- **Folder management** — create shared folders, assign per-user read-only or read-write access
- **Storage overview** — how full the disk is
- **Snapshot management** — view snapshots, create manual snapshot, restore, configure schedule and retention
- **System page** — network info, disk health, remote SSH toggle (default off), reboot/shutdown
- Download link for the Windows helper app

**Default shared folders** created at setup (no permissions until assigned):

| Folder | Purpose |
|--------|---------|
| **Projects** | Active job / client work |
| **Invoices** | Billing documents (complements FrogsWork Invoicer) |
| **Shared** | General company-wide files |

### Helper app (Windows)

- Discovers the appliance on the local network (no IP address typing)
- File user logs in with their username/password
- Maps the correct network drives (private folder + shared folders they have access to)
- Default drive letters: `U:` for private folder, `S:`/`T:`/… for shared folders; user can choose alternates if letters are taken
- Runs in the system tray; reconnects after reboot if needed
- Distributed from the appliance itself (download from the dashboard or a direct URL)
- Unsigned for v1 (SmartScreen warning acceptable during development and early deployment)

### Data protection philosophy

The main risk for small businesses is **accidental deletion, bad edits, or ransomware** — not sudden drive failure. Protection strategy:

- **Scheduled snapshots** of all business data (default: nightly at 02:00)
- Owner can restore files or folders from a snapshot via the dashboard
- **Default retention:** 7 daily, 4 weekly, 3 monthly — configurable in dashboard
- Single internal drive on v1 hardware; snapshots live on the same volume (space-efficient with copy-on-write filesystem)

RAID mirroring is explicitly **not** the approach.

---

## Physical hardware (locked — do not change)

Procurement is complete. All software must target this exact hardware.

| Component | Detail |
|-----------|--------|
| **Device** | Asus NUC 14 Essential barebone (`RNUC14MNK9700000`) |
| **CPU** | Intel N97, 4 cores, ~12W — fan-cooled mini PC |
| **RAM** | 8GB DDR5-4800 (single SO-DIMM slot, max 16GB) |
| **Storage** | 480GB Crucial NVMe M.2 2280 (only **one** M.2 slot) |
| **Network** | 2.5 Gigabit Ethernet (primary); Wi-Fi present but not used in production |
| **Power** | 65W adapter + AU mains cable (IEC C5) |
| **Size** | ~135 × 115 × 36 mm — desk/shelf appliance |

**Storage layout intent:** Ubuntu OS on a small partition (~32GB); remainder (~440GB) as a dedicated btrfs data volume for business files and snapshots. Do not wipe the whole disk when setting up data storage.

---

## Conceptual architecture

```
┌─────────────────────────────────────────────────────────┐
│  Asus NUC (Ubuntu Server)                               │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐   │
│  │ Web UI   │  │ API      │  │ File sharing (SMB)  │   │
│  │ dashboard│  │ backend  │  │ Samba               │   │
│  └────┬─────┘  └────┬─────┘  └──────────┬──────────┘   │
│       │             │                    │              │
│       └─────────────┴────────────────────┘              │
│                         │                               │
│              ┌──────────▼──────────┐                    │
│              │  /data  (btrfs)     │                    │
│              │  users + shared     │                    │
│              │  + snapshots        │                    │
│              └─────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
          │ SMB (445)              │ HTTP (80)
          ▼                        ▼
   Windows Explorer          Owner's browser
   + Helper app              (dashboard)
```

**Separation of concerns:** The API/dashboard manages users, permissions, and snapshots. The file-sharing layer (Samba) enforces access on the actual files. Changes in the dashboard must sync to real filesystem permissions.

**Identity model:** Dashboard admin (web only) and file users (SMB) are separate. File users have private folders under `/data/users/` and shared folder access under `/data/shared/`. Super-users can read all private folders.

---

## Typical user journeys

### Owner — day one

1. Unbox, plug in Ethernet and power
2. Open `http://frogswork.local` on their laptop
3. Setup wizard: choose dashboard admin password, timezone
4. Create file user accounts for staff; assign shared folder permissions
5. Optionally create a file user for themselves and enable super-user if they need oversight
6. Tell staff to download the helper app and log in

### Employee — day one

1. Install helper app (link from owner or from appliance website)
2. App finds the box, employee enters username/password
3. Drives appear in Explorer — work as normal

### Owner — someone deleted the wrong folder

1. Open dashboard → Snapshots
2. Pick last night's snapshot → restore the folder
3. Files reappear for staff on their mapped drives

---

## Development approach

| Where | Role |
|-------|------|
| **Windows laptop** | Cursor IDE, git, building the helper app, optional Remote-SSH to the NUC |
| **Asus NUC** | Real appliance environment — Ubuntu Server, SSH access, integration testing with actual SMB and snapshots |
| **Windows client PC** | Test Explorer access and helper app on the LAN |

The NUC does **not** run Cursor or an AI agent. Development on the appliance happens via **SSH from the laptop** (Cursor Remote-SSH), or by deploying builds from the laptop and testing manually.

**Goal:** Develop and test in the real Linux/Samba/btrfs environment, not a simulated one.

**Replication:** Manual Ubuntu Server install per unit, then scripted provisioning. The same install process used on the first NUC must work identically on every subsequent unit manufactured (scripted, repeatable, versioned releases).

**Approved v1 stack:** Python/FastAPI backend, React dashboard, C#/.NET 8 Windows helper, nginx, Samba, btrfs, systemd, SQLite.

---

## Legacy prototype (optional reference only)

An earlier proof-of-concept exists (`NASproject` on the developer's machine). It explored:

- FastAPI backend + SvelteKit dashboard + C# helper app
- Mock development mode on Windows
- Rough install scripts

**The new project should not build on that codebase.** It may be consulted for UX ideas or lessons learned only. The new agent plans and implements from scratch against this document.

---

## Out of scope for v1

- Cloud sync or off-site backup (snapshots are local only unless owner adds USB drive later)
- Mac helper app (manual SMB mount is acceptable short-term)
- Running the NAS software on Windows instead of the dedicated appliance
- Docker/containerized deployment
- RAID / dual-drive mirroring
- Remote access over the internet / VPN (future paid feature)
- Mobile apps
- Active Directory / domain integration
- HTTPS on the LAN (HTTP only on port 80 for v1)
- Code-signed helper app installer (unsigned acceptable for v1)

---

## Definition of done (v1)

The product is ready when:

1. A fresh NUC can be installed from scratch using documented steps and install scripts
2. Owner completes setup wizard and manages users/folders from the dashboard
3. Windows employee can use the helper app to mount drives and read/write files in Explorer
4. Nightly snapshots run automatically; owner can restore from the dashboard
5. Appliance survives reboot with no manual intervention
6. A second identical NUC can be built by repeating the same install process

---

## Instructions for the implementing agent

1. **Read this document** to understand the product intent.
2. **Read the implementation plan and development behaviour guide** for architecture, milestones, and workflow.
3. **Target the locked hardware** in Section "Physical hardware" — do not suggest alternatives.
4. **Build greenfield** — do not inherit the legacy prototype as a codebase dependency.
5. **Prioritize the owner and employee journeys** over internal engineering elegance.
6. Ask the user clarifying questions before committing to major architectural forks.
