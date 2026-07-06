#!/usr/bin/env python3
"""Generate serial + claim code for a hand-built or factory unit."""

from __future__ import annotations

import argparse
import csv
import secrets
import string
from datetime import UTC, datetime
from pathlib import Path

# Avoid ambiguous characters (0/O, 1/I/L).
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _block(length: int = 4) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_claim_code() -> str:
    return f"FW-{_block()}-{_block()}"


def generate_serial(sequence: int, year: int | None = None) -> str:
    yr = year or datetime.now(UTC).year
    return f"FW-{yr}-{sequence:05d}"


def next_sequence(registry: Path, year: int) -> int:
    if not registry.is_file():
        return 1
    max_seq = 0
    with registry.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            serial = row.get("serial", "")
            if serial.startswith(f"FW-{year}-"):
                try:
                    max_seq = max(max_seq, int(serial.rsplit("-", 1)[-1]))
                except ValueError:
                    continue
    return max_seq + 1


def append_registry(registry: Path, row: dict[str, str]) -> None:
    registry.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "serial",
        "claim_code",
        "manufactured_date",
        "software_version",
        "hardware_model",
        "qa_pass",
        "shipped_date",
        "owner_email",
        "notes",
    ]
    write_header = not registry.is_file()
    with registry.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FrogsWork unit credentials")
    parser.add_argument("--sequence", type=int, help="Serial sequence number (default: next in registry)")
    parser.add_argument("--serial", help="Use explicit serial instead of generating")
    parser.add_argument("--claim-code", help="Use explicit claim code instead of generating")
    parser.add_argument(
        "--registry",
        default="docs/factory/unit-registry.csv",
        help="Laptop-side registry CSV (claim code stored once here only)",
    )
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--notes", default="hand-built")
    parser.add_argument("--no-registry", action="store_true", help="Print only; do not append CSV")
    args = parser.parse_args()

    registry = Path(args.registry)
    year = datetime.now(UTC).year
    sequence = args.sequence if args.sequence is not None else next_sequence(registry, year)
    serial = args.serial or generate_serial(sequence, year)
    claim_code = args.claim_code or generate_claim_code()
    manufactured = datetime.now(UTC).replace(microsecond=0).isoformat()

    print("=== FrogsWork unit credentials ===")
    print(f"Serial:      {serial}")
    print(f"Setup code:  {claim_code}")
    print(f"Version:     {args.version}")
    print()
    print("--- Label (on unit) ---")
    print("FrogsWork File Storage")
    print(f"Model FWS-1  Serial {serial}")
    print("KorraOne")
    print()
    print("--- Card (inside box) ---")
    print(f"Setup code: {claim_code}")
    print("Enter at http://frogswork.local during first-time setup")
    print(f"Serial: {serial}")
    print()
    print("Keep the setup code private until the owner claims the box.")

    if not args.no_registry:
        append_registry(
            registry,
            {
                "serial": serial,
                "claim_code": claim_code,
                "manufactured_date": manufactured,
                "software_version": args.version,
                "hardware_model": "FWS-1",
                "qa_pass": "pending",
                "notes": args.notes,
            },
        )
        print(f"Appended to registry: {registry}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
