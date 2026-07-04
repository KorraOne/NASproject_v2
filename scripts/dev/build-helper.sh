#!/usr/bin/env bash
# Build the Windows helper and optionally copy to NUC.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROJECT="${REPO_ROOT}/helper/FrogsWork.Helper"
OUT="${REPO_ROOT}/helper/publish"

echo "==> Publishing FrogsWork Helper (win-x64, self-contained)..."
dotnet publish "${PROJECT}" -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true \
  -p:PublishTrimmed=false \
  -o "${OUT}"

echo "==> Output: ${OUT}/FrogsWork.Helper.exe"

if [[ "${1:-}" == "--deploy" ]]; then
  HOST="${FROGSWORK_HOST:-nuc1}"
  echo "==> Copying to ${HOST}:/var/lib/frogswork/helper/"
  ssh "${HOST}" "sudo mkdir -p /var/lib/frogswork/helper && sudo chown \$(whoami):\$(whoami) /var/lib/frogswork/helper"
  scp "${OUT}/FrogsWork.Helper.exe" "${HOST}:/var/lib/frogswork/helper/"
  ssh "${HOST}" "sudo chown frogswork:frogswork /var/lib/frogswork/helper/FrogsWork.Helper.exe && sudo chmod 644 /var/lib/frogswork/helper/FrogsWork.Helper.exe"
  echo "==> Download at http://frogswork.local/api/helper/download"
fi
