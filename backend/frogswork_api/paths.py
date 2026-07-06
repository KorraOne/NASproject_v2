"""Well-known paths on the appliance and in development."""

from pathlib import Path

# Repo root (development) or /opt/frogswork (appliance)
REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"

DATA_ROOT = Path("/data")
DATA_FROGSWORK = DATA_ROOT / "frogswork"
PERSONAL_CONTAINER_NAME = "Personal"
DATA_PERSONAL = DATA_FROGSWORK / PERSONAL_CONTAINER_NAME
DATA_USERS = DATA_PERSONAL
DATA_SHARED = DATA_FROGSWORK
DATA_SNAPSHOTS = DATA_ROOT / ".snapshots"

SAMBA_SHARE_NAME = "frogswork"
FILE_USERS_GROUP = "frogswork-users"

STATE_DIR = Path("/var/lib/frogswork")
DB_PATH = STATE_DIR / "frogswork.db"
JWT_SECRET_FILE = STATE_DIR / "jwt_secret"
SAMBA_SHARES_STAGING = STATE_DIR / "samba-shares"
SAMBA_SHARES_D = Path("/etc/samba/shares.d")
HELPER_DIR = STATE_DIR / "helper"
HELPER_EXE = HELPER_DIR / "FrogsWork.Helper.exe"


def read_version() -> str:
    if VERSION_FILE.is_file():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0-dev"
