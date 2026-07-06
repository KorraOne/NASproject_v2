"""User archetype CRUD (dashboard admin only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.db import connect
from frogswork_api.schemas import (
    ArchetypeCreateRequest,
    ArchetypeFolderPermissionAssign,
    ArchetypeFolderPermissionsReplaceRequest,
    ArchetypeResponse,
    ArchetypeUpdateRequest,
    EffectivePermissionResponse,
    MessageResponse,
)
from frogswork_api.services import archetypes as archetype_service

router = APIRouter(prefix="/api/archetypes", tags=["archetypes"])


@router.get("", response_model=list[ArchetypeResponse])
def list_archetypes(_admin: Annotated[str, Depends(get_current_admin)]) -> list[ArchetypeResponse]:
    with connect() as conn:
        return archetype_service.list_archetypes(conn)


@router.post("", response_model=ArchetypeResponse, status_code=201)
def create_archetype(
    body: ArchetypeCreateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> ArchetypeResponse:
    return archetype_service.create_archetype(body.name)


@router.get("/{archetype_id}", response_model=ArchetypeResponse)
def get_archetype(
    archetype_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> ArchetypeResponse:
    with connect() as conn:
        return archetype_service.get_archetype(conn, archetype_id)


@router.patch("/{archetype_id}", response_model=ArchetypeResponse)
def update_archetype(
    archetype_id: int,
    body: ArchetypeUpdateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> ArchetypeResponse:
    updates = body.model_dump(exclude_unset=True)
    return archetype_service.update_archetype(archetype_id, name=updates.get("name"))


@router.delete("/{archetype_id}", response_model=MessageResponse)
def delete_archetype(
    archetype_id: int,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    with connect() as conn:
        existing = archetype_service.get_archetype(conn, archetype_id)
    archetype_service.delete_archetype(archetype_id)
    return MessageResponse(message=f"Deleted archetype '{existing['name']}'.")


@router.put("/{archetype_id}/permissions", response_model=list[ArchetypeFolderPermissionAssign])
def replace_archetype_permissions(
    archetype_id: int,
    body: ArchetypeFolderPermissionsReplaceRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> list[ArchetypeFolderPermissionAssign]:
    return archetype_service.replace_archetype_permissions(
        archetype_id,
        [{"folder_id": p.folder_id, "access": p.access} for p in body.permissions],
    )


permissions_router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@permissions_router.get("/effective", response_model=list[EffectivePermissionResponse])
def list_effective_permissions(
    _admin: Annotated[str, Depends(get_current_admin)],
) -> list[EffectivePermissionResponse]:
    with connect() as conn:
        return archetype_service.list_effective_permissions(conn)
