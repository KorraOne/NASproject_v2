"""File user CRUD (dashboard admin only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.db import connect
from frogswork_api.schemas import (
    FileUserCreateRequest,
    FileUserResponse,
    FileUserUpdateRequest,
    MessageResponse,
)
from frogswork_api.services import permissions as permission_service
from frogswork_api.services import users as user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[FileUserResponse])
def list_users(_admin: Annotated[str, Depends(get_current_admin)]) -> list[FileUserResponse]:
    with connect() as conn:
        return user_service.list_users(conn)


@router.post("", response_model=FileUserResponse, status_code=201)
def create_user(
    body: FileUserCreateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FileUserResponse:
    display_name = body.display_name or body.username
    return user_service.create_user(
        username=body.username,
        display_name=display_name,
        password=body.password,
        is_superuser=body.is_superuser,
        quota_bytes=body.quota_bytes,
    )


@router.get("/{user_id}", response_model=FileUserResponse)
def get_user(
    user_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FileUserResponse:
    with connect() as conn:
        return user_service.get_user(conn, user_id)


@router.patch("/{user_id}", response_model=FileUserResponse)
def update_user(
    user_id: int,
    body: FileUserUpdateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> FileUserResponse:
    updates = body.model_dump(exclude_unset=True)
    folder_permissions = updates.pop("folder_permissions", None)
    result = user_service.update_user(
        user_id,
        display_name=updates.get("display_name"),
        password=updates.get("password"),
        is_superuser=updates.get("is_superuser"),
        quota_bytes=updates.get("quota_bytes"),
        update_quota="quota_bytes" in updates,
    )
    if folder_permissions is not None:
        permission_service.replace_user_permissions(
            user_id,
            [{"folder_id": p["folder_id"], "access": p["access"]} for p in folder_permissions],
        )
        with connect() as conn:
            return user_service.get_user(conn, user_id)
    return result


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    with connect() as conn:
        existing = user_service.get_user(conn, user_id)
    user_service.delete_user(user_id)
    return MessageResponse(message=f"Deleted user '{existing['username']}'.")
