"""Dynamic Samba share fragments for shared folders."""

from __future__ import annotations

from pathlib import Path

from frogswork_api.integrations._run import run_cmd
from frogswork_api.paths import SAMBA_SHARES_D, SAMBA_SHARES_STAGING

SHARE_PREFIX = "shared-"


def share_name(folder_name: str) -> str:
    return f"{SHARE_PREFIX}{folder_name}"


def _conf_filename(folder_name: str) -> str:
    safe = folder_name.replace("/", "-").replace(" ", "-")
    return f"{safe}.conf"


def _render_share(folder_name: str, folder_path: Path, usernames: list[str]) -> str:
    name = share_name(folder_name)
    if usernames:
        users_line = "   valid users = " + " ".join(usernames)
    else:
        users_line = "   valid users = __frogswork_no_access__\n   browseable = no"
    return f"""[{name}]
   comment = FrogsWork shared folder {folder_name}
   path = {folder_path}
   browseable = yes
   read only = no
{users_line}
"""


def write_share_config(folder_name: str, folder_path: Path, usernames: list[str]) -> None:
    SAMBA_SHARES_STAGING.mkdir(parents=True, exist_ok=True)

    staging = SAMBA_SHARES_STAGING / _conf_filename(folder_name)
    staging.write_text(
        _render_share(folder_name, folder_path, usernames),
        encoding="utf-8",
    )
    dest = SAMBA_SHARES_D / _conf_filename(folder_name)
    run_cmd("install", "-m", "644", str(staging), str(dest))


def remove_share_config(folder_name: str) -> None:
    path = SAMBA_SHARES_D / _conf_filename(folder_name)
    if path.exists():
        run_cmd("rm", "-f", str(path))
    staging = SAMBA_SHARES_STAGING / _conf_filename(folder_name)
    if staging.exists():
        staging.unlink()


def test_and_reload() -> None:
    run_cmd("testparm", "-s")
    run_cmd("systemctl", "reload", "smbd")
