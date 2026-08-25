"""
Calculo de indicadores financieros (liquidez, endeudamiento,
rentabilidad) y variacion entre periodos, a partir de las cifras
extraidas del estado financiero.

Logica pura, sin dependencias de LangGraph ni de Gemini, para poder
probarla con pytest de forma aislada (ver tests/test_indicadores.py).
"""
from typing import Optional


def _div(numerador: Optional[float], denominador: Optional[float]) -> Optional[float]:
    """Division segura: devuelve None si falta algun dato o el divisor es 0."""
    if numerador is None or denominador in (None, 0):
        return None
    return round(numerador / denominador, 4)


def calcular_indicadores(cifras: dict) -> dict:
    activo_corriente = cifras.get("activo_corriente")
    pasivo_corriente = cifras.get("pasivo_corriente")
    inventarios = cifras.get("inventarios") or 0
    activo_total = cifras.get("activo_total")
    pasivo_total = cifras.get("pasivo_total")
    patrimonio = cifras.get("patrimonio")
    ventas = cifras.get("ventas")
    ventas_anterior = cifras.get("ventas_periodo_anterior")
    utilidad_neta = cifras.get("utilidad_neta")
    utilidad_operativa = cifras.get("utilidad_operativa")
    gastos_financieros = cifras.get("gastos_financieros")

    activo_corriente_sin_inv = (
        activo_corriente - inventarios if activo_corriente is not None else None
    )

    variacion_ventas_pct = None
    if ventas is not None and ventas_anterior not in (None, 0):
        variacion_ventas_pct = round(((ventas - ventas_anterior) / ventas_anterior) * 100, 2)

    return {
        # --- Liquidez ---
        "liquidez_corriente": _div(activo_corriente, pasivo_corriente),
        "prueba_acida": _div(activo_corriente_sin_inv, pasivo_corriente),
        "capital_trabajo": (
            round(activo_corriente - pasivo_corriente, 2)
            if activo_corriente is not None and pasivo_corriente is not None
            else None
        ),
        # --- Endeudamiento ---
        "endeudamiento_total": _div(pasivo_total, activo_total),
        "endeudamiento_patrimonial": _div(pasivo_total, patrimonio),
        "cobertura_intereses": _div(utilidad_operativa, gastos_financieros),
        # --- Rentabilidad ---
        "margen_neto": _div(utilidad_neta, ventas),
        "roa": _div(utilidad_neta, activo_total),
        "roe": _div(utilidad_neta, patrimonio),
        # --- Variacion entre periodos ---
        "variacion_ventas_pct": variacion_ventas_pct,
    }
