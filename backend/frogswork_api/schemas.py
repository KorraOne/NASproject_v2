"""Pydantic request/response models."""

from pydantic import BaseModel, Field


class SetupStatusResponse(BaseModel):
    setup_complete: bool


class SetupRequest(BaseModel):
    password: str = Field(min_length=8)
    timezone: str = Field(min_length=1, max_length=64)


class SetupResponse(BaseModel):
    setup_complete: bool
    message: str


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class AdminMeResponse(BaseModel):
    role: str = "dashboard_admin"


class FileUserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    is_superuser: bool
    quota_bytes: int | None
    created_at: str
    updated_at: str


class FileUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str | None = Field(default=None, max_length=64)
    password: str = Field(min_length=8)
    is_superuser: bool = False
    quota_bytes: int | None = None


class FileUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    password: str | None = Field(default=None, min_length=8)
    is_superuser: bool | None = None
    quota_bytes: int | None = None
    folder_permissions: list["UserFolderPermissionEntry"] | None = None


class UserFolderPermissionEntry(BaseModel):
    folder_id: int
    access: str = Field(pattern="^(read|read_write)$")


class FolderPermissionEntry(BaseModel):
    user_id: int
    username: str
    access: str


class FolderPermissionsReplaceRequest(BaseModel):
    permissions: list["FolderPermissionAssign"]


class FolderPermissionAssign(BaseModel):
    user_id: int
    access: str = Field(pattern="^(read|read_write)$")


class FolderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class FolderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)


class FolderResponse(BaseModel):
    id: int
    name: str
    slug: str
    path: str
    share_name: str
    created_at: str
    permissions: list[FolderPermissionEntry]


class StorageOverviewResponse(BaseModel):
    mount: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    file_user_count: int
    shared_folder_count: int


class SnapshotResponse(BaseModel):
    id: str
    name: str
    kind: str
    snapshot_date: str
    created_at: str


class SnapshotSettingsResponse(BaseModel):
    snapshot_hour: int
    retention_daily: int
    retention_weekly: int
    retention_monthly: int


class SnapshotSettingsUpdateRequest(BaseModel):
    snapshot_hour: int | None = Field(default=None, ge=0, le=23)
    retention_daily: int | None = Field(default=None, ge=1)
    retention_weekly: int | None = Field(default=None, ge=1)
    retention_monthly: int | None = Field(default=None, ge=1)


class SnapshotBrowseEntry(BaseModel):
    name: str
    path: str
    is_dir: bool


class SnapshotRestoreRequest(BaseModel):
    source_path: str = Field(min_length=1)
    confirm_token: str = Field(min_length=1)


class SnapshotConfirmTokenResponse(BaseModel):
    confirm_token: str
    source_path: str


class SystemInfoResponse(BaseModel):
    hostname: str
    ips: list[str]
    uptime_seconds: float
    data_mount: str
    data_total_bytes: int
    data_used_bytes: int
    data_free_bytes: int
    os_total_bytes: int
    os_used_bytes: int
    os_free_bytes: int
    version: str


class SshStatusResponse(BaseModel):
    remote_enabled: bool


class SshToggleRequest(BaseModel):
    enabled: bool


class PowerConfirmRequest(BaseModel):
    confirm: bool = False


FileUserUpdateRequest.model_rebuild()
FolderPermissionsReplaceRequest.model_rebuild()

