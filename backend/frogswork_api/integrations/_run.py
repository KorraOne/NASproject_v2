"""Run system commands (via passwordless sudo on the appliance)."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Sequence

logger = logging.getLogger(__name__)

SUDO = os.environ.get("FROGSWORK_SUDO", "sudo").split()


class IntegrationError(Exception):
    """Raised when a system integration command fails."""

    def __init__(self, message: str, *, command: Sequence[str] | None = None):
        super().__init__(message)
        self.command = list(command) if command else None


def run_cmd(
    *args: str,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        logger.info("skip system command (test mode): %s", args)
        return subprocess.CompletedProcess(args, 0, "", "")

    command = [*SUDO, "-n", *args]
    logger.info("running integration command: %s", " ".join(command))
    try:
        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise IntegrationError(
            f"System operation failed: {detail or exc.cmd}",
            command=exc.cmd,
        ) from exc
