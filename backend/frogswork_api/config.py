"""Application configuration."""

import os
import secrets
from pathlib import Path

from frogswork_api.paths import DB_PATH, JWT_SECRET_FILE, STATE_DIR

# JWT access token lifetime (dashboard admin session)
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7

# Minimum dashboard admin password length
MIN_ADMIN_PASSWORD_LENGTH = 8

DEFAULT_SEED_FOLDERS = ("Projects", "Invoices", "Shared")

DEFAULT_SNAPSHOT_HOUR = 2
DEFAULT_RETENTION_DAILY = 7
DEFAULT_RETENTION_WEEKLY = 4
DEFAULT_RETENTION_MONTHLY = 3


def get_jwt_secret() -> str:
    env = os.environ.get("FROGSWORK_JWT_SECRET")
    if env:
        return env
    if JWT_SECRET_FILE.is_file():
        return JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_urlsafe(32)
    JWT_SECRET_FILE.write_text(secret, encoding="utf-8")
    try:
        JWT_SECRET_FILE.chmod(0o600)
    except OSError:
        pass
    return secret


def get_database_path() -> Path:
    override = os.environ.get("FROGSWORK_DB_PATH")
    if override:
        return Path(override)
    return DB_PATH
