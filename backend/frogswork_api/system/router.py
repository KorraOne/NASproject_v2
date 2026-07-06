"""System API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.schemas import (
    MessageResponse,
    PowerConfirmRequest,
    SshStatusResponse,
    SshToggleRequest,
    StorageSettingsResponse,
    StorageSettingsUpdateRequest,
    SystemInfoResponse,
)
from frogswork_api.services import system as system_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
def system_info(_admin: Annotated[str, Depends(get_current_admin)]) -> SystemInfoResponse:
    return system_service.get_system_info()


@router.get("/ssh", response_model=SshStatusResponse)
def ssh_status(_admin: Annotated[str, Depends(get_current_admin)]) -> SshStatusResponse:
    return system_service.get_ssh_status()


@router.post("/ssh", response_model=SshStatusResponse)
def set_ssh_status(
    body: SshToggleRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> SshStatusResponse:
    return system_service.set_ssh_status(body.enabled)


@router.get("/storage-settings", response_model=StorageSettingsResponse)
def storage_settings(
    _admin: Annotated[str, Depends(get_current_admin)],
) -> StorageSettingsResponse:
    return system_service.get_storage_settings()


@router.patch("/storage-settings", response_model=StorageSettingsResponse)
def update_storage_settings(
    body: StorageSettingsUpdateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> StorageSettingsResponse:
    return system_service.update_storage_settings(
        default_personal_quota_bytes=body.default_personal_quota_bytes,
        apply_to_uncapped_users=body.apply_to_uncapped_users,
    )


@router.post("/reboot", response_model=MessageResponse)
def reboot_system(
    body: PowerConfirmRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    result = system_service.reboot(body.confirm)
    return MessageResponse(message=result["message"])


@router.post("/shutdown", response_model=MessageResponse)
def shutdown_system(
    body: PowerConfirmRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    result = system_service.shutdown(body.confirm)
    return MessageResponse(message=result["message"])
