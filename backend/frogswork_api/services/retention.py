"""Snapshot retention policy enforcement."""

from __future__ import annotations

import sqlite3

from frogswork_api.config import (
    DEFAULT_RETENTION_DAILY,
    DEFAULT_RETENTION_MONTHLY,
    DEFAULT_RETENTION_WEEKLY,
)
from frogswork_api.db import connect, get_setting
from frogswork_api.integrations import btrfs


def _iso_week_key(day) -> tuple[int, int]:
    iso = day.isocalendar()
    return iso.year, iso.week


def _month_key(day) -> str:
    return day.strftime("%Y-%m")


def _load_retention(conn: sqlite3.Connection) -> tuple[int, int, int]:
    daily = int(get_setting(conn, "retention_daily", str(DEFAULT_RETENTION_DAILY)))
    weekly = int(get_setting(conn, "retention_weekly", str(DEFAULT_RETENTION_WEEKLY)))
    monthly = int(get_setting(conn, "retention_monthly", str(DEFAULT_RETENTION_MONTHLY)))
    return daily, weekly, monthly


def _grouped_snapshots() -> tuple[list, list, list]:
    snapshots = btrfs.list_snapshots()
    dailies = sorted(
        [s for s in snapshots if s.kind == "daily"],
        key=lambda s: s.snapshot_date,
        reverse=True,
    )
    weeklies = sorted(
        [s for s in snapshots if s.kind == "weekly"],
        key=lambda s: s.snapshot_date,
        reverse=True,
    )
    monthlies = sorted(
        [s for s in snapshots if s.kind == "monthly"],
        key=lambda s: s.snapshot_date,
        reverse=True,
    )
    return dailies, weeklies, monthlies


def apply_retention() -> None:
    with connect() as conn:
        retention_daily, retention_weekly, retention_monthly = _load_retention(conn)

    dailies, weeklies, monthlies = _grouped_snapshots()
    for snap in monthlies[retention_monthly:]:
        btrfs.delete_snapshot(snap.id)

    dailies, weeklies, monthlies = _grouped_snapshots()
    monthly_months = {_month_key(s.snapshot_date) for s in monthlies}
    for snap in weeklies[retention_weekly:]:
        month = _month_key(snap.snapshot_date)
        if month not in monthly_months:
            btrfs.rename_snapshot(snap.id, f"monthly-{snap.snapshot_date.isoformat()}")
            monthly_months.add(month)
        else:
            btrfs.delete_snapshot(snap.id)

    dailies, weeklies, monthlies = _grouped_snapshots()
    weekly_weeks = {_iso_week_key(s.snapshot_date) for s in weeklies}
    for snap in dailies[retention_daily:]:
        week = _iso_week_key(snap.snapshot_date)
        if week not in weekly_weeks:
            btrfs.rename_snapshot(snap.id, f"weekly-{snap.snapshot_date.isoformat()}")
            weekly_weeks.add(week)
        else:
            btrfs.delete_snapshot(snap.id)
