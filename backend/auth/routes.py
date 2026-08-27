"""Autenticación, sesión revocable y administración RBAC."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.auth.dependencies import CurrentUser, get_current_identity, require_admin
from backend.auth.security import authenticate_user, hash_password, issue_access_token
from backend.config import JWT_EXPIRE_MINUTES
from backend.db.database import (
    crear_usuario,
    establecer_usuario_activo,
    listar_usuarios,
    normalize_username,
    revocar_sesion,
)


router = APIRouter(prefix="/auth", tags=["auth"])
Role = Literal["admin", "analyst"]
USERNAME_PATTERN = r"^[a-z0-9](?:[a-z0-9_.-]{0,62}[a-z0-9])?$"


class LoginRequest(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    username: str
    role: Role


class CurrentUserResponse(BaseModel):
    username: str
    role: Role


class UserResponse(BaseModel):
    username: str
    role: Role
    is_active: bool
    created_at: str
    updated_at: str


class CreateUserRequest(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64, pattern=USERNAME_PATTERN)]
    password: Annotated[str, Field(min_length=12, max_length=128)]
    role: Role = "analyst"

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username_field(cls, value: object) -> object:
        return normalize_username(str(value))


class ActiveUserRequest(BaseModel):
    is_active: bool


def _public_user(user: dict) -> UserResponse:
    return UserResponse(
        username=str(user["username"]),
        role=user["role"],
        is_active=bool(user["is_active"]),
        created_at=str(user["created_at"]),
        updated_at=str(user["updated_at"]),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasenia incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = issue_access_token(user["username"], user["role"])
    return TokenResponse(
        access_token=token,
        expires_in_minutes=JWT_EXPIRE_MINUTES,
        username=user["username"],
        role=user["role"],
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(identity: Annotated[CurrentUser, Depends(get_current_identity)]) -> CurrentUserResponse:
    return CurrentUserResponse(username=identity.username, role=identity.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(identity: Annotated[CurrentUser, Depends(get_current_identity)]) -> None:
    revocar_sesion(identity.jti, identity.username)


@router.get("/users", response_model=list[UserResponse])
def users(_: Annotated[CurrentUser, Depends(require_admin)]) -> list[UserResponse]:
    return [_public_user(user) for user in listar_usuarios()]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> UserResponse:
    try:
        user = crear_usuario(payload.username, hash_password(payload.password), payload.role)
    except ValueError as exc:
        if str(exc) == "username_exists":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario ya existe",
            ) from None
        raise
    return _public_user(user)


@router.patch("/users/{username}/active", response_model=UserResponse)
def update_user_active(
    username: str,
    payload: ActiveUserRequest,
    identity: Annotated[CurrentUser, Depends(require_admin)],
) -> UserResponse:
    target = normalize_username(username)
    if target == identity.username and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes desactivar tu propia cuenta",
        )
    user = establecer_usuario_activo(target, payload.is_active)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _public_user(user)
