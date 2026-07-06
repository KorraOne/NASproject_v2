"""Unauthenticated public endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from frogswork_api.integrations import system_ops
from frogswork_api.paths import read_version

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/info")
def public_info():
    ips = system_ops.read_primary_ips()
    return {
        "hostname": system_ops.read_hostname(),
        "primary_ip": ips[0] if ips else None,
        "ips": ips,
        "version": read_version(),
        "help_path": "/help",
    }
