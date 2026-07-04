"""First-run setup wizard."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status

from frogswork_api.auth.security import hash_password
from frogswork_api.config import (
    DEFAULT_RETENTION_DAILY,
    DEFAULT_RETENTION_MONTHLY,
    DEFAULT_RETENTION_WEEKLY,
    DEFAULT_SEED_FOLDERS,
    DEFAULT_SNAPSHOT_HOUR,
    MIN_ADMIN_PASSWORD_LENGTH,
)
from frogswork_api.db import connect, is_setup_complete, set_setting, utc_now_iso
from frogswork_api.paths import DATA_SHARED
from frogswork_api.schemas import SetupRequest, SetupResponse, SetupStatusResponse

router = APIRouter(prefix="/api/setup", tags=["setup"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "folder"


def run_setup(password: str, timezone: str) -> None:
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters.",
        )

    with connect() as conn:
        if is_setup_complete(conn):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Setup is already complete.",
            )

        password_hash = hash_password(password)
        now = utc_now_iso()
        conn.execute(
            "INSERT INTO dashboard_admin (id, password_hash, created_at) VALUES (1, ?, ?)",
            (password_hash, now),
        )

        set_setting(conn, "setup_complete", "true")
        set_setting(conn, "timezone", timezone)
        set_setting(conn, "snapshot_hour", str(DEFAULT_SNAPSHOT_HOUR))
        set_setting(conn, "retention_daily", str(DEFAULT_RETENTION_DAILY))
        set_setting(conn, "retention_weekly", str(DEFAULT_RETENTION_WEEKLY))
        set_setting(conn, "retention_monthly", str(DEFAULT_RETENTION_MONTHLY))

        for name in DEFAULT_SEED_FOLDERS:
            slug = _slugify(name)
            folder_path = DATA_SHARED / name
            folder_path.mkdir(parents=True, exist_ok=True)
            conn.execute(
                """
                INSERT INTO shared_folders (name, slug, path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, slug, str(folder_path), now),
            )


@router.get("/status", response_model=SetupStatusResponse)
def setup_status() -> SetupStatusResponse:
    with connect() as conn:
        return SetupStatusResponse(setup_complete=is_setup_complete(conn))


@router.post("", response_model=SetupResponse)
def complete_setup(body: SetupRequest) -> SetupResponse:
    run_setup(body.password, body.timezone)
    return SetupResponse(
        setup_complete=True,
        message="Setup complete. Sign in with your dashboard admin password.",
    )
