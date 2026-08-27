"""Identidad autenticada y autorización por rol para rutas FastAPI."""

from dataclasses import dataclass
from typing import Annotated, Callable, Literal

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.security import decode_access_token
from backend.db.database import obtener_identidad_de_sesion


_bearer_scheme = HTTPBearer(auto_error=False)
Role = Literal["admin", "analyst"]


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: Role
    jti: str


def get_current_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacion requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        session = obtener_identidad_de_sesion(str(payload["jti"]))
    except jwt.PyJWTError:
        session = None
        payload = {}
    if (
        session is None
        or not bool(session["is_active"])
        or session["username"] != payload.get("sub")
        or session["role"] != payload.get("role")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        username=str(session["username"]),
        role=session["role"],
        jti=str(session["jti"]),
    )


def get_current_user(
    identity: Annotated[CurrentUser, Depends(get_current_identity)],
) -> str:
    return identity.username


def require_roles(*allowed_roles: Role) -> Callable:
    allowed = frozenset(allowed_roles)

    def dependency(
        identity: Annotated[CurrentUser, Depends(get_current_identity)],
    ) -> CurrentUser:
        if identity.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return identity

    return dependency


require_admin = require_roles("admin")
