"""System visibility and power/SSH controls."""

from __future__ import annotations

import shutil

from fastapi import HTTPException, status

from frogswork_api.db import connect, get_setting, set_setting
from frogswork_api.integrations import system_ops
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.paths import DATA_ROOT, read_version

SSH_SETTING_KEY = "remote_ssh_enabled"
DEFAULT_PERSONAL_QUOTA_KEY = "default_personal_quota_bytes"


def ensure_ssh_setting_migrated() -> None:
    """Backfill setting on upgraded appliances without changing live sshd config."""
    with connect() as conn:
        if get_setting(conn, SSH_SETTING_KEY) is not None:
            return
        set_setting(conn, SSH_SETTING_KEY, "true")


def init_ssh_for_new_setup() -> None:
    """Fresh wizard completion: remote SSH off by default."""
    with connect() as conn:
        set_setting(conn, SSH_SETTING_KEY, "false")
    system_ops.write_ssh_dropin(False)


def get_system_info() -> dict:
    data_usage = shutil.disk_usage(DATA_ROOT)
    root_usage = shutil.disk_usage("/")
    with connect() as conn:
        from frogswork_api.services import device_identity

        row = conn.execute(
            "SELECT email FROM dashboard_admin WHERE id = 1"
        ).fetchone()
        admin_email = row["email"] if row else None
        serial = device_identity.get_device_serial(conn)
    return {
        "hostname": system_ops.read_hostname(),
        "ips": system_ops.read_primary_ips(),
        "uptime_seconds": system_ops.read_uptime_seconds(),
        "data_mount": str(DATA_ROOT),
        "data_total_bytes": data_usage.total,
        "data_used_bytes": data_usage.used,
        "data_free_bytes": data_usage.free,
        "os_total_bytes": root_usage.total,
        "os_used_bytes": root_usage.used,
        "os_free_bytes": root_usage.free,
        "version": read_version(),
        "serial": serial,
        "admin_email": admin_email,
    }


def get_ssh_status() -> dict:
    with connect() as conn:
        stored = get_setting(conn, SSH_SETTING_KEY)
    if stored is None:
        enabled = system_ops.read_ssh_dropin_enabled()
    else:
        enabled = stored == "true"
    return {"remote_enabled": enabled}


def set_ssh_status(enabled: bool) -> dict:
    try:
        system_ops.write_ssh_dropin(enabled)
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    with connect() as conn:
        set_setting(conn, SSH_SETTING_KEY, "true" if enabled else "false")
    return get_ssh_status()


def reboot(confirm: bool) -> dict:
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set confirm to true to reboot the appliance.",
        )
    try:
        system_ops.reboot_system()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return {"message": "Rebooting FrogsWork. The dashboard will be back in about a minute."}


def shutdown(confirm: bool) -> dict:
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set confirm to true to shut down the appliance.",
        )
    try:
        system_ops.shutdown_system()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return {
        "message": "Shutting down FrogsWork. Press the power button to turn it back on.",
    }


def get_storage_settings() -> dict:
    with connect() as conn:
        raw = get_setting(conn, DEFAULT_PERSONAL_QUOTA_KEY)
    quota = int(raw) if raw is not None else None
    return {"default_personal_quota_bytes": quota}


def update_storage_settings(
    *,
    default_personal_quota_bytes: int | None,
    apply_to_uncapped_users: bool = False,
) -> dict:
    if default_personal_quota_bytes is not None and default_personal_quota_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default personal cap must be a positive number of bytes.",
        )

    usernames_to_apply: list[str] = []
    with connect() as conn:
        if default_personal_quota_bytes is None:
            conn.execute(
                "DELETE FROM system_settings WHERE key = ?",
                (DEFAULT_PERSONAL_QUOTA_KEY,),
            )
        else:
            set_setting(conn, DEFAULT_PERSONAL_QUOTA_KEY, str(default_personal_quota_bytes))

        if apply_to_uncapped_users and default_personal_quota_bytes is not None:
            rows = conn.execute(
                "SELECT id, username FROM file_users WHERE quota_bytes IS NULL"
            ).fetchall()
            usernames_to_apply = [row["username"] for row in rows]
            for row in rows:
                conn.execute(
                    "UPDATE file_users SET quota_bytes = ? WHERE id = ?",
                    (default_personal_quota_bytes, row["id"]),
                )

    if usernames_to_apply and default_personal_quota_bytes is not None:
        from frogswork_api.integrations import linux_users

        for username in usernames_to_apply:
            try:
                linux_users.set_quota(username, default_personal_quota_bytes)
            except IntegrationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(exc),
                ) from exc

    return get_storage_settings()
