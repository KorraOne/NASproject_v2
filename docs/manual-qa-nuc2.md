# Manual QA (sellable nuc2)

These are the “act as customer” checks after provisioning a unit. Treat them as ship/no-ship gates.

## A) First boot / setup wizard

- Power on with **Ethernet** connected (or use WiFi USB flow if testing that path).
- In a browser: `http://frogswork.local` (or the IP from your router).
- Setup wizard:
  - Enter **claim code** (matches the card you printed)
  - Set owner email/password
  - Set timezone
- Confirm you land on the dashboard.

## B) File sharing sanity (Windows client)

On a Windows PC on the same LAN:

- Download helper from dashboard (or `http://frogswork.local/api/helper/download`).
- Run helper, sign in as a file user.
- Confirm drive mapping appears (W: for shared root).
- Create a folder + file, edit it, delete it.

## C) Permissions smoke

- Create a second file user in dashboard.
- Confirm each user only sees what they should (Personal privacy, shared folder access).
- Confirm “read-only” access really blocks writes.

## D) Updates (stable channel)

- On the unit, confirm it is configured for stable updates:
  - `FROGSWORK_UPDATE_MANIFEST_URL` points to `updates/latest.json`
- Dashboard → **System → Updates**:
  - Click **Check for updates**
  - If update available, click **Apply update**
  - Refresh after 1–3 minutes and confirm the version changed.

## E) Reboot survival

- Dashboard → System → Reboot
- Confirm after reboot:
  - Dashboard loads
  - SMB share works
  - Helper still connects and drive mapping works

## F) Quick service status (on the NUC)

```bash
systemctl is-active frogswork-api nginx avahi-daemon smbd
curl -sf http://localhost/api/health
```

## Pass/Fail recording

- If any section fails, set `qa_pass=no` in your unit registry notes and keep the logs from:
  - `/var/lib/frogswork/logs/`

