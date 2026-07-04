"""Samba passdb sync for file users."""

from __future__ import annotations

from frogswork_api.integrations._run import IntegrationError, run_cmd


def set_password(username: str, password: str) -> None:
    # smbpasswd -a -s reads password twice from stdin
    input_text = f"{password}\n{password}\n"
    try:
        run_cmd("smbpasswd", "-a", "-s", username, input_text=input_text)
    except IntegrationError:
        # User may already exist in passdb after partial create — try update
        run_cmd("smbpasswd", "-s", username, input_text=input_text)


def delete_user(username: str) -> None:
    try:
        run_cmd("smbpasswd", "-x", username)
    except IntegrationError as exc:
        if "does not exist" not in str(exc).lower():
            raise


def reload_samba() -> None:
    run_cmd("systemctl", "reload", "smbd")
