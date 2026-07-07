# Update manifests

This folder is written by CI.

- `latest.json`: stable channel (newest semver tag).
- `latest-proto.json`: prototype channel (moving build).

Appliances read these via:

- `https://raw.githubusercontent.com/<OWNER>/<REPO>/main/updates/latest.json`
- `https://raw.githubusercontent.com/<OWNER>/<REPO>/main/updates/latest-proto.json`

