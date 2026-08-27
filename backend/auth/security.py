"""bcrypt, JWT Bearer con claims cerrados y sesiones persistentes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import uuid4

import bcrypt
import jwt

from backend.config import (
    ADMIN_PASSWORD_HASH,
    ANALYST_PASSWORD_HASH,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_EXPIRE_MINUTES,
    JWT_ISSUER,
    JWT_SECRET_KEY,
)
from backend.db.database import crear_sesion, normalize_username, obtener_usuario

Role = Literal["admin", "analyst"]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def hash_password(plain_password: str) -> str:
    if not plain_password:
        raise ValueError("La contrasenia no puede estar vacia")
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = obtener_usuario(normalize_username(username))
    # La comprobacion dummy reduce la diferencia temporal entre usuario inexistente y password incorrecto.
    password_hash = user["password_hash"] if user else ADMIN_PASSWORD_HASH
    valid_password = verify_password(password, password_hash)
    if user is None or not bool(user["is_active"]) or not valid_password:
        return None
    return {"username": user["username"], "role": user["role"]}


def create_access_token(
    username: str,
    role: Role = "admin",
    expires_minutes: int = JWT_EXPIRE_MINUTES,
    *,
    jti: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": normalize_username(username),
        "role": role,
        "type": "access",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": jti or str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def issue_access_token(
    username: str,
    role: Role,
    expires_minutes: int = JWT_EXPIRE_MINUTES,
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)
    jti = str(uuid4())
    crear_sesion(jti, username, expires_at)
    return create_access_token(username, role, expires_minutes, jti=jti)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "role", "type", "iss", "aud", "iat", "nbf", "exp", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token invalido")
    if payload.get("role") not in {"admin", "analyst"}:
        raise jwt.InvalidTokenError("Rol de token invalido")
    if not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise jwt.InvalidTokenError("Sujeto de token invalido")
    if not isinstance(payload.get("jti"), str) or not payload["jti"]:
        raise jwt.InvalidTokenError("Sesion de token invalida")
    return payload


def validate_auth_configuration() -> None:
    for variable, password_hash in (
        ("ADMIN_PASSWORD_HASH", ADMIN_PASSWORD_HASH),
        ("ANALYST_PASSWORD_HASH", ANALYST_PASSWORD_HASH),
    ):
        cost = int(password_hash.split("$")[2])
        if cost < 12:
            raise RuntimeError(f"{variable} debe usar costo bcrypt 12 o superior")
