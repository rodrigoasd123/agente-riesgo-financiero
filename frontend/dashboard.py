"""Datos allowlisted y gráficos deterministas para el dashboard financiero."""

from __future__ import annotations

import math
from typing import Any

import altair as alt


FIGURE_LABELS = {
    "pasivo_total": "Pasivo total",
    "patrimonio": "Patrimonio",
    "ventas_periodo_anterior": "Ventas periodo anterior",
    "ventas": "Ventas periodo actual",
    "utilidad_operativa": "Utilidad operativa",
    "utilidad_neta": "Utilidad neta",
}

MULTIPLE_INDICATORS = {
    "liquidez_corriente": "Liquidez corriente",
    "prueba_acida": "Prueba ácida",
    "cobertura_intereses": "Cobertura de intereses",
}

PERCENT_INDICATORS = {
    "endeudamiento_total": "Endeudamiento total",
    "endeudamiento_patrimonial": "Deuda / patrimonio",
    "margen_neto": "Margen neto",
    "roa": "ROA",
    "roe": "ROE",
}

ALERT_CODES = {
    "LIQUIDEZ_BAJA",
    "PRUEBA_ACIDA_BAJA",
    "ENDEUDAMIENTO_ALTO",
    "COBERTURA_INTERESES_BAJA",
    "PERDIDAS_NETAS",
    "CAIDA_INGRESOS",
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def numeric_value(value: Any) -> float | None:
    """Convierte sólo escalares numéricos finitos para KPI y gráficos."""
    return _number(value)


def funding_rows(cifras: dict) -> list[dict]:
    rows = []
    for key in ("pasivo_total", "patrimonio"):
        value = _number(cifras.get(key))
        if value is not None and value >= 0:
            rows.append({"componente": FIGURE_LABELS[key], "valor": value})
    return rows if len(rows) == 2 and any(row["valor"] > 0 for row in rows) else []


def sales_rows(cifras: dict) -> list[dict]:
    labels = {"ventas_periodo_anterior": "Periodo anterior", "ventas": "Periodo actual"}
    rows = []
    for order, key in enumerate(("ventas_periodo_anterior", "ventas")):
        value = _number(cifras.get(key))
        if value is not None:
            rows.append({"periodo": labels[key], "valor": value, "orden": order})
    return rows


def results_rows(cifras: dict) -> list[dict]:
    rows = []
    for order, key in enumerate(("ventas", "utilidad_operativa", "utilidad_neta")):
        value = _number(cifras.get(key))
        if value is not None:
            rows.append({"concepto": FIGURE_LABELS[key], "valor": value, "orden": order})
    return rows


def indicator_rows(indicadores: dict) -> tuple[list[dict], list[dict]]:
    multiples = []
    percentages = []
    for key, label in MULTIPLE_INDICATORS.items():
        value = _number(indicadores.get(key))
        if value is not None:
            multiples.append({"indicador": label, "valor": value, "unidad": "veces"})
    for key, label in PERCENT_INDICATORS.items():
        value = _number(indicadores.get(key))
        if value is not None:
            percentages.append({"indicador": label, "valor": value * 100, "unidad": "%"})
    variation = _number(indicadores.get("variacion_ventas_pct"))
    if variation is not None:
        percentages.append({"indicador": "Variación de ventas", "valor": variation, "unidad": "%"})
    return multiples, percentages


def alert_rows(alertas: list[dict]) -> list[dict]:
    allowlisted = []
    for alert in alertas:
        severity = str(alert.get("severidad") or "").lower()
        code = str(alert.get("codigo") or "").strip()[:64]
        if severity in {"alta", "media", "baja"} and code in ALERT_CODES:
            allowlisted.append({"codigo": code, "severidad": severity})
    return allowlisted


def cashflow_rows(projection: dict | None) -> list[dict]:
    rows = []
    for raw in (projection or {}).get("flujos", []):
        period = _number(raw.get("periodo"))
        flow = _number(raw.get("flujo"))
        cumulative = _number(raw.get("flujo_acumulado"))
        if period is not None and flow is not None and cumulative is not None:
            rows.append(
                {
                    "periodo": int(period),
                    "flujo": flow,
                    "flujo_acumulado": cumulative,
                }
            )
    return rows


def funding_chart(rows: list[dict]) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=rows))
        .mark_arc(innerRadius=55, outerRadius=105)
        .encode(
            theta=alt.Theta("valor:Q"),
            color=alt.Color(
                "componente:N",
                scale=alt.Scale(range=["#ef6c63", "#35a77a"]),
                legend=alt.Legend(title=None),
            ),
            tooltip=[alt.Tooltip("componente:N"), alt.Tooltip("valor:Q", format=",.2f")],
        )
        .properties(title="Financiamiento de los activos", height=280)
    )


