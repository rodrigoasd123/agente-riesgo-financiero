"""Escenarios, exportaciones y distribucion de analisis autorizados."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from backend.agent.financial_tools import calcular_escenario
from backend.auth.dependencies import get_current_user
from backend.db.database import obtener_analisis
from backend.email_service import EmailUnavailableError, email_provider, enviar_reporte, validate_recipient
from backend.reporting import generar_csv, generar_pdf, safe_stem


router = APIRouter(prefix="/analyses", tags=["finanzas-reportes"])


class ProjectionRequest(BaseModel):
    initial_investment: Annotated[Decimal, Field(gt=0, le=Decimal("1000000000000"))]
    cash_flows: Annotated[list[Decimal], Field(min_length=1, max_length=30)]
    discount_rate_percent: Annotated[Decimal, Field(gt=Decimal("-99"), le=Decimal("1000"))] = Decimal("10")

    @field_validator("cash_flows")
    @classmethod
    def bounded_flows(cls, values: list[Decimal]) -> list[Decimal]:
        if any(abs(value) > Decimal("1000000000000") for value in values):
            raise ValueError("Los flujos exceden el limite permitido")
        return values


class EmailReportRequest(BaseModel):
    recipient: Annotated[str, Field(min_length=3, max_length=254)]
    projection: ProjectionRequest | None = None


def _owned(analysis_id: str, actor: str) -> dict:
    analysis = obtener_analisis(analysis_id, actor)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisis no encontrado")
    return analysis


def _projection(payload: ProjectionRequest | None) -> dict | None:
    if payload is None:
        return None
    return calcular_escenario(payload.initial_investment, payload.cash_flows, payload.discount_rate_percent)


@router.post("/{analysis_id}/projection")
def projection(analysis_id: str, payload: ProjectionRequest, actor: Annotated[str, Depends(get_current_user)]) -> dict:
    _owned(analysis_id, actor)
    return calcular_escenario(payload.initial_investment, payload.cash_flows, payload.discount_rate_percent)


@router.post("/{analysis_id}/report/csv")
def csv_report(analysis_id: str, actor: Annotated[str, Depends(get_current_user)], payload: ProjectionRequest | None = None) -> Response:
    analysis = _owned(analysis_id, actor)
    filename = f"reporte_{safe_stem(analysis['filename'])}.csv"
    return Response(generar_csv(analysis, _projection(payload)), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/{analysis_id}/report/pdf")
def pdf_report(analysis_id: str, actor: Annotated[str, Depends(get_current_user)], payload: ProjectionRequest | None = None) -> Response:
    analysis = _owned(analysis_id, actor)
    filename = f"reporte_{safe_stem(analysis['filename'])}.pdf"
    return Response(generar_pdf(analysis, _projection(payload)), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/{analysis_id}/email")
def email_report(analysis_id: str, payload: EmailReportRequest, actor: Annotated[str, Depends(get_current_user)]) -> dict:
    analysis = _owned(analysis_id, actor)
    try:
        recipient = validate_recipient(payload.recipient)
        stem = safe_stem(analysis["filename"])
        pdf_filename = f"reporte_{stem}.pdf"
        csv_filename = f"reporte_{stem}.csv"
        projection_data = _projection(payload.projection)
        pdf_bytes = generar_pdf(analysis, projection_data)
        csv_bytes = generar_csv(analysis, projection_data)
        provider = email_provider()
        enviar_reporte(
            recipient,
            pdf_filename,
            pdf_bytes,
            csv_filename,
            csv_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except EmailUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return {"sent": True, "recipient": recipient, "provider": provider}
