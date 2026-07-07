"""Well-known paths on the appliance and in development."""

from __future__ import annotations

import os
from pathlib import Path


def _env_path(key: str, default: str) -> Path:
    value = os.environ.get(key)
    return Path(value) if value else Path(default)


# Repo root (development) or /opt/frogswork (appliance)
REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"

# Override in tests/CI with FROGSWORK_DATA_ROOT and FROGSWORK_STATE_DIR.
DATA_ROOT = _env_path("FROGSWORK_DATA_ROOT", "/data")
DATA_FROGSWORK = DATA_ROOT / "frogswork"
PERSONAL_CONTAINER_NAME = "Personal"
DATA_PERSONAL = DATA_FROGSWORK / PERSONAL_CONTAINER_NAME
DATA_USERS = DATA_PERSONAL
DATA_SHARED = DATA_FROGSWORK
DATA_SNAPSHOTS = DATA_ROOT / ".snapshots"

SAMBA_SHARE_NAME = "frogswork"
FILE_USERS_GROUP = "frogswork-users"

STATE_DIR = _env_path("FROGSWORK_STATE_DIR", "/var/lib/frogswork")
DB_PATH = STATE_DIR / "frogswork.db"
JWT_SECRET_FILE = STATE_DIR / "jwt_secret"
SAMBA_SHARES_STAGING = STATE_DIR / "samba-shares"
SAMBA_SHARES_D = Path("/etc/samba/shares.d")
HELPER_DIR = STATE_DIR / "helper"
HELPER_EXE = HELPER_DIR / "FrogsWork.Helper.exe"
UPDATES_DIR = STATE_DIR / "updates"
PENDING_UPDATE_TARBALL = UPDATES_DIR / "pending.tar.gz"
PENDING_UPDATE_SHA256 = UPDATES_DIR / "pending.sha256"


def read_version() -> str:
    if VERSION_FILE.is_file():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0-dev"
