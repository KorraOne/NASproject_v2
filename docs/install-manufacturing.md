# Manufacturing install

Step-by-step provisioning for a fresh Asus NUC. Tested on **Ubuntu Server 26.04 LTS** with the default LVM installer layout.

## Prerequisites

- Asus NUC 14 Essential with 480 GB NVMe
- Network connection (Wi-Fi OK for dev; Ethernet for production)
- Windows laptop with OpenSSH client (`ssh`, `scp`)
- SSH access to the NUC (e.g. `ssh nuc1` with key auth)
- Passwordless sudo for the deploy user on the NUC

## 1. Base Ubuntu install

1. Install **Ubuntu Server 26.04 LTS** (UEFI, default partitioning with LVM — no custom layout required).
2. Enable **OpenSSH server** during install.
3. Create admin user (e.g. `korra`) with sudo.
4. Set hostname:
   ```bash
   sudo hostnamectl set-hostname frogswork
   ```
5. Passwordless sudo (one-time):
   ```bash
   echo 'korra ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/korra
   ```

## 2. Deploy FrogsWork from dev laptop

Copy the repo to `/opt/frogswork` on the NUC, then run install:

```bash
# From laptop (Git Bash or WSL if using sync.sh)
FROGSWORK_HOST=nuc1 bash scripts/dev/sync.sh

# First-time full install on NUC (if not using sync deploy step):
ssh nuc1
sudo bash /opt/frogswork/scripts/install/install.sh
```

Install script order:

| Script | Purpose |
|--------|---------|
| `00-prereqs.sh` | apt packages (Python, nginx, Samba, btrfs, Avahi, Node) |
| `01-partition.sh` | LVM LV `frogswork-data` + btrfs `/data` |
| `02-deploy-app.sh` | venv, dashboard build, nginx/systemd/avahi |
| `03-enable-services.sh` | Enable and start services |

## 3. Smoke test checklist

```bash
curl -s http://localhost/api/health
# {"status":"ok","version":"0.0.0-dev"}

systemctl is-active frogswork-api nginx avahi-daemon smbd
df -h /data
testparm -s
```

From laptop on LAN:

```bash
curl http://<nuc-ip>/api/health
# Browser: http://frogswork.local or http://<nuc-ip>
```

## 4. Development deploy loop

After code changes:

```bash
FROGSWORK_HOST=nuc1 bash scripts/dev/sync.sh
```

On Windows without rsync, `sync.sh` falls back to **tar over SSH**.

Step-by-step guide: [`dev-steps/M1.md`](dev-steps/M1.md).
