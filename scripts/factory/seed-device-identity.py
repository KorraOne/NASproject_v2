#!/usr/bin/env python3
"""Seed device identity from factory install."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from frogswork_api.db import connect, init_db  # noqa: E402
from frogswork_api.paths import DB_PATH  # noqa: E402
from frogswork_api.services import device_identity  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed FrogsWork device identity")
    parser.add_argument("--serial", required=True)
    parser.add_argument("--claim-code", required=True)
    parser.add_argument("--software-version", default=None)
    args = parser.parse_args()

    version = args.software_version
    if not version:
        version_file = REPO_ROOT / "VERSION"
        version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else "unknown"

    init_db(DB_PATH)
    with connect() as conn:
        device_identity.seed_device_identity(
            conn,
            serial=args.serial,
            claim_code=args.claim_code,
            software_version=version,
        )
    print(f"Seeded device identity serial={args.serial}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
