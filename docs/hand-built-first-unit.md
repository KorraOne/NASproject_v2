# Your first hand-built FrogsWork unit

Step-by-step for building **one unit yourself** (not a full factory line). For boxed retail later, see [factory-deploy.md](factory-deploy.md).

## What you track (laptop spreadsheet)

Keep the **master copy** on your laptop in `docs/factory/unit-registry.csv` (copy from [`unit-registry.template.csv`](factory/unit-registry.template.csv)). The appliance stores only a **hash** of the setup code.

| Field | When | Example | Notes |
|-------|------|---------|-------|
| `serial` | Before install | `FW-2026-00001` | On unit label; support/RMA |
| `claim_code` | Before install | `FW-7K3M-9P2Q` | **Card inside box only** — never on exterior |
| `manufactured_date` | Build day | ISO timestamp | Auto-filled by script |
| `software_version` | Build day | `1.0.0` | Match git tag |
| `hardware_model` | Build day | `FWS-1` | Fixed for v1 |
| `qa_pass` | After smoke tests | `yes` / `pending` | Update when Path A passes |
| `shipped_date` | When you sell | | Optional until sold |
| `owner_email` | After customer setup | | From dashboard (optional note) |
| `notes` | Anytime | `hand-built nuc2` | Your reference |

Generate and log a row:

```powershell
python scripts/factory/generate-unit-credentials.py --notes "first hand-built unit"
```

Print the label text from the script output. Stick **serial** on the unit; **setup code** on a card inside the box.

---

## Build day checklist

### A. Laptop — credentials and release

1. `git checkout v1.0.0`
2. Generate serial + setup code (above) — save the registry CSV somewhere safe
3. Build release tarball:
   ```bash
   bash scripts/release/build-tarball.sh
   ```
4. (Optional) Build WiFi setup USB:
   ```powershell
   .\scripts\factory\build-wifi-usb.ps1 -DriveLetter E
   ```
   Replace `E` with your USB drive letter.

### B. NUC — Ubuntu

1. Install **Ubuntu Server 26.04 LTS** (UEFI, default LVM, OpenSSH)
2. Hostname: `frogswork`
3. **Do not** leave passwordless sudo on the shipped unit

### C. NUC — FrogsWork install (production)

```bash
scp dist/frogswork-v1.0.0.tar.gz nuc:/tmp/
ssh nuc
sudo mkdir -p /opt/frogswork
sudo tar -xzf /tmp/frogswork-v1.0.0.tar.gz -C /opt/frogswork --strip-components=1

sudo bash /opt/frogswork/scripts/factory/factory-install.sh \
  --serial FW-2026-00001 \
  --claim-code FW-7K3M-9P2Q
```

Use the serial and setup code from step A2.

This installs software, seeds the claim code, copies the helper, enables WiFi USB watcher, runs burn-in, and appends a factory registry row on the device.

### D. Hand the customer

Include in the box:

- Appliance + power cable
- Ethernet cable
- WiFi setup USB (optional path)
- **Setup code card** (inside box)
- **Serial label** (on unit)
- Printed [customer-quick-start.md](../customer-quick-start.md)

Tell the owner:

1. Plug in power (+ ethernet, or use WiFi USB)
2. Open **http://frogswork.local**
3. Enter setup code, create owner email/password
4. Add staff under **Users**
5. Send staff the **employee help link** — they download the helper themselves (see below)

---

## Owner vs staff — who downloads the helper?

| Person | What they do |
|--------|----------------|
| **Owner** | Sets up the box, adds users, shares the employee help link |
| **Each staff member** | Opens the help link on their own Windows PC, downloads and installs the helper, signs in |

Employee help URL (no admin login):

```
http://frogswork.local/help
```

Owner copies this from **User guide** in the dashboard.

---

## WiFi USB — customer flow

1. On a PC: open `WiFi Setup.html` on the USB → enter Wi-Fi details → save `frogswork-setup.json` to the USB root
2. Eject USB, plug into powered-on FrogsWork box, wait ~2 minutes
3. Plug USB back into PC, open `frogswork-setup.log` — look for `Finished: SUCCESS`
4. Join the same Wi-Fi on the PC, open **http://frogswork.local**

If it fails, send `frogswork-setup.log` to support (no password in the log).

---

## Before you sell — verify

Walk [commercial-ship-checklist.md](../commercial-ship-checklist.md) Path A on **this exact unit**:

```bash
bash /opt/frogswork/scripts/dev/run-p0-checklist.sh
```

Plus manual: fresh claim wizard, Windows helper **W:** drive, backup restore, reboot.

Update `qa_pass` to `yes` in your laptop registry when done.

---

## Warranty (what to tell customers)

See [warranty-rma.md](../warranty-rma.md). In short: Australian Consumer Law applies; if the hardware is **faulty**, you will repair, replace, or refund. No separate “24-month” marketing promise beyond that.

---

## Related

- [customer-quick-start.md](../customer-quick-start.md)
- [retail-kit-and-labels.md](../retail-kit-and-labels.md)
- [wifi-usb-provisioning.md](../wifi-usb-provisioning.md)
