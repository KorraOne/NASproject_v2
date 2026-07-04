"""Windows helper app API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from frogswork_api.helper.deps import get_current_file_user
from frogswork_api.paths import HELPER_EXE
from frogswork_api.schemas import HelperMountListResponse
from frogswork_api.services import helper_mounts as helper_mount_service

router = APIRouter(prefix="/api/helper", tags=["helper"])

DEFAULT_HOST = "frogswork.local"


@router.get("/mounts", response_model=HelperMountListResponse)
def list_mounts(
    file_user: Annotated[str, Depends(get_current_file_user)],
    host: str = Query(default=DEFAULT_HOST, min_length=1),
) -> HelperMountListResponse:
    return helper_mount_service.get_mounts_for_user(file_user, host)


@router.get("/download")
def download_helper() -> FileResponse:
    if not HELPER_EXE.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Helper app is not installed on this appliance yet.",
        )
    return FileResponse(
        path=HELPER_EXE,
        filename="FrogsWork.Helper.exe",
        media_type="application/octet-stream",
    )
