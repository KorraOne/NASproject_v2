"""Storage usage overview for the dashboard."""

from __future__ import annotations

import shutil
from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.db import connect
from frogswork_api.paths import DATA_ROOT
from frogswork_api.schemas import StorageOverviewResponse

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("", response_model=StorageOverviewResponse)
def storage_overview(
    _admin: Annotated[str, Depends(get_current_admin)],
) -> StorageOverviewResponse:
    usage = shutil.disk_usage(DATA_ROOT)
    with connect() as conn:
        user_count = conn.execute("SELECT COUNT(*) AS n FROM file_users").fetchone()["n"]
        folder_count = conn.execute("SELECT COUNT(*) AS n FROM shared_folders").fetchone()["n"]
    return StorageOverviewResponse(
        mount=str(DATA_ROOT),
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        file_user_count=user_count,
        shared_folder_count=folder_count,
    )
