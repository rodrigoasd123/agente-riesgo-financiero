"""Escenarios, exportaciones y distribucion de analisis autorizados."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.agent.financial_tools import (
    calcular_escenario,
    calcular_excedente_tesoreria,
    simular_inversion,
)
from backend.agent.sales_forecasting import pronosticar_ventas
from backend.auth.dependencies import get_current_user
from backend.db.database import obtener_analisis
from backend.email_service import EmailUnavailableError, email_provider, enviar_reporte, validate_recipient
from backend.reporting import generar_csv, generar_pdf, safe_stem


router = APIRouter(prefix="/analyses", tags=["finanzas-reportes"])


class InvestmentSimulationRequest(BaseModel):
    capital_inicial: Annotated[Decimal, Field(gt=0, le=Decimal("1000000000000"))]
    plazo_meses: Annotated[int, Field(ge=1, le=600)]
    tasa_percent: Annotated[
        Decimal | None, Field(ge=Decimal("-99.99"), le=Decimal("1000"))
    ] = None
    tasa_anual_percent: Annotated[
        Decimal | None, Field(ge=Decimal("-99.99"), le=Decimal("1000"))
    ] = None
    tipo_tasa: Literal["tea", "tna", "efectiva_periodo"] = "tna"
    periodicidad_tasa: Literal[
        "mensual", "bimestral", "trimestral", "cuatrimestral", "semestral", "anual"
    ] = "anual"
    frecuencia_capitalizacion: Literal[
        "diaria", "mensual", "bimestral", "trimestral", "cuatrimestral", "semestral", "anual"
    ] = "mensual"
    base_dias: Literal[360, 365] = 365
    momento_aporte: Literal["inicio_periodo", "fin_periodo"] = "fin_periodo"
    inflacion_anual_percent: Annotated[
        Decimal, Field(ge=Decimal("-99.99"), le=Decimal("1000"))
    ] = Decimal("0")
    costo_mantenimiento_mensual: Annotated[
        Decimal, Field(ge=0, le=Decimal("1000000000"))
    ] = Decimal("0")
    comision_entrada_percent: Annotated[Decimal, Field(ge=0, le=Decimal("50"))] = Decimal("0")
    comision_salida_percent: Annotated[Decimal, Field(ge=0, le=Decimal("50"))] = Decimal("0")
    impuesto_ganancia_percent: Annotated[Decimal, Field(ge=0, le=Decimal("60"))] = Decimal("0")
    aporte_mensual: Annotated[Decimal, Field(ge=0, le=Decimal("1000000000000"))] = Decimal("0")
    moneda: Literal["PEN", "USD", "EUR"] = "PEN"

    @model_validator(mode="after")
    def one_rate_input(self):
        if self.tasa_percent is None and self.tasa_anual_percent is None:
            raise ValueError("Debes indicar tasa_percent")
        if self.tasa_percent is not None and self.tasa_anual_percent is not None:
            raise ValueError("Usa tasa_percent o tasa_anual_percent, no ambos")
        return self


class InvestmentSeriesPoint(BaseModel):
    mes: int
    capital_aportado: Decimal
    ganancia_acumulada: Decimal
    saldo: Decimal
    saldo_real: Decimal


class InvestmentSimulationResponse(BaseModel):
    moneda: Literal["PEN", "USD", "EUR"]
    capital_inicial: Decimal
    aporte_mensual: Decimal
    plazo_meses: int
    tasa_anual_percent: Decimal
    tipo_tasa: Literal["tea", "tna", "efectiva_periodo"]
    tasa_ingresada_percent: Decimal
    periodicidad_tasa: str
    frecuencia_capitalizacion: str
    base_dias: int
    tasa_efectiva_mensual_percent: Decimal
    tasa_efectiva_anual_percent: Decimal
    descripcion_tasa: str
    momento_aporte: Literal["inicio_periodo", "fin_periodo"]
    inflacion_anual_percent: Decimal
    costo_mantenimiento_mensual: Decimal
    total_aportado: Decimal
    total_aportado_valor_real: Decimal
    saldo_final_bruto: Decimal
    comision_entrada: Decimal
    comision_salida: Decimal
    costos_mantenimiento: Decimal
    impuestos_totales: Decimal
    costos_totales: Decimal
    ganancia_neta: Decimal
    saldo_final_neto: Decimal
    roi_neto_percent: Decimal
    saldo_final_real: Decimal
    ganancia_real: Decimal
    roi_real_percent: Decimal
    series: list[InvestmentSeriesPoint]
    advertencia: str


class TreasurySurplusResponse(BaseModel):
    calculable: bool
    motivo: str | None
    moneda: Literal["PEN", "USD", "EUR"]
    efectivo_total: Decimal | None
    efectivo_restringido: Decimal | None
    efectivo_no_restringido: Decimal | None
    saldo_minimo_proyectado: Decimal | None
    pasivo_corriente: Decimal | None
    factor_reserva_percent: Decimal
    reserva_operativa: Decimal | None
    metodo_reserva: str | None
    excedente_invertible: Decimal | None
    escenarios: dict[str, Decimal]
    advertencia: str


class SalesHistoryPoint(BaseModel):
    periodo: str
    ventas: Decimal


class SalesForecastPoint(BaseModel):
    periodo: str
    ventas_estimadas: Decimal
    limite_inferior: Decimal
    limite_superior: Decimal


class SalesForecastResponse(BaseModel):
    calculable: bool
    motivo: str | None
    horizonte_meses: int
    modelo: Literal["regresion_lineal_temporal", "persistencia"] | None
    confianza: Literal["baja", "media"] | None
    mae: Decimal | None
    mae_regresion: Decimal | None
    mae_persistencia: Decimal | None
    tendencia_mensual: Decimal | None
    total_pronosticado: Decimal | None
    total_historico_comparable: Decimal | None
    variacion_total_percent: Decimal | None
    historico: list[SalesHistoryPoint]
    pronostico: list[SalesForecastPoint]
    advertencia: str


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


@router.get("/{analysis_id}/treasury-surplus", response_model=TreasurySurplusResponse)
def treasury_surplus(
    analysis_id: str,
    actor: Annotated[str, Depends(get_current_user)],
    reserve_percent: Annotated[Decimal, Query(ge=0, le=100)] = Decimal("20"),
    moneda: Annotated[Literal["PEN", "USD", "EUR"], Query()] = "PEN",
) -> dict:
    analysis = _owned(analysis_id, actor)
    cifras = json.loads(analysis.get("cifras_json") or "{}")
    return calcular_excedente_tesoreria(cifras, reserve_percent, moneda)


@router.get("/{analysis_id}/sales-forecast", response_model=SalesForecastResponse)
def sales_forecast(
    analysis_id: str,
    actor: Annotated[str, Depends(get_current_user)],
    horizon_months: Annotated[int, Query(ge=1, le=12)] = 6,
) -> dict:
    analysis = _owned(analysis_id, actor)
    cifras = json.loads(analysis.get("cifras_json") or "{}")
    return pronosticar_ventas(cifras.get("ventas_mensuales"), horizon_months)


@router.post(
    "/{analysis_id}/investment-simulation",
    response_model=InvestmentSimulationResponse,
)
def investment_simulation(
    analysis_id: str,
    payload: InvestmentSimulationRequest,
    actor: Annotated[str, Depends(get_current_user)],
) -> dict:
    _owned(analysis_id, actor)
    try:
        rate = payload.tasa_percent
        rate_type = payload.tipo_tasa
        if rate is None:
            rate = payload.tasa_anual_percent
            rate_type = "tna"
        assert rate is not None
        return simular_inversion(
            capital_inicial=payload.capital_inicial,
            plazo_meses=payload.plazo_meses,
            tasa_anual_percent=rate,
            frecuencia_capitalizacion=payload.frecuencia_capitalizacion,
            comision_entrada_percent=payload.comision_entrada_percent,
            comision_salida_percent=payload.comision_salida_percent,
            impuesto_ganancia_percent=payload.impuesto_ganancia_percent,
            aporte_mensual=payload.aporte_mensual,
            moneda=payload.moneda,
            tipo_tasa=rate_type,
            periodicidad_tasa=payload.periodicidad_tasa,
            base_dias=payload.base_dias,
            momento_aporte=payload.momento_aporte,
            inflacion_anual_percent=payload.inflacion_anual_percent,
            costo_mantenimiento_mensual=payload.costo_mantenimiento_mensual,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
