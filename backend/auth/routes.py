"""Contrato de login para el unico usuario local de la demo."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.auth.security import authenticate_user, create_access_token
from backend.config import JWT_EXPIRE_MINUTES


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasenia incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user["username"]),
        expires_in_minutes=JWT_EXPIRE_MINUTES,
    )
