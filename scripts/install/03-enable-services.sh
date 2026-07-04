#!/usr/bin/env bash
# Enable and start FrogsWork services.
set -euo pipefail

echo "==> Enabling services..."
systemctl enable frogswork-api.service
systemctl enable nginx.service
systemctl enable avahi-daemon.service
systemctl enable smbd.service nmbd.service 2>/dev/null || systemctl enable smbd nmbd
systemctl enable frogswork-snapshot.timer 2>/dev/null || true

echo "==> Starting services..."
systemctl restart frogswork-api.service
systemctl restart nginx.service
systemctl restart avahi-daemon.service
systemctl restart smbd.service nmbd.service 2>/dev/null || systemctl restart smbd nmbd

echo "==> Service status:"
systemctl is-active frogswork-api nginx avahi-daemon smbd || true

echo "==> SSH: remote access left as-is for development (hard toggle lands in M7)."

echo "==> 03-enable-services.sh complete."
echo "    Smoke test: curl -s http://localhost/api/health"
