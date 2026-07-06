"""Linux user accounts, private folders, and ACLs."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import DATA_FROGSWORK, DATA_PERSONAL, DATA_ROOT, DATA_USERS, FILE_USERS_GROUP

SUPERUSER_GROUP = "frogswork-superuser"
NOLOGIN_SHELL = "/usr/sbin/nologin"


def ensure_superuser_group() -> None:
    run_cmd("groupadd", "-f", SUPERUSER_GROUP)


def ensure_file_users_group() -> None:
    run_cmd("groupadd", "-f", FILE_USERS_GROUP)


def ensure_personal_container() -> None:
    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        DATA_FROGSWORK.mkdir(parents=True, exist_ok=True)
        DATA_PERSONAL.mkdir(parents=True, exist_ok=True)
        return
    try:
        run_cmd("test", "-d", str(DATA_FROGSWORK))
    except IntegrationError:
        run_cmd("mkdir", "-p", str(DATA_FROGSWORK))
    try:
        run_cmd("test", "-d", str(DATA_PERSONAL))
    except IntegrationError:
        run_cmd("mkdir", "-p", str(DATA_PERSONAL))


def create_home_directory(username: str) -> Path:
    ensure_personal_container()
    home = DATA_USERS / username
    try:
        run_cmd("test", "!", "-e", str(home))
    except IntegrationError:
        raise IntegrationError(f"Home directory already exists: {home}") from None

    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        home.mkdir(parents=True, exist_ok=False)
        return home

    if _is_btrfs(DATA_ROOT):
        run_cmd("btrfs", "subvolume", "create", str(home))
    else:
        run_cmd("mkdir", "-p", str(home))
    return home


def _is_btrfs(path: Path) -> bool:
    try:
        run_cmd("btrfs", "filesystem", "show", str(path))
        return True
    except IntegrationError:
        return False


def _path_exists(path: Path) -> bool:
    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        return path.exists()
    try:
        run_cmd("test", "-e", str(path))
        return True
    except IntegrationError:
        return False


def remove_home_directory(username: str) -> None:
    home = DATA_USERS / username
    if not _path_exists(home):
        return
    if _is_btrfs(DATA_ROOT):
        run_cmd("btrfs", "subvolume", "delete", str(home))
    else:
        shutil.rmtree(home)


def ensure_private_primary_group(username: str) -> None:
    """Ensure the user owns a private group (legacy accounts used frogswork-users)."""
    try:
        run_cmd("getent", "group", username)
    except IntegrationError:
        run_cmd("groupadd", username)
    run_cmd("usermod", "-g", username, username)
    run_cmd("usermod", "-aG", FILE_USERS_GROUP, username)


def apply_private_folder_permissions(
    username: str,
    *,
    extra_grants: list[tuple[str, str]] | None = None,
) -> None:
    home = DATA_USERS / username
    ensure_private_primary_group(username)
    run_cmd("chown", f"{username}:{username}", str(home))
    run_cmd("chmod", "700", str(home))
    run_cmd("setfacl", "-b", str(home))
    run_cmd("setfacl", "-m", f"u:{username}:rwx", str(home))
    run_cmd("setfacl", "-d", "-m", f"u:{username}:rwx", str(home))
    run_cmd("setfacl", "-m", f"g:{SUPERUSER_GROUP}:r-x", str(home))
    for grantee, access in extra_grants or []:
        mode = "rwx" if access == "read_write" else "r-x"
        run_cmd("setfacl", "-m", f"u:{grantee}:{mode}", str(home))
    run_cmd("setfacl", "-m", "m:rwx", str(home))
    run_cmd("setfacl", "-m", "o:---", str(home))


def create_linux_user(username: str) -> None:
    ensure_superuser_group()
    ensure_file_users_group()
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
        run_cmd("usermod", "-aG", FILE_USERS_GROUP, username)
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
        return
    try:
        run_cmd("gpasswd", "-d", username, SUPERUSER_GROUP)
    except IntegrationError as exc:
        message = str(exc).lower()
        if "is not a member" in message or "not a member of" in message:
            return
        raise


def set_quota(username: str, quota_bytes: int | None) -> None:
    set_path_quota(DATA_USERS / username, quota_bytes)


def set_path_quota(path: Path, quota_bytes: int | None) -> None:
    if not _path_exists(path):
        raise IntegrationError(f"Path not found: {path}")

    if quota_bytes is None:
        return

    if not _is_btrfs(DATA_ROOT):
        return

    run_cmd("btrfs", "quota", "enable", str(DATA_ROOT))
    limit = f"{quota_bytes}b"
    run_cmd("btrfs", "qgroup", "limit", limit, str(path))