def ordered_bar_chart(rows: list[dict], category: str, title: str) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X(f"{category}:N", sort=alt.SortField("orden"), title=None),
            y=alt.Y("valor:Q", title="Importe"),
            color=alt.condition("datum.valor >= 0", alt.value("#3976d2"), alt.value("#d95555")),
            tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip("valor:Q", format=",.2f")],
        )
        .properties(title=title, height=280)
        .interactive()
    )


def indicator_chart(rows: list[dict], title: str, unit: str) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("indicador:N", sort="-x", title=None),
            x=alt.X("valor:Q", title=unit),
            color=alt.condition("datum.valor >= 0", alt.value("#4a78c2"), alt.value("#d95555")),
            tooltip=[
                alt.Tooltip("indicador:N"),
                alt.Tooltip("valor:Q", format=".2f"),
                alt.Tooltip("unidad:N"),
            ],
        )
        .properties(title=title, height=max(220, len(rows) * 42))
        .interactive()
    )


def alerts_chart(rows: list[dict]) -> alt.Chart:
    colors = alt.Scale(domain=["alta", "media", "baja"], range=["#d95555", "#e3a52f", "#3b82c4"])
    return (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("codigo:N", title=None),
            x=alt.X("count():Q", title="Cantidad"),
            color=alt.Color("severidad:N", scale=colors, legend=alt.Legend(title="Severidad")),
            tooltip=[alt.Tooltip("codigo:N"), alt.Tooltip("severidad:N"), alt.Tooltip("count():Q")],
        )
        .properties(title="Mapa de alertas", height=max(220, len(rows) * 38))
    )


def cashflow_chart(rows: list[dict]) -> alt.LayerChart:
    data = alt.Data(values=rows)
    bars = alt.Chart(data).mark_bar(opacity=0.7).encode(
        x=alt.X("periodo:O", title="Periodo"),
        y=alt.Y("flujo:Q", title="Flujo del periodo"),
        color=alt.condition("datum.flujo >= 0", alt.value("#35a77a"), alt.value("#d95555")),
        tooltip=[alt.Tooltip("periodo:O"), alt.Tooltip("flujo:Q", format=",.2f")],
    )
    line = alt.Chart(data).mark_line(point=True, color="#f1b53a", strokeWidth=3).encode(
        x=alt.X("periodo:O"),
        y=alt.Y("flujo_acumulado:Q", title="Flujo acumulado"),
        tooltip=[alt.Tooltip("periodo:O"), alt.Tooltip("flujo_acumulado:Q", format=",.2f")],
    )
    return alt.layer(bars, line).resolve_scale(y="independent").properties(
        title="Flujo del periodo y acumulado", height=320
    )


def investment_series_rows(simulation_result: dict | None) -> list[dict]:
    rows = []
    for item in (simulation_result or {}).get("series", []):
        mes = _number(item.get("mes"))
        capital = _number(item.get("capital_aportado"))
        intereses = _number(item.get("intereses_acumulados"))
        saldo = _number(item.get("saldo"))
        if mes is not None and capital is not None and intereses is not None and saldo is not None:
            rows.append({
                "mes": int(mes),
                "capital_aportado": capital,
                "intereses_acumulados": intereses,
                "saldo": saldo,
            })
    return rows


def investment_evolution_chart(rows: list[dict]) -> alt.LayerChart:
    data = alt.Data(values=rows)
    capital_area = alt.Chart(data).mark_area(opacity=0.6, color="#3976d2").encode(
        x=alt.X("mes:O", title="Mes"),
        y=alt.Y("capital_aportado:Q", title="Importe Acumulado ($)"),
        tooltip=[alt.Tooltip("mes:O", title="Mes"), alt.Tooltip("capital_aportado:Q", title="Capital Aportado", format=",.2f")],
    )
    saldo_line = alt.Chart(data).mark_line(color="#2ca02c", strokeWidth=3).encode(
        x=alt.X("mes:O", title="Mes"),
        y=alt.Y("saldo:Q", title="Saldo Total ($)"),
        tooltip=[alt.Tooltip("mes:O", title="Mes"), alt.Tooltip("saldo:Q", title="Saldo Total con Rendimientos", format=",.2f")],
    )
    return alt.layer(capital_area, saldo_line).properties(
        title="Evolución del Patrimonio (Capital Aportado vs Saldo Total)", height=320
    ).interactive()

