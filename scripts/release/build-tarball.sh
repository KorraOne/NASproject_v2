#!/usr/bin/env bash
# Build a factory release tarball (prebuilt dashboard + helper exe).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(tr -d '\r\n' < "${ROOT}/VERSION")"
OUT_DIR="${1:-${ROOT}/dist}"
STAGING="${OUT_DIR}/frogswork-${VERSION}"
ARCHIVE="${OUT_DIR}/frogswork-v${VERSION}.tar.gz"

echo "==> Building FrogsWork release ${VERSION}"

cd "${ROOT}/dashboard"
if [[ -f package-lock.json ]]; then
  npm ci --silent
else
  npm install --silent
fi
npm run build

cd "${ROOT}/helper/FrogsWork.Helper"
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o "${ROOT}/dist/helper-publish" -v q

rm -rf "${STAGING}"
mkdir -p "${STAGING}/backend" "${STAGING}/dashboard/dist" "${STAGING}/helper" \
  "${STAGING}/scripts" "${STAGING}/deploy"

cp -a "${ROOT}/backend/frogswork_api" "${ROOT}/backend/pyproject.toml" "${ROOT}/backend/tests" "${STAGING}/backend/"
cp -a "${ROOT}/dashboard/dist/." "${STAGING}/dashboard/dist/"
cp "${ROOT}/dist/helper-publish/FrogsWork.Helper.exe" "${STAGING}/helper/FrogsWork.Helper.exe"
cp -a "${ROOT}/scripts/install" "${ROOT}/scripts/btrfs" "${ROOT}/scripts/samba" \
  "${ROOT}/scripts/factory" "${ROOT}/scripts/migrate" "${STAGING}/scripts/"
cp -a "${ROOT}/deploy/." "${STAGING}/deploy/"
cp "${ROOT}/VERSION" "${STAGING}/VERSION"

if [[ -f "${ROOT}/scripts/install/install.sh" ]]; then
  :
else
  cat >"${STAGING}/scripts/install/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${DIR}/00-prereqs.sh"
bash "${DIR}/01-partition.sh"
bash "${DIR}/02-deploy-app.sh"
bash "${DIR}/03-enable-services.sh"
EOF
  chmod +x "${STAGING}/scripts/install/install.sh"
fi

tar -czf "${ARCHIVE}" -C "${OUT_DIR}" "frogswork-${VERSION}"
SHA256="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
echo "${SHA256}  frogswork-v${VERSION}.tar.gz" > "${ARCHIVE}.sha256"

echo "==> Created ${ARCHIVE}"
echo "==> SHA256 ${SHA256}"
