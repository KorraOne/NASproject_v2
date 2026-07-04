#!/usr/bin/env bash
# Create btrfs /data on an LVM logical volume (Ubuntu default installer layout).
# Idempotent: exits 0 if /data is already mounted.
set -euo pipefail

VG_NAME="${FROGSWORK_VG:-ubuntu-vg}"
LV_NAME="${FROGSWORK_DATA_LV:-frogswork-data}"
DATA_MOUNT="/data"
DRY_RUN=false

usage() {
  echo "Usage: $0 [--dry-run]"
  echo "  Creates LV ${VG_NAME}/${LV_NAME}, formats btrfs, mounts at ${DATA_MOUNT}."
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

run() {
  if $DRY_RUN; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

if mountpoint -q "${DATA_MOUNT}"; then
  echo "==> ${DATA_MOUNT} already mounted — nothing to do."
  btrfs filesystem show "${DATA_MOUNT}" 2>/dev/null || df -h "${DATA_MOUNT}"
  exit 0
fi

LV_PATH="/dev/${VG_NAME}/${LV_NAME}"

if ! vgs "${VG_NAME}" &>/dev/null; then
  echo "ERROR: volume group ${VG_NAME} not found." >&2
  exit 1
fi

if lvs "${VG_NAME}/${LV_NAME}" &>/dev/null; then
  echo "==> Logical volume ${LV_PATH} already exists."
else
  echo "==> Creating logical volume ${LV_NAME} (90% of free space in ${VG_NAME})..."
  run lvcreate -l 90%FREE -n "${LV_NAME}" "${VG_NAME}"
fi

if ! blkid -o value -s TYPE "${LV_PATH}" 2>/dev/null | grep -q btrfs; then
  echo "==> Formatting ${LV_PATH} as btrfs..."
  run mkfs.btrfs -L frogswork-data "${LV_PATH}"
else
  echo "==> ${LV_PATH} already btrfs."
fi

run mkdir -p "${DATA_MOUNT}"

if ! grep -q "[[:space:]]${DATA_MOUNT}[[:space:]]" /etc/fstab; then
  UUID="$(blkid -s UUID -o value "${LV_PATH}")"
  echo "==> Adding ${DATA_MOUNT} to /etc/fstab (UUID=${UUID})..."
  if $DRY_RUN; then
    echo "[dry-run] echo UUID=${UUID} ${DATA_MOUNT} btrfs defaults 0 0 >> /etc/fstab"
  else
    echo "UUID=${UUID} ${DATA_MOUNT} btrfs defaults 0 0" >> /etc/fstab
  fi
fi

echo "==> Mounting ${DATA_MOUNT}..."
run mount "${DATA_MOUNT}"

echo "==> Creating data directories..."
run mkdir -p "${DATA_MOUNT}/users" "${DATA_MOUNT}/shared" "${DATA_MOUNT}/.snapshots"
run chmod 755 "${DATA_MOUNT}/users" "${DATA_MOUNT}/shared"
run chmod 700 "${DATA_MOUNT}/.snapshots"

echo "==> /data layout:"
ls -la "${DATA_MOUNT}" || true
echo "==> 01-partition.sh complete."
