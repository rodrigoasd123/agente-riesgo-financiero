"""Pronóstico temporal explicable de ventas mensuales, sin servicios externos."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP, localcontext


MONEY = Decimal("0.01")
RATE = Decimal("0.01")
PERIOD_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
WARNING = (
    "Pronóstico estadístico orientativo basado únicamente en la historia mensual "
    "disponible; no garantiza ventas futuras ni reemplaza un presupuesto aprobado."
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE, rounding=ROUND_HALF_UP)


def _next_period(period: str, offset: int = 1) -> str:
    year, month = map(int, period.split("-"))
    absolute = year * 12 + month - 1 + offset
    return f"{absolute // 12:04d}-{absolute % 12 + 1:02d}"


def _fit_linear(values: list[Decimal]) -> tuple[Decimal, Decimal]:
    count = Decimal(len(values))
    x_mean = Decimal(len(values) - 1) / Decimal(2)
    y_mean = sum(values, Decimal(0)) / count
    denominator = sum(
        ((Decimal(index) - x_mean) ** 2 for index in range(len(values))),
        Decimal(0),
    )
    if denominator == 0:
        return y_mean, Decimal(0)
    slope = sum(
        (
            (Decimal(index) - x_mean) * (value - y_mean)
            for index, value in enumerate(values)
        ),
        Decimal(0),
    ) / denominator
    return y_mean - slope * x_mean, slope


def _parse_history(raw_points: object) -> tuple[list[dict], str | None]:
    if not isinstance(raw_points, list):
        return [], "El documento no contiene una serie mensual estructurada."
    by_period: dict[str, Decimal] = {}
    for raw in raw_points:
        if not isinstance(raw, dict):
            return [], "La serie mensual contiene una fila inválida."
        period = str(raw.get("periodo") or "").strip()
        if not PERIOD_RE.fullmatch(period) or period in by_period:
            return [], "Los períodos mensuales son inválidos o están duplicados."
        try:
            value = Decimal(str(raw.get("ventas")))
        except (ValueError, TypeError):
            return [], "La serie mensual contiene una venta no numérica."
        if not value.is_finite() or value < 0:
            return [], "Las ventas mensuales deben ser importes no negativos."
        by_period[period] = value

    periods = sorted(by_period)
    if len(periods) < 6:
        return [], "Se requieren al menos seis meses consecutivos para pronosticar."
    for index in range(1, len(periods)):
        if periods[index] != _next_period(periods[index - 1]):
            return [], "La historia debe contener meses consecutivos sin vacíos."
    return [
        {"periodo": period, "ventas": by_period[period]} for period in periods[-120:]
    ], None


def pronosticar_ventas(raw_points: object, horizonte_meses: int = 6) -> dict:
    """Selecciona por backtesting entre tendencia lineal y persistencia."""
    if horizonte_meses < 1 or horizonte_meses > 12:
        raise ValueError("El horizonte debe estar entre 1 y 12 meses.")
    history, error = _parse_history(raw_points)
    base = {
        "calculable": False,
        "motivo": error,
        "horizonte_meses": horizonte_meses,
        "modelo": None,
        "confianza": None,
        "mae": None,
        "mae_regresion": None,
        "mae_persistencia": None,
        "tendencia_mensual": None,
        "total_pronosticado": None,
        "total_historico_comparable": None,
        "variacion_total_percent": None,
        "historico": [],
        "pronostico": [],
        "advertencia": WARNING,
    }
    if error:
        return base

    values = [item["ventas"] for item in history]
    regression_errors: list[Decimal] = []
    persistence_errors: list[Decimal] = []
    for target in range(4, len(values)):
        intercept, slope = _fit_linear(values[:target])
        regression_errors.append(abs(values[target] - (intercept + slope * Decimal(target))))
        persistence_errors.append(abs(values[target] - values[target - 1]))
    mae_regression = sum(regression_errors, Decimal(0)) / Decimal(len(regression_errors))
    mae_persistence = sum(persistence_errors, Decimal(0)) / Decimal(len(persistence_errors))
    model = "regresion_lineal_temporal" if mae_regression <= mae_persistence else "persistencia"
    selected_mae = min(mae_regression, mae_persistence)

    intercept, slope = _fit_linear(values)
    if model == "regresion_lineal_temporal":
        residuals = [
            value - (intercept + slope * Decimal(index))
            for index, value in enumerate(values)
        ]
        degrees = max(1, len(values) - 2)
    else:
        residuals = [values[index] - values[index - 1] for index in range(1, len(values))]
        degrees = max(1, len(residuals))
    with localcontext() as context:
        context.prec = 40
        residual_std = (
            sum((item * item for item in residuals), Decimal(0)) / Decimal(degrees)
        ).sqrt()

    forecast = []
    last_period = history[-1]["periodo"]
    for step in range(1, horizonte_meses + 1):
        raw_prediction = (
            intercept + slope * Decimal(len(values) + step - 1)
            if model == "regresion_lineal_temporal"
            else values[-1]
        )
        prediction = max(Decimal(0), raw_prediction)
        with localcontext() as context:
            context.prec = 40
            widening = (Decimal(1) + Decimal(step) / Decimal(len(values))).sqrt()
        margin = Decimal("1.281552") * residual_std * widening
        forecast.append(
            {
                "periodo": _next_period(last_period, step),
                "ventas_estimadas": _money(prediction),
                "limite_inferior": _money(max(Decimal(0), prediction - margin)),
                "limite_superior": _money(prediction + margin),
            }
        )

    comparable_count = min(horizonte_meses, len(values))
    historical_total = sum(values[-comparable_count:], Decimal(0))
    forecast_total = sum((item["ventas_estimadas"] for item in forecast), Decimal(0))
    variation = (
        (forecast_total / historical_total - Decimal(1)) * Decimal(100)
        if historical_total > 0
        else None
    )
    base.update(
        {
            "calculable": True,
            "motivo": None,
            "modelo": model,
            "confianza": "baja" if len(values) < 18 else "media",
            "mae": _money(selected_mae),
            "mae_regresion": _money(mae_regression),
            "mae_persistencia": _money(mae_persistence),
            "tendencia_mensual": _money(slope),
            "total_pronosticado": _money(forecast_total),
            "total_historico_comparable": _money(historical_total),
            "variacion_total_percent": _rate(variation) if variation is not None else None,
            "historico": [
                {"periodo": item["periodo"], "ventas": _money(item["ventas"])}
                for item in history
            ],
            "pronostico": forecast,
        }
    )
    return base
