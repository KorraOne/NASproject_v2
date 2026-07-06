# Architecture

FrogsWork File Storage runs on an **Asus NUC 14 Essential** with **Ubuntu Server 26.04 LTS** (26.x tested; 24.04 also supported).

## Components

| Component | Technology | Role |
|-----------|------------|------|
| Dashboard | React + Vite | Owner admin UI (static files) |
| API | Python FastAPI | Users, folders, snapshots, system control |
| Metadata | SQLite | Dashboard admin, permissions matrix, policies (M2+) |
| Proxy | nginx | HTTP :80, `/api/*` → FastAPI on `127.0.0.1:8000` |
| Files | Samba | SMB file access for Windows clients |
| Storage | btrfs on `/data` | User private folders, shared folders, snapshots |
| Discovery | Avahi | `frogswork.local`, helper mDNS |
| Helper | C# .NET 8 WPF | Windows drive mapping (M8) |

## Disk layout (Ubuntu default LVM installer)

| Volume | Size | FS | Mount | Purpose |
|--------|------|-----|-------|---------|
| `ubuntu-lv` | ~100 GB | ext4 | `/` | Ubuntu OS, packages, `/opt/frogswork` |
| `frogswork-data` LV | ~90% of VG free | btrfs | `/data` | Business files + snapshots |

The installer uses LVM on `nvme0n1p3`. M1 creates logical volume `ubuntu-vg/frogswork-data` from free space — **no repartitioning**.

## Data paths

```
/data/frogswork/            Unified SMB share root (ACL-controlled)
  Projects/                 Team folders (admin-created)
  Invoices/
  Personal/                 Private homes container (traverse-only for members)
    {username}/             One private folder per file user
/data/.snapshots/           Readonly btrfs snapshots (M6+)
/var/lib/frogswork/         SQLite DB, setup flag, helper cache
/opt/frogswork/             Application install root
```

Windows clients map a single drive (`W:`) to `\\frogswork\frogswork`. Team folders and `Personal\{username}` appear based on POSIX ACLs. Samba `hide unreadable = yes` filters Explorer listings so users do not see folders they cannot read.

## systemd services

| Unit | Purpose |
|------|---------|
| `frogswork-api.service` | FastAPI via uvicorn |
| `nginx.service` | Static dashboard + API proxy |
| `smbd` / `nmbd` | SMB file sharing |
| `avahi-daemon.service` | mDNS (`frogswork.local`) |
| `frogswork-snapshot.timer` | Nightly snapshots (M6+) |

## Network (development)

Wi-Fi is acceptable for development. Production units should use Ethernet (`enp1s0`). Appliance hostname: **`frogswork`**.
