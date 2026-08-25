"""Preguntas fundamentadas sobre un analisis propiedad del actor."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.agent.financial_context import construir_fragmentos_indicadores
from backend.agent.moderation import MENSAJE_BLOQUEO, contiene_termino_bloqueado
from backend.config import MAX_CHAT_LENGTH
from backend.db.database import actualizar_embeddings, guardar_pregunta, obtener_analisis
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
    retrieval_route: str
    retrieval_confidence: float
    retrieval_cache_hit: bool


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

    document_chunks = json.loads(analisis["chunks_json"] or "[]")
    cached_embeddings = json.loads(analisis.get("embeddings_json") or "[]")
    structured_chunks = construir_fragmentos_indicadores(
        json.loads(analisis["indicadores_json"] or "{}"),
        json.loads(analisis["alertas_json"] or "[]"),
    )
    if not document_chunks and not structured_chunks:
        raise HTTPException(status_code=409, detail="El analisis no contiene texto consultable")

    with agent_run(run_name=f"chat-{payload.analysis_id}"):
        resultado = qa_graph.invoke(
            {
                "pregunta": payload.pregunta,
                "document_chunks": document_chunks,
                "structured_chunks": structured_chunks,
                "document_embeddings": cached_embeddings,
            }
        )

    resulting_embeddings = resultado.get("document_embeddings", [])
    if resulting_embeddings and resulting_embeddings != cached_embeddings:
        actualizar_embeddings(payload.analysis_id, current_user, resulting_embeddings)

    response = ChatResponse(
        respuesta=resultado.get("respuesta", ""),
        fuente=resultado.get("fuente"),
        encontrado=bool(resultado.get("encontrado")),
        retrieval_route=resultado.get("retrieval_route", "sin_evidencia"),
        retrieval_confidence=float(resultado.get("retrieval_confidence", 0)),
        retrieval_cache_hit=bool(resultado.get("retrieval_cache_hit")),
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
