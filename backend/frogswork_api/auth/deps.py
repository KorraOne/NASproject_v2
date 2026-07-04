"""Auth dependencies for protected routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from frogswork_api.auth.security import decode_access_token
from frogswork_api.db import connect, is_setup_complete

_bearer = HTTPBearer(auto_error=False)


def require_setup_complete() -> None:
    with connect() as conn:
        if not is_setup_complete(conn):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Setup is not complete. Finish the setup wizard first.",
            )


def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    require_setup_complete()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)
