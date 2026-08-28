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


def _style_chart(chart):
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#50677d",
            titleColor="#718398",
            gridColor="#e6edf3",
            domainColor="#dbe5ee",
            labelFont="Segoe UI",
            titleFont="Segoe UI",
        )
        .configure_title(
            color="#102235",
            font="Segoe UI",
            fontSize=16,
            fontWeight=600,
            anchor="start",
            offset=18,
        )
        .configure_legend(labelColor="#50677d", titleColor="#718398")
    )


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


def _with_direction(rows: list[dict], value_key: str) -> list[dict]:
    """Añade una categoría estable para colorear barras en Vega-Lite."""
    return [
        {
            **row,
            "_sentido": "positivo" if float(row[value_key]) >= 0 else "negativo",
        }
        for row in rows
    ]


def _direction_color(positive_color: str = "#0d9488") -> alt.Color:
    return alt.Color(
        "_sentido:N",
        scale=alt.Scale(
            domain=["positivo", "negativo"],
            range=[positive_color, "#d9535f"],
        ),
        legend=None,
    )


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
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_arc(innerRadius=55, outerRadius=105)
        .encode(
            theta=alt.Theta("valor:Q"),
            color=alt.Color(
                "componente:N",
                scale=alt.Scale(range=["#0f766e", "#22d3ee"]),
                legend=alt.Legend(title=None),
            ),
            tooltip=[alt.Tooltip("componente:N"), alt.Tooltip("valor:Q", format=",.2f")],
        )
        .properties(title="Financiamiento de los activos", height=280)
    )
    return _style_chart(chart)


def ordered_bar_chart(rows: list[dict], category: str, title: str) -> alt.Chart:
    chart_rows = _with_direction(rows, "valor")
    chart = (
        alt.Chart(alt.Data(values=chart_rows))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X(f"{category}:N", sort=alt.SortField("orden"), title=None),
            y=alt.Y("valor:Q", title="Importe"),
            color=_direction_color(),
            tooltip=[alt.Tooltip(f"{category}:N"), alt.Tooltip("valor:Q", format=",.2f")],
        )
        .properties(title=title, height=280)
    )
    return _style_chart(chart)


def indicator_chart(rows: list[dict], title: str, unit: str) -> alt.Chart:
    chart_rows = _with_direction(rows, "valor")
    chart = (
        alt.Chart(alt.Data(values=chart_rows))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("indicador:N", sort="-x", title=None),
            x=alt.X("valor:Q", title=unit),
            color=_direction_color("#168fa0"),
            tooltip=[
                alt.Tooltip("indicador:N"),
                alt.Tooltip("valor:Q", format=".2f"),
                alt.Tooltip("unidad:N"),
            ],
        )
        .properties(title=title, height=max(220, len(rows) * 42))
    )
    return _style_chart(chart)


def alerts_chart(rows: list[dict]) -> alt.Chart:
    colors = alt.Scale(domain=["alta", "media", "baja"], range=["#d9535f", "#d89a22", "#168fa0"])
    chart = (
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
    return _style_chart(chart)


def cashflow_chart(rows: list[dict]) -> alt.LayerChart:
    data = alt.Data(values=_with_direction(rows, "flujo"))
    bars = alt.Chart(data).mark_bar(opacity=0.7).encode(
        x=alt.X("periodo:O", title="Periodo"),
        y=alt.Y("flujo:Q", title="Flujo del periodo"),
        color=_direction_color(),
        tooltip=[alt.Tooltip("periodo:O"), alt.Tooltip("flujo:Q", format=",.2f")],
    )
    line = alt.Chart(data).mark_line(point=True, color="#d89a22", strokeWidth=3).encode(
        x=alt.X("periodo:O"),
        y=alt.Y("flujo_acumulado:Q", title="Flujo acumulado"),
        tooltip=[alt.Tooltip("periodo:O"), alt.Tooltip("flujo_acumulado:Q", format=",.2f")],
    )
    chart = alt.layer(bars, line).resolve_scale(y="independent").properties(
        title="Flujo del periodo y acumulado", height=320
    )
    return _style_chart(chart)
