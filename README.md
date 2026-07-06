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
| [`docs/hand-built-first-unit.md`](docs/hand-built-first-unit.md) | **First hand-built unit** — serial, setup code, WiFi USB |
| [`docs/install-manufacturing.md`](docs/install-manufacturing.md) | NUC provisioning and smoke tests |
| [`docs/commercial-ship-checklist.md`](docs/commercial-ship-checklist.md) | Ship/no-ship criteria (hand-sold and factory) |
| [`docs/customer-quick-start.md`](docs/customer-quick-start.md) | Owner quick-start (print with unit) |
| [`docs/factory-deploy.md`](docs/factory-deploy.md) | Factory line and release tarball |
| [`docs/warranty-rma.md`](docs/warranty-rma.md) | Warranty and returns |
| [`docs/api.md`](docs/api.md) | API conventions and endpoint reference |

## Repository layout

```
backend/          Python FastAPI control plane
dashboard/        React owner dashboard
helper/           C# Windows tray app
scripts/          Install, btrfs, dev sync scripts
deploy/           nginx, systemd, avahi templates
docs/             Architecture, manufacturing, API notes
VERSION           Release version (currently 1.0.0)
```

## Status

**v1.0.0** — feature complete. Ship criteria: [`docs/commercial-ship-checklist.md`](docs/commercial-ship-checklist.md).

Milestones M0–M9: [`docs/dev-steps/README.md`](docs/dev-steps/README.md).

### Release tag

```bash
git tag -a v1.0.0 -m "FrogsWork File Storage v1.0.0"
```

Factory release tarball: `bash scripts/release/build-tarball.sh`

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

Asus NUC 14 Essential, Ubuntu Server 26.04 LTS (24.04 also supported), single 480 GB NVMe (OS + btrfs data volume).
