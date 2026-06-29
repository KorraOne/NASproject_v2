# FrogsWork File Storage

Plug-and-play SMB file-sharing appliance for small businesses — part of the **FrogsWork** suite by **KorraOne**.

A business buys a pre-configured Asus NUC, plugs it into their network, and manages shared files, users, and snapshots from a web dashboard at `http://frogswork.local`. Staff on Windows PCs use a helper app to map network drives in File Explorer.

## Documentation

| Document | Purpose |
|----------|---------|
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Product vision — what to build and why |
| [`docs/development-behaviour.md`](docs/development-behaviour.md) | How to develop — workflow, git, testing, deployment |
| [Implementation plan](.cursor/plans/frogswork_file_storage_d3d107e4.plan.md) | Architecture, tech stack, milestones M0–M9 |

## Status

Greenfield implementation in progress. See the implementation plan for the current milestone.

## Hardware

Asus NUC 14 Essential, Ubuntu Server 24.04 LTS, single 480 GB NVMe (OS + btrfs data volume).
