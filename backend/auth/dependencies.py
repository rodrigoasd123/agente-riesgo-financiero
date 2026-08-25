"""Dependencia de autenticacion Bearer para rutas FastAPI."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.security import decode_access_token


_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacion requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return str(payload["sub"])
