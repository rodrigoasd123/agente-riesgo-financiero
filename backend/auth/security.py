"""bcrypt para credenciales y JWT Bearer con claims cerrados."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import bcrypt
import jwt

from backend.config import (
    ADMIN_PASSWORD_HASH,
    ADMIN_USERNAME,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_EXPIRE_MINUTES,
    JWT_ISSUER,
    JWT_SECRET_KEY,
)


_USERS_DB = {
    ADMIN_USERNAME: {
        "username": ADMIN_USERNAME,
        "hashed_password": ADMIN_PASSWORD_HASH,
        "role": "admin",
    }
}


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
    user = _USERS_DB.get(username)
    # La comprobacion dummy reduce la diferencia temporal entre usuario inexistente y password incorrecto.
    password_hash = user["hashed_password"] if user else ADMIN_PASSWORD_HASH
    valid_password = verify_password(password, password_hash)
    if user is None or not valid_password:
        return None
    return {"username": user["username"], "role": user["role"]}


def create_access_token(username: str, expires_minutes: int = JWT_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "type": "access",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "type", "iss", "aud", "iat", "nbf", "exp", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token invalido")
    return payload


def validate_auth_configuration() -> None:
    cost = int(ADMIN_PASSWORD_HASH.split("$")[2])
    if cost < 12:
        raise RuntimeError("ADMIN_PASSWORD_HASH debe usar costo bcrypt 12 o superior")
