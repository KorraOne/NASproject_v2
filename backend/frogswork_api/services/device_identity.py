"""Factory device identity and claim-code validation."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from frogswork_api.auth.security import hash_password, verify_password
from frogswork_api.db import utc_now_iso

CLAIM_CODE_PATTERN = re.compile(r"^FW-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$")
MAX_CLAIM_ATTEMPTS = 5
CLAIM_WINDOW_HOURS = 1


def skip_claim_check() -> bool:
    return os.environ.get("FROGSWORK_SKIP_CLAIM", "").strip() in ("1", "true", "yes")


def requires_claim_code(conn: sqlite3.Connection) -> bool:
    if skip_claim_check():
        return False
    row = conn.execute(
        "SELECT claimed_at FROM device_identity WHERE id = 1"
    ).fetchone()
    return row is not None and row["claimed_at"] is None


def get_device_serial(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT serial FROM device_identity WHERE id = 1").fetchone()
    if row is None:
        return None
    return row["serial"]


def normalize_claim_code(code: str) -> str:
    return code.strip().upper()


def validate_claim_code_format(code: str) -> None:
    if not CLAIM_CODE_PATTERN.match(normalize_claim_code(code)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup code format is invalid. Check the card in your box.",
        )


def _claim_window_start() -> str:
    start = datetime.now(UTC) - timedelta(hours=CLAIM_WINDOW_HOURS)
    return start.replace(microsecond=0).isoformat()


def verify_claim_code(conn: sqlite3.Connection, claim_code: str) -> None:
    validate_claim_code_format(claim_code)
    row = conn.execute(
        """
        SELECT claim_code_hash, claimed_at, claim_attempts, claim_window_start
        FROM device_identity WHERE id = 1
        """
    ).fetchone()
    if row is None:
        return
    if row["claimed_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This device has already been set up.",
        )

    window_start = row["claim_window_start"]
    attempts = row["claim_attempts"] or 0
    if window_start is None or window_start < _claim_window_start():
        attempts = 0
        window_start = utc_now_iso()
        conn.execute(
            """
            UPDATE device_identity
            SET claim_attempts = 0, claim_window_start = ?
            WHERE id = 1
            """,
            (window_start,),
        )

    if attempts >= MAX_CLAIM_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect setup codes. Wait an hour and try again.",
        )

    if not verify_password(normalize_claim_code(claim_code), row["claim_code_hash"]):
        conn.execute(
            """
            UPDATE device_identity
            SET claim_attempts = claim_attempts + 1, claim_window_start = ?
            WHERE id = 1
            """,
            (window_start,),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect setup code. Check the card in your box.",
        )


def mark_claimed(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE device_identity
        SET claimed_at = ?, claim_code_hash = '', claim_attempts = 0
        WHERE id = 1 AND claimed_at IS NULL
        """,
        (utc_now_iso(),),
    )


def seed_device_identity(
    conn: sqlite3.Connection,
    *,
    serial: str,
    claim_code: str,
    software_version: str,
) -> None:
    validate_claim_code_format(claim_code)
    now = utc_now_iso()
    claim_hash = hash_password(normalize_claim_code(claim_code))
    existing = conn.execute("SELECT id FROM device_identity WHERE id = 1").fetchone()
    if existing:
        conn.execute(
            """
            UPDATE device_identity
            SET serial = ?, claim_code_hash = ?, manufactured_at = ?,
                software_version = ?, claimed_at = NULL, claim_attempts = 0,
                claim_window_start = NULL
            WHERE id = 1
            """,
            (serial, claim_hash, now, software_version),
        )
    else:
        conn.execute(
            """
            INSERT INTO device_identity (
                id, serial, claim_code_hash, manufactured_at,
                software_version, claimed_at, claim_attempts, claim_window_start
            ) VALUES (1, ?, ?, ?, ?, NULL, 0, NULL)
            """,
            (serial, claim_hash, now, software_version),
        )
