"""Pydantic request/response models."""

from pydantic import BaseModel, ConfigDict, Field


class SetupStatusResponse(BaseModel):
    setup_complete: bool
    requires_claim_code: bool = False


class SetupRequest(BaseModel):
    password: str = Field(min_length=8)
    timezone: str = Field(min_length=1, max_length=64)
    claim_code: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    backup_email: str | None = Field(default=None, max_length=254)
    backup_phone: str | None = Field(default=None, max_length=32)


class SetupResponse(BaseModel):
    setup_complete: bool
    message: str
    access_token: str | None = None


class LoginRequest(BaseModel):
    password: str
    email: str | None = Field(default=None, max_length=254)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class AdminMeResponse(BaseModel):
    role: str = "dashboard_admin"
    email: str | None = None


class ElevationGrantEntry(BaseModel):
    grant_type: str
    target_id: int
    target_name: str
    access: str


class UserElevationResponse(BaseModel):
    expires_at: str
    granted_at: str
    reason: str | None = None
    grants: list[ElevationGrantEntry] = []


class ElevationGrantCreate(BaseModel):
    grant_type: str = Field(pattern="^(shared_folder|personal_folder)$")
    target_id: int
    access: str = Field(pattern="^(read|read_write)$")


class UserElevationReplaceRequest(BaseModel):
    duration_hours: int = Field(ge=1, le=720)
    reason: str | None = Field(default=None, max_length=200)
    grants: list[ElevationGrantCreate]


class ElevationSharedFolderOption(BaseModel):
    id: int
    name: str
    baseline_access: str
    allowed_access: list[str]


class ElevationPersonalFolderOption(BaseModel):
    user_id: int
    username: str
    display_name: str
    baseline_access: str
    allowed_access: list[str]


class ElevationOptionsResponse(BaseModel):
    shared_folders: list[ElevationSharedFolderOption]
    personal_folders: list[ElevationPersonalFolderOption]


class FileUserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    archetype_id: int | None
    archetype_name: str | None
    is_superuser: bool
    is_elevated: bool = False
    elevation: UserElevationResponse | None = None
    quota_bytes: int | None
    created_at: str
    updated_at: str


class FileUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str | None = Field(default=None, max_length=64)
    password: str = Field(min_length=8)
    archetype_id: int | None = None
    quota_bytes: int | None = None


class FileUserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=64)
    password: str | None = Field(default=None, min_length=8)
    archetype_id: int | None = None
    quota_bytes: int | None = None


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


class FolderArchetypePermissionAssign(BaseModel):
    archetype_id: int
    access: str = Field(pattern="^(read|read_write)$")


class FolderArchetypePermissionsReplaceRequest(BaseModel):
    permissions: list[FolderArchetypePermissionAssign]


class FolderArchetypePermissionEntry(BaseModel):
    archetype_id: int
    archetype_name: str
    access: str


class FolderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    quota_bytes: int | None = None
    archetype_permissions: list[FolderArchetypePermissionAssign] = []


class FolderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    quota_bytes: int | None = None


class FolderResponse(BaseModel):
    id: int
    name: str
    slug: str
    path: str
    share_name: str
    quota_bytes: int | None
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
    serial: str | None = None
    admin_email: str | None = None


class SshStatusResponse(BaseModel):
    remote_enabled: bool


class SshToggleRequest(BaseModel):
    enabled: bool


class StorageSettingsResponse(BaseModel):
    default_personal_quota_bytes: int | None


class StorageSettingsUpdateRequest(BaseModel):
    default_personal_quota_bytes: int | None = None
    apply_to_uncapped_users: bool = False


class PowerConfirmRequest(BaseModel):
    confirm: bool = False


class HelperMountResponse(BaseModel):
    label: str
    share: str
    unc_path: str
    suggested_letter: str
    kind: str
    access: str
    personal_path: str | None = None


class HelperMountListResponse(BaseModel):
    hostname: str
    username: str
    display_name: str
    mounts: list[HelperMountResponse]


class ArchetypeFolderPermissionEntry(BaseModel):
    folder_id: int
    folder_name: str
    access: str


class ArchetypeResponse(BaseModel):
    id: int
    name: str
    is_system: bool
    can_view_all_personal: bool
    user_count: int
    created_at: str
    folder_permissions: list[ArchetypeFolderPermissionEntry]


class ArchetypeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class ArchetypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)


class ArchetypeFolderPermissionAssign(BaseModel):
    folder_id: int
    access: str = Field(pattern="^(read|read_write)$")


class ArchetypeFolderPermissionsReplaceRequest(BaseModel):
    permissions: list[ArchetypeFolderPermissionAssign]


class EffectiveSharedFolderPermission(BaseModel):
    folder_name: str
    access: str


class EffectivePermissionResponse(BaseModel):
    user_id: int
    username: str
    display_name: str
    archetype_id: int | None
    archetype_name: str | None
    can_view_all_personal: bool
    is_elevated: bool = False
    elevation: UserElevationResponse | None = None
    personal_folder: str
    shared_folders: list[EffectiveSharedFolderPermission]


FileUserUpdateRequest.model_rebuild()
FolderPermissionsReplaceRequest.model_rebuild()

