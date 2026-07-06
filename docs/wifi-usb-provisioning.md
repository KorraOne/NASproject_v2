# WiFi USB provisioning

**Status:** Implemented — `import-wifi.sh`, systemd path/service, NetworkManager in prereqs.

Alternative to ethernet for customers who cannot run a cable to the router. Ships in every retail box.

## Retail USB contents

| File | Direction | Purpose |
|------|-----------|---------|
| `WiFi Setup.html` | Factory → customer | Offline form on PC to write config |
| `README.txt` | Factory → customer | Ethernet vs WiFi setup steps |
| `frogswork-setup.json` | PC → NUC | WiFi credentials (consumed once) |
| `frogswork-setup.log` | NUC → PC | Human-readable diagnostic log |
| `frogswork-setup.status` | NUC → PC | `success` or `failed` + error code |

Tooling: [`tools/wifi-setup/`](../tools/wifi-setup/)

## Customer flow

1. On Windows/Mac: open `WiFi Setup.html` on the USB stick
2. Enter network name, password, country → saves `frogswork-setup.json`
3. Safely eject USB, plug into powered-on FrogsWork box (no ethernet)
4. NUC applies WiFi, writes log + status to USB, scrubs JSON
5. Remove USB, join same WiFi on phone/laptop, open `http://frogswork.local`
6. If failed: re-plug USB into PC and read `frogswork-setup.log` (or send to support)

## Input format (`frogswork-setup.json`)

```json
{
  "version": 1,
  "wifi": {
    "ssid": "OfficeWiFi",
    "password": "secret",
    "country": "AU"
  },
  "optional_hostname": "frogswork"
}
```

## Log format (`frogswork-setup.log`)

```
[FrogsWork WiFi Setup]
Started: 2026-07-06T10:15:00+08:00
Serial: FW-2026-00042
Software: 1.0.0

Step 1: USB mount detected          OK
Step 2: Read frogswork-setup.json   OK
Step 3: Validate SSID/country       OK
Step 4: nmcli connection create     OK
Step 5: Associate to AP             OK  (signal -52 dBm)
Step 6: DHCP address obtained       OK  (192.168.1.87)
Step 7: Dashboard health check      OK
Step 8: Scrub credentials from USB  OK

Finished: SUCCESS
Next: Remove USB, connect your PC to the same WiFi, open http://frogswork.local
```

On failure: log failing step, sanitized nmcli stderr, short “What to try” hint.

**Never log WiFi password.**

## Status format (`frogswork-setup.status`)

```json
{
  "result": "success",
  "error_code": null,
  "ip": "192.168.1.87",
  "finished_at": "2026-07-06T10:16:00+08:00"
}
```

## Security rules

1. Delete or zero `frogswork-setup.json` after read (success or failure)
2. Never persist password in `.log` or `.status`
3. Log may include: serial, timestamps, SSID name, IP, signal, error codes
4. `sync` before USB unmount

## Implementation

| Component | Path |
|-----------|------|
| Import script | [`scripts/factory/import-wifi.sh`](../scripts/factory/import-wifi.sh) |
| systemd path unit | [`deploy/systemd/frogswork-usb-provision.path`](../deploy/systemd/frogswork-usb-provision.path) |
| systemd service | [`deploy/systemd/frogswork-usb-provision.service`](../deploy/systemd/frogswork-usb-provision.service) |
| PC-side HTML | [`tools/wifi-setup/WiFi Setup.html`](../tools/wifi-setup/WiFi%20Setup.html) |

### systemd watcher

Watches `/media/*/*/frogswork-setup.json` (USB automount paths). On trigger, runs `import-wifi.sh` with mount path as argument.

### Dependencies

- `network-manager` + `nmcli` on appliance
- Writable FAT/exFAT USB (customer sticks)

## Support workflow

Customer emails support → attaches `frogswork-setup.log` from USB → support sees exact failure step without remote SSH.

## Fallback

Quick-start card lists **ethernet cable** as primary path. Phone hotspot as last resort.
