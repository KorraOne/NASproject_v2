#!/usr/bin/env bash
# Install apt packages required by FrogsWork File Storage.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

PACKAGES=(
  python3-venv
  python3-pip
  python3-dev
  nginx
  samba
  samba-common-bin
  btrfs-progs
  acl
  avahi-daemon
  avahi-utils
  rsync
  curl
  lvm2
  nodejs
  npm
)

echo "==> Updating apt cache..."
apt-get update -qq

echo "==> Installing packages: ${PACKAGES[*]}"
apt-get install -y --no-install-recommends "${PACKAGES[@]}"

echo "==> Package versions (key tools):"
python3 --version
node --version
nginx -v 2>&1 || true
smbd --version 2>&1 | head -1 || true
btrfs --version | head -1

echo "==> 00-prereqs.sh complete."
