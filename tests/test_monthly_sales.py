"""SPEC-011: extracción y visualización temporal de ventas mensuales."""

from backend.agent.pdf_reader import extraer_cifras_fallback
from frontend.dashboard import sales_rows, sales_trend_chart


def test_fallback_extracts_monthly_sales_without_inventing_missing_months():
    text = """
    Ventas netas (2025): 210,000
    Enero 2025: 100,000 Base
    Febrero 2025: 110,000 +10.0%
    """
    cifras = extraer_cifras_fallback(text)

    assert cifras["ventas_mensuales"] == [
        {"mes": "Enero", "periodo": "2025-01", "ventas": 100000.0},
        {"mes": "Febrero", "periodo": "2025-02", "ventas": 110000.0},
    ]


def test_dashboard_prefers_monthly_series_and_allowlists_fields():
    rows = sales_rows(
        {
            "ventas": 210000,
            "ventas_periodo_anterior": 200000,
            "ventas_mensuales": [
                {"mes": "Enero", "periodo": "2025-01", "ventas": 100000, "secreto": "x"},
                {"mes": "Febrero", "periodo": "2025-02", "ventas": 110000},
            ],
        }
    )

    assert [row["periodo"] for row in rows] == ["Ene 2025", "Feb 2025"]
    assert round(rows[1]["variacion_pct"], 2) == 10.0
    assert all("secreto" not in row for row in rows)
    spec = sales_trend_chart(rows).to_dict()
    assert spec["mark"]["type"] == "line"
    assert "params" not in spec


def test_dashboard_keeps_two_period_fallback_for_old_documents():
    rows = sales_rows({"ventas_periodo_anterior": 200000, "ventas": 210000})
    assert [row["periodo"] for row in rows] == ["Periodo anterior", "Periodo actual"]
    assert all("variacion_pct" not in row for row in rows)
