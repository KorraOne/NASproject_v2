"""File-user authentication for the Windows helper."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from frogswork_api.integrations import samba

security = HTTPBasic()


def get_current_file_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    username = credentials.username.strip().lower()
    password = credentials.password
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not samba.verify_password(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username
