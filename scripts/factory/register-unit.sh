#!/usr/bin/env bash
# Append a row to the factory unit registry CSV.
# Usage: register-unit.sh --serial FW-2026-00042 --claim-code FW-7K3M-9P2Q --version 1.0.0 --qa-pass yes
set -euo pipefail

REGISTRY="${FROGSWORK_UNIT_REGISTRY:-/var/lib/frogswork/factory/unit-registry.csv}"
SERIAL=""
CLAIM_CODE=""
VERSION=""
QA_PASS="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial) SERIAL="$2"; shift 2 ;;
    --claim-code) CLAIM_CODE="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --qa-pass) QA_PASS="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$SERIAL" || -z "$CLAIM_CODE" || -z "$VERSION" ]]; then
  echo "Usage: $0 --serial FW-2026-00042 --claim-code FW-7K3M-9P2Q --version 1.0.0" >&2
  exit 1
fi

mkdir -p "$(dirname "$REGISTRY")"
if [[ ! -f "$REGISTRY" ]]; then
  echo "serial,claim_code,manufactured_date,software_version,hardware_model,qa_pass" >"$REGISTRY"
  chmod 600 "$REGISTRY"
fi

echo "${SERIAL},${CLAIM_CODE},$(date -Iseconds),${VERSION},FWS-1,${QA_PASS}" >>"$REGISTRY"
echo "==> Registered unit $SERIAL in $REGISTRY"
