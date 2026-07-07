"""Update integration — fetch release manifest + stage tarball + apply."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import PENDING_UPDATE_SHA256, PENDING_UPDATE_TARBALL, UPDATES_DIR


@dataclass(frozen=True)
class UpdateManifest:
    version: str
    tarball_url: str
    sha256: str
    notes: str | None = None


def _skip_system() -> bool:
    return os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1"


def _read_url_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        raise IntegrationError(f"Could not fetch update manifest: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise IntegrationError(f"Update manifest is not valid JSON: {exc}") from exc


def fetch_manifest(url: str) -> UpdateManifest:
    data = _read_url_json(url)
    for key in ("version", "tarball_url", "sha256"):
        if key not in data or not isinstance(data[key], str) or not data[key].strip():
            raise IntegrationError(f"Update manifest missing field: {key}")
    notes = data.get("notes")
    if notes is not None and not isinstance(notes, str):
        notes = None
    return UpdateManifest(
        version=data["version"].strip(),
        tarball_url=data["tarball_url"].strip(),
        sha256=data["sha256"].strip(),
        notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
    )


def _sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_update_tarball(*, tarball_url: str, sha256_hex: str) -> None:
    """Download tarball and write pending.* files under /var/lib/frogswork/updates."""
    if _skip_system():
        return

    UPDATES_DIR.mkdir(parents=True, exist_ok=True)

    tmp_path = UPDATES_DIR / "pending.tar.gz.tmp"
    try:
        with urllib.request.urlopen(tarball_url, timeout=60) as resp:
            with open(tmp_path, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
    except Exception as exc:  # noqa: BLE001
        raise IntegrationError(f"Could not download update tarball: {exc}") from exc

    actual = _sha256_file(tmp_path)
    if actual.lower() != sha256_hex.lower():
        tmp_path.unlink(missing_ok=True)
        raise IntegrationError("Update tarball failed SHA256 verification.")

    tmp_path.replace(PENDING_UPDATE_TARBALL)
    PENDING_UPDATE_SHA256.write_text(f"{sha256_hex}  pending.tar.gz\n", encoding="utf-8")


def apply_staged_update() -> None:
    """Run the root update apply script via sudo."""
    if _skip_system():
        return
    # sudoers allows this exact command only.
    run_cmd("/opt/frogswork/scripts/update/apply-update.sh")

