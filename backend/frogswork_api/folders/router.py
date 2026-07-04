"""Shared folder API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.db import connect
from frogswork_api.schemas import (
    FolderCreateRequest,
    FolderPermissionEntry,
    FolderPermissionsReplaceRequest,
    FolderResponse,
    FolderUpdateRequest,
    MessageResponse,
)
from frogswork_api.services import folders as folder_service
from frogswork_api.services import permissions as permission_service

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.get("", response_model=list[FolderResponse])
def list_folders(_admin: Annotated[str, Depends(get_current_admin)]) -> list[FolderResponse]:
    with connect() as conn:
        return folder_service.list_folders(conn)


@router.post("", response_model=FolderResponse, status_code=201)
def create_folder(
    body: FolderCreateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FolderResponse:
    return folder_service.create_folder(body.name)


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FolderResponse:
    with connect() as conn:
        return folder_service.get_folder(conn, folder_id)


@router.patch("/{folder_id}", response_model=FolderResponse)
def rename_folder(
    folder_id: int,
    body: FolderUpdateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FolderResponse:
    if body.name is None:
        with connect() as conn:
            return folder_service.get_folder(conn, folder_id)
    return folder_service.rename_folder(folder_id, body.name)


@router.delete("/{folder_id}", response_model=MessageResponse)
def delete_folder(
    folder_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    with connect() as conn:
        folder = folder_service.get_folder(conn, folder_id)
    folder_service.delete_folder(folder_id)
    return MessageResponse(message=f"Deleted folder '{folder['name']}'.")


@router.put("/{folder_id}/permissions", response_model=list[FolderPermissionEntry])
def replace_folder_permissions(
    folder_id: int,
    body: FolderPermissionsReplaceRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> list[FolderPermissionEntry]:
    entries = [{"user_id": p.user_id, "access": p.access} for p in body.permissions]
    return permission_service.replace_folder_permissions(folder_id, entries)
