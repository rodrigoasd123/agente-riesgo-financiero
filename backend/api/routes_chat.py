"""Preguntas fundamentadas sobre un analisis propiedad del actor."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.agent.financial_context import construir_fragmentos_financieros
from backend.agent.moderation import MENSAJE_BLOQUEO, contiene_termino_bloqueado
from backend.config import MAX_CHAT_LENGTH
from backend.db.database import guardar_pregunta, obtener_analisis
from backend.observability.tracing import agent_run
from backend.workflow.graph import qa_graph


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    analysis_id: Annotated[str, Field(min_length=1, max_length=64)]
    pregunta: Annotated[str, Field(min_length=1, max_length=MAX_CHAT_LENGTH)]


class ChatResponse(BaseModel):
    respuesta: str
    fuente: str | None
    encontrado: bool


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: Annotated[str, Depends(get_current_user)],
) -> ChatResponse:
    if contiene_termino_bloqueado(payload.pregunta):
        raise HTTPException(status_code=422, detail=MENSAJE_BLOQUEO)
    analisis = obtener_analisis(payload.analysis_id, current_user)
    if not analisis:
        # 404 evita confirmar la existencia de recursos de otro actor.
        raise HTTPException(status_code=404, detail="Analisis no encontrado")

    chunks = json.loads(analisis["chunks_json"] or "[]")
    contexto_estructurado = construir_fragmentos_financieros(
        json.loads(analisis["cifras_json"] or "{}"),
        json.loads(analisis["indicadores_json"] or "{}"),
        json.loads(analisis["alertas_json"] or "[]"),
    )
    # Se agrega al final para conservar como primera cita el PDF cuando ambas
    # fuentes contienen la misma cifra; indicadores derivados siguen disponibles.
    chunks.extend(contexto_estructurado)
    if not chunks:
        raise HTTPException(status_code=409, detail="El analisis no contiene texto consultable")

    with agent_run(run_name=f"chat-{payload.analysis_id}"):
        resultado = qa_graph.invoke({"pregunta": payload.pregunta, "chunks": chunks})

    response = ChatResponse(
        respuesta=resultado.get("respuesta", ""),
        fuente=resultado.get("fuente"),
        encontrado=bool(resultado.get("encontrado")),
    )
    guardar_pregunta(
        analysis_id=payload.analysis_id,
        asked_by=current_user,
        pregunta=payload.pregunta,
        respuesta=response.respuesta,
        fuente=response.fuente,
        encontrado=response.encontrado,
    )
    return response
