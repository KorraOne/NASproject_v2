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
