"""Snapshot business logic."""

from __future__ import annotations

from fastapi import HTTPException, status

from frogswork_api.config import (
    DEFAULT_RETENTION_DAILY,
    DEFAULT_RETENTION_MONTHLY,
    DEFAULT_RETENTION_WEEKLY,
    DEFAULT_SNAPSHOT_HOUR,
)
from frogswork_api.db import connect, get_setting, set_setting
from frogswork_api.integrations import btrfs
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.services import retention as retention_service


def _snapshot_to_dict(info: btrfs.SnapshotInfo) -> dict:
    return {
        "id": info.id,
        "name": info.name,
        "kind": info.kind,
        "snapshot_date": info.snapshot_date.isoformat(),
        "created_at": info.created_at,
    }


def list_snapshots() -> list[dict]:
    return [_snapshot_to_dict(s) for s in btrfs.list_snapshots()]


def create_snapshot() -> dict:
    try:
        info = btrfs.create_daily_snapshot()
        return _snapshot_to_dict(info)
    except IntegrationError as exc:
        if "already exists" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def get_settings() -> dict:
    with connect() as conn:
        return {
            "snapshot_hour": int(get_setting(conn, "snapshot_hour", str(DEFAULT_SNAPSHOT_HOUR))),
            "retention_daily": int(
                get_setting(conn, "retention_daily", str(DEFAULT_RETENTION_DAILY))
            ),
            "retention_weekly": int(
                get_setting(conn, "retention_weekly", str(DEFAULT_RETENTION_WEEKLY))
            ),
            "retention_monthly": int(
                get_setting(conn, "retention_monthly", str(DEFAULT_RETENTION_MONTHLY))
            ),
        }


def update_settings(
    *,
    snapshot_hour: int | None = None,
    retention_daily: int | None = None,
    retention_weekly: int | None = None,
    retention_monthly: int | None = None,
) -> dict:
    if snapshot_hour is not None and not 0 <= snapshot_hour <= 23:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot hour must be between 0 and 23.",
        )
    for value, label in (
        (retention_daily, "Daily retention"),
        (retention_weekly, "Weekly retention"),
        (retention_monthly, "Monthly retention"),
    ):
        if value is not None and value < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label} must be at least 1.",
            )

    with connect() as conn:
        if snapshot_hour is not None:
            set_setting(conn, "snapshot_hour", str(snapshot_hour))
        if retention_daily is not None:
            set_setting(conn, "retention_daily", str(retention_daily))
        if retention_weekly is not None:
            set_setting(conn, "retention_weekly", str(retention_weekly))
        if retention_monthly is not None:
            set_setting(conn, "retention_monthly", str(retention_monthly))

    return get_settings()


def browse_snapshot(snapshot_id: str, path: str = "") -> list[dict]:
    try:
        return btrfs.browse_snapshot(snapshot_id, path)
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


def restore_token(snapshot_id: str, source_path: str) -> dict:
    try:
        token = btrfs.restore_confirm_token(snapshot_id, source_path)
        return {"confirm_token": token, "source_path": source_path.strip().lstrip("/")}
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def restore_snapshot(snapshot_id: str, source_path: str, confirm_token: str) -> None:
    try:
        btrfs.restore_path(snapshot_id, source_path, confirm_token)
    except IntegrationError as exc:
        if "Confirmation token" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


def apply_retention() -> None:
    try:
        retention_service.apply_retention()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
