"""Snapshot API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.schemas import (
    MessageResponse,
    SnapshotBrowseEntry,
    SnapshotConfirmTokenResponse,
    SnapshotResponse,
    SnapshotRestoreRequest,
    SnapshotSettingsResponse,
    SnapshotSettingsUpdateRequest,
)
from frogswork_api.services import snapshots as snapshot_service

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotResponse])
def list_snapshots(_admin: Annotated[str, Depends(get_current_admin)]) -> list[SnapshotResponse]:
    return snapshot_service.list_snapshots()


@router.post("", response_model=SnapshotResponse, status_code=201)
def create_snapshot(_admin: Annotated[str, Depends(get_current_admin)]) -> SnapshotResponse:
    return snapshot_service.create_snapshot()


@router.get("/settings", response_model=SnapshotSettingsResponse)
def get_settings(_admin: Annotated[str, Depends(get_current_admin)]) -> SnapshotSettingsResponse:
    return snapshot_service.get_settings()


@router.patch("/settings", response_model=SnapshotSettingsResponse)
def update_settings(
    body: SnapshotSettingsUpdateRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> SnapshotSettingsResponse:
    updates = body.model_dump(exclude_unset=True)
    return snapshot_service.update_settings(**updates)


@router.get("/{snapshot_id}/browse", response_model=list[SnapshotBrowseEntry])
def browse_snapshot(
    snapshot_id: str,
    _admin: Annotated[str, Depends(get_current_admin)],
    path: str = Query(default=""),
) -> list[SnapshotBrowseEntry]:
    return snapshot_service.browse_snapshot(snapshot_id, path)


@router.get("/{snapshot_id}/restore-token", response_model=SnapshotConfirmTokenResponse)
def restore_token(
    snapshot_id: str,
    _admin: Annotated[str, Depends(get_current_admin)],
    path: str = Query(min_length=1),
) -> SnapshotConfirmTokenResponse:
    return snapshot_service.restore_token(snapshot_id, path)


@router.post("/{snapshot_id}/restore", response_model=MessageResponse)
def restore_snapshot(
    snapshot_id: str,
    body: SnapshotRestoreRequest,
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    snapshot_service.restore_snapshot(snapshot_id, body.source_path, body.confirm_token)
    return MessageResponse(message=f"Restored '{body.source_path}' from {snapshot_id}.")
