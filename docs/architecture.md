# Architecture

FrogsWork File Storage runs on an **Asus NUC 14 Essential** with **Ubuntu Server 24.04 LTS**.

## Components

| Component | Technology | Role |
|-----------|------------|------|
| Dashboard | React + Vite | Owner admin UI (static files) |
| API | Python FastAPI | Users, folders, snapshots, system control |
| Metadata | SQLite | Dashboard admin, permissions matrix, policies |
| Proxy | nginx | HTTP :80, `/api/*` → FastAPI Unix socket |
| Files | Samba | SMB file access for Windows clients |
| Storage | btrfs on `/data` | User private folders, shared folders, snapshots |
| Discovery | Avahi | `frogswork.local`, helper mDNS |
| Helper | C# .NET 8 WPF | Windows drive mapping |

Detailed diagrams and partition layout are in the implementation plan (`.cursor/plans/frogswork_file_storage_d3d107e4.plan.md`). This document will expand in **M1** after provisioning is implemented on hardware.

## Data paths

```
/data/users/{username}/     Private folder per file user
/data/shared/{folder}/      Shared business folders
/data/.snapshots/           Readonly btrfs snapshots
/var/lib/frogswork/         SQLite DB, setup flag, helper MSI cache
```
