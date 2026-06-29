# Manufacturing install

Step-by-step provisioning for a fresh Asus NUC. **Implemented in M1** (requires Ubuntu Server 24.04 on the appliance).

## Prerequisites

- Asus NUC 14 Essential with 480 GB NVMe
- Ethernet connection to the LAN
- Windows laptop with git and SSH client

## Overview (M1+)

1. Manually install **Ubuntu Server 24.04 LTS** (UEFI, OpenSSH server enabled).
2. Set hostname: `sudo hostnamectl set-hostname frogswork`
3. Clone this repository at a release tag.
4. Run install scripts in order:
   - `sudo scripts/install/00-prereqs.sh`
   - `sudo scripts/install/01-partition.sh`
   - `sudo scripts/install/02-deploy-app.sh`
   - `sudo scripts/install/03-enable-services.sh`
5. Smoke test: `curl http://frogswork.local/api/health`

Full checklist and SSH hardening notes will be added when M1 is complete.
