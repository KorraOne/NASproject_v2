"""btrfs snapshot operations."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import DATA_ROOT, DATA_SNAPSHOTS

SNAPSHOT_NAME_PATTERN = re.compile(r"^(daily|weekly|monthly)-(\d{4}-\d{2}-\d{2})$")
ALLOWED_RESTORE_PREFIXES = ("users/", "shared/")


@dataclass(frozen=True)
class SnapshotInfo:
    id: str
    name: str
    kind: str
    snapshot_date: date
    created_at: str


def _skip_system() -> bool:
    return os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1"


def _parse_snapshot_dir(name: str) -> SnapshotInfo | None:
    match = SNAPSHOT_NAME_PATTERN.match(name)
    if not match:
        return None
    kind, day = match.group(1), match.group(2)
    snapshot_date = date.fromisoformat(day)
    created_at = datetime.combine(snapshot_date, datetime.min.time()).isoformat()
    return SnapshotInfo(
        id=name,
        name=name,
        kind=kind,
        snapshot_date=snapshot_date,
        created_at=created_at,
    )


def _list_snapshot_names() -> list[str]:
    if _skip_system():
        if not DATA_SNAPSHOTS.is_dir():
            return []
        return sorted(
            entry.name
            for entry in DATA_SNAPSHOTS.iterdir()
            if entry.is_dir() and _parse_snapshot_dir(entry.name)
        )
    result = run_cmd("ls", "-1", str(DATA_SNAPSHOTS))
    names: list[str] = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if name and _parse_snapshot_dir(name):
            names.append(name)
    return sorted(names)


def list_snapshots() -> list[SnapshotInfo]:
    snapshots: list[SnapshotInfo] = []
    for name in _list_snapshot_names():
        info = _parse_snapshot_dir(name)
        if info is not None:
            snapshots.append(info)
    snapshots.sort(key=lambda s: s.snapshot_date, reverse=True)
    return snapshots


def get_snapshot(snapshot_id: str) -> SnapshotInfo:
    info = _parse_snapshot_dir(snapshot_id)
    if info is None:
        raise IntegrationError(f"Snapshot '{snapshot_id}' not found.")
    if _skip_system():
        if not (DATA_SNAPSHOTS / snapshot_id).is_dir():
            raise IntegrationError(f"Snapshot '{snapshot_id}' not found.")
    elif snapshot_id not in _list_snapshot_names():
        raise IntegrationError(f"Snapshot '{snapshot_id}' not found.")
    return info


def create_daily_snapshot(for_date: date | None = None) -> SnapshotInfo:
    day = for_date or date.today()
    name = f"daily-{day.isoformat()}"
    dest = DATA_SNAPSHOTS / name
    if dest.exists() or (not _skip_system() and name in _list_snapshot_names()):
        raise IntegrationError(f"Snapshot '{name}' already exists.")
    DATA_SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    if _skip_system():
        dest.mkdir(parents=True, exist_ok=False)
    else:
        run_cmd("btrfs", "subvolume", "snapshot", "-r", str(DATA_ROOT), str(dest))
    return get_snapshot(name)


def delete_snapshot(snapshot_id: str) -> None:
    path = DATA_SNAPSHOTS / snapshot_id
    get_snapshot(snapshot_id)
    if _skip_system():
        import shutil

        shutil.rmtree(path)
        return
    run_cmd("btrfs", "subvolume", "delete", str(path))


def rename_snapshot(snapshot_id: str, new_name: str) -> SnapshotInfo:
    if _parse_snapshot_dir(new_name) is None:
        raise IntegrationError(f"Invalid snapshot name '{new_name}'.")
    old_path = DATA_SNAPSHOTS / snapshot_id
    new_path = DATA_SNAPSHOTS / new_name
    get_snapshot(snapshot_id)
    if new_path.exists():
        raise IntegrationError(f"Snapshot '{new_name}' already exists.")
    if _skip_system():
        old_path.rename(new_path)
    else:
        run_cmd("mv", str(old_path), str(new_path))
    return get_snapshot(new_name)


def normalize_relative_path(path: str) -> str:
    cleaned = path.strip().replace("\\", "/").lstrip("/")
    if not cleaned or ".." in cleaned.split("/"):
        raise IntegrationError("Invalid path.")
    if not any(cleaned.startswith(prefix) for prefix in ALLOWED_RESTORE_PREFIXES):
        raise IntegrationError("Path must be under users/ or shared/.")
    return cleaned


def browse_snapshot(snapshot_id: str, relative_path: str = "") -> list[dict]:
    get_snapshot(snapshot_id)
    rel = ""
    root = DATA_SNAPSHOTS / snapshot_id
    if relative_path.strip():
        rel = normalize_relative_path(relative_path)
        root = root / rel

    if _skip_system():
        if not root.is_dir():
            raise IntegrationError("Path not found in snapshot.")
        lines = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        entries: list[dict] = []
        for entry in lines:
            if entry.name == ".snapshots":
                continue
            child_path = f"{rel}/{entry.name}".lstrip("/") if rel else entry.name
            entries.append({"name": entry.name, "path": child_path, "is_dir": entry.is_dir()})
        return entries

    result = run_cmd("ls", "-1p", str(root))
    entries = []
    for line in result.stdout.splitlines():
        raw = line.strip()
        if not raw or raw == ".snapshots/":
            continue
        is_dir = raw.endswith("/")
        name = raw.rstrip("/")
        child_path = f"{rel}/{name}".lstrip("/") if rel else name
        entries.append({"name": name, "path": child_path, "is_dir": is_dir})
    if not entries and rel:
        run_cmd("test", "-d", str(root))
    return entries


def restore_confirm_token(snapshot_id: str, source_path: str) -> str:
    rel = normalize_relative_path(source_path)
    return f"RESTORE:{snapshot_id}:{rel}"


def restore_path(snapshot_id: str, source_path: str, confirm_token: str) -> None:
    rel = normalize_relative_path(source_path)
    expected = restore_confirm_token(snapshot_id, rel)
    if confirm_token != expected:
        raise IntegrationError("Confirmation token does not match. Restore cancelled.")
    snap_path = DATA_SNAPSHOTS / snapshot_id / rel
    dest_path = DATA_ROOT / rel
    if _skip_system():
        if not snap_path.exists():
            raise IntegrationError(f"'{source_path}' not found in snapshot.")
    else:
        run_cmd("test", "-e", str(snap_path))
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if _skip_system():
        import shutil

        if snap_path.is_dir():
            if dest_path.exists():
                for item in snap_path.iterdir():
                    target = dest_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, target, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, target)
            else:
                shutil.copytree(snap_path, dest_path)
        else:
            shutil.copy2(snap_path, dest_path)
        return
    if snap_path.is_dir():
        if dest_path.exists():
            run_cmd("cp", "-a", f"{snap_path}/.", str(dest_path))
        else:
            run_cmd("cp", "-a", str(snap_path), str(dest_path))
    else:
        run_cmd("cp", "-a", str(snap_path), str(dest_path))
