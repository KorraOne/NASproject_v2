"""First-run setup wizard."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status

from frogswork_api.auth.security import create_access_token, hash_password
from frogswork_api.config import (
    DEFAULT_RETENTION_DAILY,
    DEFAULT_RETENTION_MONTHLY,
    DEFAULT_RETENTION_WEEKLY,
    DEFAULT_SEED_FOLDERS,
    DEFAULT_SNAPSHOT_HOUR,
    MIN_ADMIN_PASSWORD_LENGTH,
)
from frogswork_api.db import connect, is_setup_complete, set_setting, utc_now_iso
from frogswork_api.integrations import share_layout
from frogswork_api.paths import DATA_FROGSWORK
from frogswork_api.schemas import SetupRequest, SetupResponse, SetupStatusResponse
from frogswork_api.services import device_identity
from frogswork_api.services.system import init_ssh_for_new_setup

router = APIRouter(prefix="/api/setup", tags=["setup"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "folder"


def _validate_email(email: str | None, required: bool) -> str | None:
    if email is None or email.strip() == "":
        if required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for your owner account.",
            )
        return None
    normalized = email.strip().lower()
    if "@" not in normalized or len(normalized) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid email address.",
        )
    return normalized


def run_setup(
    password: str,
    timezone: str,
    *,
    claim_code: str | None = None,
    email: str | None = None,
    backup_email: str | None = None,
    backup_phone: str | None = None,
) -> str | None:
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

        claim_required = device_identity.requires_claim_code(conn)
        if claim_required:
            if not claim_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Enter the setup code from the card in your box.",
                )
            device_identity.verify_claim_code(conn, claim_code)

        normalized_email = _validate_email(email, required=claim_required)
        normalized_backup = _validate_email(backup_email, required=False)
        backup_phone_value = backup_phone.strip() if backup_phone else None

        password_hash = hash_password(password)
        now = utc_now_iso()
        conn.execute(
            """
            INSERT INTO dashboard_admin (
                id, password_hash, email, backup_email, backup_phone, created_at
            ) VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                password_hash,
                normalized_email,
                normalized_backup,
                backup_phone_value,
                now,
            ),
        )

        set_setting(conn, "setup_complete", "true")
        set_setting(conn, "timezone", timezone)
        set_setting(conn, "snapshot_hour", str(DEFAULT_SNAPSHOT_HOUR))
        set_setting(conn, "retention_daily", str(DEFAULT_RETENTION_DAILY))
        set_setting(conn, "retention_weekly", str(DEFAULT_RETENTION_WEEKLY))
        set_setting(conn, "retention_monthly", str(DEFAULT_RETENTION_MONTHLY))

        for name in DEFAULT_SEED_FOLDERS:
            slug = _slugify(name)
            DATA_FROGSWORK.mkdir(parents=True, exist_ok=True)
            folder_path = DATA_FROGSWORK / name
            folder_path.mkdir(parents=True, exist_ok=True)
            conn.execute(
                """
                INSERT INTO shared_folders (name, slug, path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, slug, str(folder_path), now),
            )

        share_layout.sync_share_root_acl([])
        if claim_required:
            device_identity.mark_claimed(conn)

    init_ssh_for_new_setup()
    return create_access_token()


@router.get("/status", response_model=SetupStatusResponse)
def setup_status() -> SetupStatusResponse:
    with connect() as conn:
        return SetupStatusResponse(
            setup_complete=is_setup_complete(conn),
            requires_claim_code=device_identity.requires_claim_code(conn),
        )


@router.post("", response_model=SetupResponse)
def complete_setup(body: SetupRequest) -> SetupResponse:
    token = run_setup(
        body.password,
        body.timezone,
        claim_code=body.claim_code,
        email=body.email,
        backup_email=body.backup_email,
        backup_phone=body.backup_phone,
    )
    return SetupResponse(
        setup_complete=True,
        message="Setup complete. Welcome to FrogsWork.",
        access_token=token,
    )
