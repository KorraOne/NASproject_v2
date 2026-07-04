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
