"""File user CRUD (dashboard admin only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.db import connect
from frogswork_api.schemas import (
    ElevationOptionsResponse,
    FileUserCreateRequest,
    FileUserResponse,
    FileUserUpdateRequest,
    MessageResponse,
    UserElevationReplaceRequest,
    UserElevationResponse,
)
from frogswork_api.services import elevations as elevation_service
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
        archetype_id=body.archetype_id,
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
    return user_service.update_user(
        user_id,
        display_name=updates.get("display_name"),
        password=updates.get("password"),
        archetype_id=updates.get("archetype_id"),
        quota_bytes=updates.get("quota_bytes"),
        update_quota="quota_bytes" in updates,
    )


@router.get("/{user_id}/elevation/options", response_model=ElevationOptionsResponse)
def get_elevation_options(
    user_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> ElevationOptionsResponse:
    return ElevationOptionsResponse(**elevation_service.get_elevation_options(user_id))


@router.put("/{user_id}/elevation", response_model=UserElevationResponse)
def replace_elevation(
    user_id: int,
    body: UserElevationReplaceRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> UserElevationResponse:
    result = elevation_service.replace_elevations(
        user_id,
        duration_hours=body.duration_hours,
        reason=body.reason,
        grants=[g.model_dump() for g in body.grants],
    )
    return UserElevationResponse(**result)


@router.delete("/{user_id}/elevation", response_model=MessageResponse)
def revoke_elevation(
    user_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    with connect() as conn:
        user = user_service.get_user(conn, user_id)
    elevation_service.revoke_elevations(user_id)
    return MessageResponse(message=f"Revoked temporary access for '{user['username']}'.")


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    with connect() as conn:
        existing = user_service.get_user(conn, user_id)
    user_service.delete_user(user_id)
    return MessageResponse(message=f"Deleted user '{existing['username']}'.")
