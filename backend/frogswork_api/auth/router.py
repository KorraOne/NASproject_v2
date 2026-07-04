"""Dashboard admin authentication."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from frogswork_api.auth.deps import get_current_admin
from frogswork_api.auth.security import create_access_token, verify_password
from frogswork_api.db import connect, is_setup_complete
from frogswork_api.schemas import AdminMeResponse, LoginRequest, LoginResponse, MessageResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    with connect() as conn:
        if not is_setup_complete(conn):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Setup is not complete. Finish the setup wizard first.",
            )
        row = conn.execute(
            "SELECT password_hash FROM dashboard_admin WHERE id = 1"
        ).fetchone()
        if row is None or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password.",
            )
    token = create_access_token()
    return LoginResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    _admin: Annotated[str, Depends(get_current_admin)],
) -> MessageResponse:
    # JWT is stateless; client discards the token.
    return MessageResponse(message="Signed out.")


@router.get("/me", response_model=AdminMeResponse)
def me(_admin: Annotated[str, Depends(get_current_admin)]) -> AdminMeResponse:
    return AdminMeResponse()
