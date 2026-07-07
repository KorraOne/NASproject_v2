# Prototype deploy (nuc1) — click-to-update

This is the **fast iteration** workflow for real hardware: you publish a prototype build, then (as a “customer”) you click **System → Updates → Apply update** in the dashboard.

## How it works

- CI publishes a **prototype release** on tag `proto` with assets:
  - `frogswork-proto.tar.gz`
  - `frogswork-proto.tar.gz.sha256`
- CI also commits a moving manifest to the repo:
  - `updates/latest-proto.json`
- The appliance checks the manifest URL, downloads the tarball, verifies SHA256, then applies the update (atomic swap + service restart).

## 1) Point nuc1 at the prototype channel

On the NUC (over SSH), set `FROGSWORK_UPDATE_MANIFEST_URL` for the API service.

Create a systemd override:

```bash
sudo systemctl edit frogswork-api.service
```

Add:

```ini
[Service]
Environment=FROGSWORK_UPDATE_MANIFEST_URL=https://raw.githubusercontent.com/<OWNER>/<REPO>/main/updates/latest-proto.json
```

Then reload + restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart frogswork-api.service
```

## 2) Validate the end-to-end update loop

1. Push a commit to `main` (or run the workflow manually) to update the `proto` release.\n+2. On nuc1 dashboard: **System → Updates → Check for updates**.\n+3. Confirm it shows **Update available**.\n+4. Click **Apply update**.\n+5. Wait 1–3 minutes, refresh dashboard.\n+\n+If you need logs on the box:\n+\n+```bash\n+sudo journalctl -u frogswork-api.service -n 200 --no-pager\n+```\n+\n+## Notes\n+\n+- Stable (sellable) units should use `updates/latest.json` instead:\n+  `https://raw.githubusercontent.com/<OWNER>/<REPO>/main/updates/latest.json`\n+- If the update mechanism is disabled, it’s usually because `FROGSWORK_UPDATE_MANIFEST_URL` is not set.\n+
