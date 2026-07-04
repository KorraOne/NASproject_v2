"""System integration — SSH drop-in, power control, host info."""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import DATA_ROOT, STATE_DIR

SSH_DROPIN = Path("/etc/ssh/sshd_config.d/frogswork.conf")
SSH_STAGING = STATE_DIR / "sshd-frogswork.conf"

SSH_DISABLED_CONTENT = """# Managed by FrogsWork — remote SSH disabled
AllowUsers __frogswork_ssh_disabled__
"""

SSH_ENABLED_MARKER = "# Managed by FrogsWork — remote SSH enabled\n"


def _skip_system() -> bool:
    return os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1"


def read_uptime_seconds() -> float:
    if _skip_system():
        return 86400.0
    uptime_text = Path("/proc/uptime").read_text(encoding="utf-8").split()[0]
    return float(uptime_text)


def read_primary_ips() -> list[str]:
    if _skip_system():
        return ["127.0.0.1"]
    result = run_cmd("hostname", "-I")
    return [part for part in result.stdout.split() if part]


def read_hostname() -> str:
    return socket.gethostname()


def write_ssh_dropin(enabled: bool) -> None:
    if _skip_system():
        SSH_STAGING.parent.mkdir(parents=True, exist_ok=True)
        if enabled:
            SSH_STAGING.write_text(SSH_ENABLED_MARKER, encoding="utf-8")
        else:
            SSH_STAGING.write_text(SSH_DISABLED_CONTENT, encoding="utf-8")
        return
    if enabled:
        if SSH_DROPIN.is_file():
            run_cmd("rm", "-f", str(SSH_DROPIN))
    else:
        SSH_STAGING.parent.mkdir(parents=True, exist_ok=True)
        SSH_STAGING.write_text(SSH_DISABLED_CONTENT, encoding="utf-8")
        run_cmd("install", "-m", "644", str(SSH_STAGING), str(SSH_DROPIN))
    run_cmd("systemctl", "reload", "ssh")


def read_ssh_dropin_enabled() -> bool:
    if _skip_system():
        if not SSH_STAGING.is_file():
            return False
        content = SSH_STAGING.read_text(encoding="utf-8")
        return "__frogswork_ssh_disabled__" not in content
    if not SSH_DROPIN.is_file():
        return True
    result = run_cmd("cat", str(SSH_DROPIN))
    return "__frogswork_ssh_disabled__" not in result.stdout


def reboot_system() -> None:
    if _skip_system():
        return
    run_cmd("systemctl", "reboot")


def shutdown_system() -> None:
    if _skip_system():
        return
    run_cmd("systemctl", "poweroff")
