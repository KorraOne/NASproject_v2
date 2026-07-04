"""Well-known paths on the appliance and in development."""

from pathlib import Path

# Repo root (development) or /opt/frogswork (appliance)
REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"

DATA_ROOT = Path("/data")
DATA_USERS = DATA_ROOT / "users"
DATA_SHARED = DATA_ROOT / "shared"
DATA_SNAPSHOTS = DATA_ROOT / ".snapshots"

STATE_DIR = Path("/var/lib/frogswork")


def read_version() -> str:
    if VERSION_FILE.is_file():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0-dev"
