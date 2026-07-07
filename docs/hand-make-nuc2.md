# Hand-make a sellable unit (nuc2)

This is the “I have fresh hardware, I want a sellable FrogsWork NUC” checklist. It is optimized for **repeatability**, **logs**, and **one command to install**.

## What you need

- Fresh Asus NUC + NVMe
- USB installer for **Ubuntu Server 26.04 LTS** (24.04 also supported)
- Ethernet (recommended during provisioning)
- Your Windows laptop with:
  - `ssh` / `scp`
  - git (to tag releases)

## 0) Decide the unit identifiers

You will record these forever:

- **Serial**: e.g. `FW-2026-00042` (sticker on the outside of the box)
- **Claim code**: e.g. `FW-7K3M-9P2Q` (card inside the box; one-time setup secret)

## 1) Install base Ubuntu + OpenSSH

1. Install Ubuntu Server (UEFI, default partitioning with LVM is OK).
2. During install, enable **OpenSSH server**.
3. Set hostname:

```bash
sudo hostnamectl set-hostname frogswork
```

4. Reboot.

## 2) Build a release tarball (on your laptop)

From this repo:

```bash
bash scripts/release/build-tarball.sh dist
```

This creates:

- `dist/frogswork-vX.Y.Z.tar.gz`
- `dist/frogswork-vX.Y.Z.tar.gz.sha256`

## 3) Copy to the NUC and extract

```bash
scp dist/frogswork-vX.Y.Z.tar.gz nuc2:/tmp/
ssh nuc2

sudo mkdir -p /opt/frogswork
sudo tar -xzf /tmp/frogswork-vX.Y.Z.tar.gz -C /opt/frogswork --strip-components=1
```

## 4) Factory-style install (recommended) with full logs

This runs install scripts, installs the helper, seeds identity (serial + claim code), registers the unit, and runs burn-in checks.

```bash
SERIAL="FW-2026-00042"
CLAIM_CODE="FW-7K3M-9P2Q"

sudo mkdir -p /var/lib/frogswork/logs

sudo -E bash /opt/frogswork/scripts/factory/factory-install.sh \
  --serial "$SERIAL" \
  --claim-code "$CLAIM_CODE" \
  |& tee "/var/lib/frogswork/logs/factory-install-$(date -Iseconds).log"
```

## 5) Automated smoke (optional extra)

```bash
sudo -E bash /opt/frogswork/scripts/dev/smoke-m9.sh \
  |& tee "/var/lib/frogswork/logs/smoke-m9-$(date -Iseconds).log"
```

## 6) Where the unit registry row goes

The factory install appends to:

- `/var/lib/frogswork/factory/unit-registry.csv`

It includes: `serial`, `claim_code`, `manufactured_date`, `software_version`, `hardware_model`, `qa_pass`.

Copy it off the NUC for your master tracking sheet:

```bash
scp nuc2:/var/lib/frogswork/factory/unit-registry.csv .
```

## 7) Manual QA (required)

Use [`docs/manual-qa-nuc2.md`](manual-qa-nuc2.md).

