# FrogsWork File Storage

Plug-and-play SMB file-sharing appliance for small businesses — part of the **FrogsWork** suite by **KorraOne**.

A business buys a pre-configured Asus NUC, plugs it into their network, and manages shared files, users, and snapshots from a web dashboard at `http://frogswork.local`. Staff on Windows PCs use a helper app to map network drives in File Explorer.

## Documentation

| Document | Purpose |
|----------|---------|
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Product vision — what to build and why |
| [`docs/development-behaviour.md`](docs/development-behaviour.md) | How to develop — workflow, git, testing, deployment |
| [`docs/dev-steps/README.md`](docs/dev-steps/README.md) | **Per-milestone implementation guides** (M0–M9) |
| [`docs/architecture.md`](docs/architecture.md) | System components and data paths |
| [`docs/install-manufacturing.md`](docs/install-manufacturing.md) | NUC provisioning (M1+) |
| [`docs/api.md`](docs/api.md) | API conventions and endpoint reference |

## Repository layout

```
backend/          Python FastAPI control plane
dashboard/        React owner dashboard
helper/           C# Windows tray app
scripts/          Install, btrfs, dev sync scripts
deploy/           nginx, systemd, avahi templates
docs/             Architecture, manufacturing, API notes
VERSION           Release version (currently 0.0.0-dev)
```

## Status

**M1 (provisioning)** — complete on NUC `nuc1`. Health: `http://192.168.0.232/api/health`

**M2** — setup wizard and SQLite. Guide: [`docs/dev-steps/M2.md`](docs/dev-steps/M2.md).

## Dev prerequisites (Windows laptop)

| Tool | Purpose |
|------|---------|
| Python 3.12+ | Backend lint/tests |
| Node.js 20+ | Dashboard build |
| .NET 8 SDK | Helper app build |
| git | Version control |

### Quick checks

```bash
# Backend unit tests (from backend/)
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\pytest

# Dashboard (from dashboard/)
npm install
npm run build

# Helper (from helper/FrogsWork.Helper/)
dotnet build
```

## Hardware

Asus NUC 14 Essential, Ubuntu Server 24.04 LTS, single 480 GB NVMe (OS + btrfs data volume).
