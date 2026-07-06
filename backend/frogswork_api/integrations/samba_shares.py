"""Samba share helpers — unified [frogswork] share (ACL on subfolders)."""

from __future__ import annotations

from frogswork_api.integrations._run import run_cmd
from frogswork_api.paths import SAMBA_SHARE_NAME


def share_name(_folder_name: str | None = None) -> str:
    """All folders live under the single frogswork SMB share."""
    return SAMBA_SHARE_NAME


def reload_samba() -> None:
    run_cmd("testparm", "-s")
    run_cmd("systemctl", "reload", "smbd")


def test_and_reload() -> None:
    reload_samba()


# Legacy no-ops — per-folder fragments removed in unified share model.
def write_share_config(*_args, **_kwargs) -> None:
    return None


def remove_share_config(*_args, **_kwargs) -> None:
    return None


def rebuild_manifest() -> None:
    return None
