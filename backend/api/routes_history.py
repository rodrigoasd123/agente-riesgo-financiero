"""Historial aislado por usuario autenticado."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.db.database import listar_analisis


router = APIRouter(tags=["historial"])


@router.get("/analyses")
def listar(current_user: Annotated[str, Depends(get_current_user)]) -> dict:
    return {"analyses": listar_analisis(current_user)}
