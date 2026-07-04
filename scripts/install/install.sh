#!/usr/bin/env bash
# Full first-time appliance install (run on NUC with sudo).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> FrogsWork install starting..."
bash "${SCRIPT_DIR}/00-prereqs.sh"
bash "${SCRIPT_DIR}/01-partition.sh"
bash "${SCRIPT_DIR}/02-deploy-app.sh"
bash "${SCRIPT_DIR}/03-enable-services.sh"
find "${SCRIPT_DIR}/.." -name '*.sh' -exec chmod +x {} +
echo "==> FrogsWork install complete."
