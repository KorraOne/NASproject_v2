# Manufacturing install

Step-by-step provisioning for a fresh Asus NUC. Tested on **Ubuntu Server 26.04 LTS** (24.04 LTS also supported) with the default LVM installer layout.

## Prerequisites

- Asus NUC 14 Essential with 480 GB NVMe
- Network connection (Ethernet for production; Wi-Fi OK for dev)
- Windows laptop with OpenSSH client (`ssh`, `scp`)

## 1. Base Ubuntu install

1. Install **Ubuntu Server 26.04 LTS** (UEFI, default partitioning with LVM).
2. Enable **OpenSSH server** during install.
3. Create admin user (e.g. `korra`) with sudo — **dev only**; factory images remove passwordless sudo.
4. Set hostname:
   ```bash
   sudo hostnamectl set-hostname frogswork
   ```

## 2. Production install (ship candidate)

Use a **release tarball** (no git/Node on the NUC):

```bash
# On laptop: build tarball
bash scripts/release/build-tarball.sh

# Copy to NUC
scp dist/frogswork-v1.0.0.tar.gz nuc:/tmp/
ssh nuc
sudo mkdir -p /opt/frogswork
sudo tar -xzf /tmp/frogswork-v1.0.0.tar.gz -C /opt/frogswork --strip-components=1
export FROGSWORK_PRODUCTION=1
sudo -E bash /opt/frogswork/scripts/install/install.sh
```

Or **factory install** (claim code + registry):

```bash
sudo bash /opt/frogswork/scripts/factory/factory-install.sh \
  --serial FW-2026-00042 \
  --claim-code FW-7K3M-9P2Q
```

Install script order:

| Script | Purpose |
|--------|---------|
| `00-prereqs.sh` | apt packages (Python, nginx, Samba, btrfs, Avahi, NetworkManager) |
| `01-partition.sh` | LVM LV `frogswork-data` + btrfs `/data` |
| `02-deploy-app.sh` | venv, dashboard build (dev) or use prebuilt `dist/`, nginx/systemd |
| `03-enable-services.sh` | Enable and start services |

**Production:** set `FROGSWORK_PRODUCTION=1` so `/opt/frogswork` stays `root:root` (no dev deploy user ownership).

## 3. Development install (nuc1)

```bash
FROGSWORK_HOST=nuc1 bash scripts/dev/sync.sh
```

Passwordless sudo for deploy user is acceptable on dev units only.

## 4. Smoke test checklist

### Automated (on NUC)

```bash
sudo bash /opt/frogswork/scripts/dev/smoke-m9.sh
bash /opt/frogswork/scripts/dev/run-p0-checklist.sh
```

### Owner (manual)

- [ ] Complete setup wizard (setup code if factory unit; password + optional email otherwise)
- [ ] Create file user on **Users**
- [ ] Manage folders and permissions
- [ ] Create backup and restore a test file on **Backups**
- [ ] **System** page shows network info and helper download

### Windows helper (manual)

- [ ] Download helper from **System** or `/api/helper/download`
- [ ] Sign in with file user credentials
- [ ] Drive **W:** maps in File Explorer
- [ ] Read/write a test file

### Reboot survival

- [ ] Reboot NUC — services auto-start without SSH

## 5. Drive layout

- Unified Samba share `frogswork` at `/data/frogswork`
- Helper maps a single **W:** drive (not legacy U:/S:/T:)

See [factory-deploy.md](factory-deploy.md) for factory line process and [commercial-ship-checklist.md](commercial-ship-checklist.md) for ship criteria.
