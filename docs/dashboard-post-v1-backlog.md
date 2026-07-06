# Dashboard post-v1 backlog

Features intentionally deferred from the v1 dashboard scope. Keep these out of navigation until implemented.

## Users

| Feature | Description |
|---------|-------------|
| Pause user | Disable Samba login without deleting the account or personal folder |

## Folders

| Feature | Description |
|---------|-------------|
| Temporary lock | Read-only freeze on a shared folder (ACL + deny write) |

## Storage

| Feature | Description |
|---------|-------------|
| Per-folder usage metering | Show actual bytes used per shared folder, not just quota caps |
| Backup storage breakdown | Disk used by btrfs snapshots on the Storage page |
| Export to external backup | Copy archives to USB or network destination |
| Import from external backup | Restore from off-appliance backup media |

## Dashboard

| Feature | Description |
|---------|-------------|
| Recent activity | Audit log of user/folder/permission changes |
| Alerts API | Dedicated health metrics beyond disk usage and snapshot age |

## System

| Feature | Description |
|---------|-------------|
| Logs viewer | Browse API and service logs from the dashboard |
| Version & updates | In-place software update mechanism |
| Factory reset | Wipe data and return to setup wizard (destructive) |

## Snapshots

| Feature | Description |
|---------|-------------|
| Backup destinations | Off-site or secondary backup targets beyond local btrfs |
