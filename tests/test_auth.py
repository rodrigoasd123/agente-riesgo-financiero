"""
Pruebas de seguridad: verificacion de contrasenia con bcrypt contra el
hash provisto por el equipo, y ciclo completo de emision/validacion de
JWT.
"""
import time

import jwt
import pytest

from backend.auth.security import (
    verify_password,
    create_access_token,
    decode_access_token,
    authenticate_user,
)
from backend.config import ADMIN_PASSWORD_HASH
from backend.config import JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_SECRET_KEY


def test_password_correcta_verifica_ok():
    assert verify_password("admin123", ADMIN_PASSWORD_HASH) is True


def test_password_incorrecta_falla():
    assert verify_password("clave-incorrecta", ADMIN_PASSWORD_HASH) is False


def test_authenticate_user_admin():
    user = authenticate_user("admin", "admin123")
    assert user is not None
    assert user["username"] == "admin"


def test_authenticate_user_password_mala():
    assert authenticate_user("admin", "password-mala") is None


def test_jwt_roundtrip():
    token = create_access_token("admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["type"] == "access"
    assert payload["iss"]
    assert payload["aud"]
    assert payload["jti"]


def test_jwt_token_expirado():
    token = create_access_token("admin", expires_minutes=0)
    time.sleep(1)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_jwt_firma_alterada_falla():
    token = create_access_token("admin")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token + "x")


def test_jwt_audiencia_incorrecta_falla():
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "admin",
            "type": "access",
            "iss": JWT_ISSUER,
            "aud": "otra-api",
            "iat": now,
            "nbf": now,
            "exp": now + 60,
            "jti": "test-audience",
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(jwt.InvalidAudienceError):
        decode_access_token(token)


def test_jwt_tipo_incorrecto_falla():
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "admin",
            "type": "refresh",
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": now,
            "nbf": now,
            "exp": now + 60,
            "jti": "test-type",
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
