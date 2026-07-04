"""Linux user accounts, private folders, and ACLs."""

from __future__ import annotations

import shutil
from pathlib import Path

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import DATA_ROOT, DATA_USERS

SUPERUSER_GROUP = "frogswork-superuser"
NOLOGIN_SHELL = "/usr/sbin/nologin"


def ensure_superuser_group() -> None:
    run_cmd("groupadd", "-f", SUPERUSER_GROUP)


def _is_btrfs(path: Path) -> bool:
    try:
        run_cmd("btrfs", "filesystem", "show", str(path))
        return True
    except IntegrationError:
        return False


def create_home_directory(username: str) -> Path:
    home = DATA_USERS / username
    if home.exists():
        raise IntegrationError(f"Home directory already exists: {home}")

    if _is_btrfs(DATA_ROOT):
        run_cmd("btrfs", "subvolume", "create", str(home))
    else:
        home.mkdir(parents=True, exist_ok=False)
    return home


def remove_home_directory(username: str) -> None:
    home = DATA_USERS / username
    if not home.exists():
        return
    if _is_btrfs(DATA_ROOT):
        run_cmd("btrfs", "subvolume", "delete", str(home))
    else:
        shutil.rmtree(home)


def apply_private_folder_permissions(username: str) -> None:
    home = DATA_USERS / username
    run_cmd("chown", f"{username}:{username}", str(home))
    run_cmd(
        "setfacl",
        "-m",
        f"u:{username}:rwx,g:{SUPERUSER_GROUP}:r-x,o:---",
        str(home),
    )
    run_cmd("setfacl", "-m", f"m:rwx", str(home))


def create_linux_user(username: str) -> None:
    ensure_superuser_group()
    home = create_home_directory(username)
    try:
        run_cmd(
            "useradd",
            "--home-dir",
            str(home),
            "--no-create-home",
            "--shell",
            NOLOGIN_SHELL,
            username,
        )
        apply_private_folder_permissions(username)
    except IntegrationError:
        remove_home_directory(username)
        raise


def delete_linux_user(username: str) -> None:
    try:
        run_cmd("userdel", username)
    except IntegrationError as exc:
        if "does not exist" not in str(exc).lower():
            raise
    remove_home_directory(username)


def set_superuser_membership(username: str, enabled: bool) -> None:
    ensure_superuser_group()
    if enabled:
        run_cmd("usermod", "-aG", SUPERUSER_GROUP, username)
    else:
        run_cmd("gpasswd", "-d", username, SUPERUSER_GROUP)


def set_quota(username: str, quota_bytes: int | None) -> None:
    home = DATA_USERS / username
    if not home.exists():
        raise IntegrationError(f"Home directory not found for {username}.")

    if quota_bytes is None:
        return

    if not _is_btrfs(DATA_ROOT):
        return

    run_cmd("btrfs", "quota", "enable", str(DATA_ROOT))
    limit = f"{quota_bytes}b"
    run_cmd("btrfs", "qgroup", "limit", limit, str(home))
