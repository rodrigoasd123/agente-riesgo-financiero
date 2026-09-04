"""SPEC-013: pronóstico temporal explicable y aislado por propietario."""

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.db.database as database
from backend.agent.sales_forecasting import pronosticar_ventas
from backend.db.database import guardar_analisis
from backend.main import app
from frontend.dashboard import sales_forecast_chart, sales_forecast_rows


def _history(values: list[int], start_year: int = 2025, start_month: int = 1) -> list[dict]:
    rows = []
    for offset, value in enumerate(values):
        absolute = start_year * 12 + start_month - 1 + offset
        rows.append(
            {
                "mes": "Mes",
                "periodo": f"{absolute // 12:04d}-{absolute % 12 + 1:02d}",
                "ventas": value,
            }
        )
    return rows


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "forecast.db"))
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_linear_backtesting_forecasts_six_consecutive_months():
    result = pronosticar_ventas(_history([100, 110, 120, 130, 140, 150]), 6)

    assert result["calculable"] is True
    assert result["modelo"] == "regresion_lineal_temporal"
    assert result["mae_regresion"] == Decimal("0.00")
    assert result["mae_persistencia"] == Decimal("10.00")
    assert [row["periodo"] for row in result["pronostico"]] == [
        "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"
    ]
    assert [row["ventas_estimadas"] for row in result["pronostico"]] == [
        Decimal("160.00"), Decimal("170.00"), Decimal("180.00"),
        Decimal("190.00"), Decimal("200.00"), Decimal("210.00"),
    ]
    assert all(
        row["limite_inferior"] <= row["ventas_estimadas"] <= row["limite_superior"]
        for row in result["pronostico"]
    )


def test_insufficient_or_gapped_history_is_not_invented():
    short = pronosticar_ventas(_history([100, 110, 120, 130, 140]), 6)
    gapped = _history([100, 110, 120, 130, 140, 150])
    gapped[3]["periodo"] = "2025-10"
    gap_result = pronosticar_ventas(gapped, 6)

    assert short["calculable"] is False
    assert short["pronostico"] == []
    assert gap_result["calculable"] is False
    assert "consecutivos" in gap_result["motivo"]


def test_forecast_api_requires_auth_isolates_owner_and_validates_horizon(client: TestClient):
    analyst = _login(client, "analista", "analista123")
    admin = _login(client, "admin", "admin123")
    guardar_analisis(
        analysis_id="forecast-1",
        filename="ventas.pdf",
        created_by="analista",
        cifras={"ventas_mensuales": _history(list(range(100, 220, 10))), "moneda": "PEN"},
        indicadores={},
        alertas=[],
        resumen="Prueba",
    )

    assert client.get("/analyses/forecast-1/sales-forecast").status_code == 401
    assert client.get(
        "/analyses/forecast-1/sales-forecast", headers=admin
    ).status_code == 404
    assert client.get(
        "/analyses/forecast-1/sales-forecast?horizon_months=13", headers=analyst
    ).status_code == 422

    response = client.get(
        "/analyses/forecast-1/sales-forecast?horizon_months=6", headers=analyst
    )
    assert response.status_code == 200, response.text
    assert response.json()["calculable"] is True
    assert len(response.json()["pronostico"]) == 6


def test_forecast_chart_is_allowlisted_and_has_no_params():
    rows = sales_forecast_rows(
        {
            "historico": [{"periodo": "2025-12", "ventas": "100", "texto": "privado"}],
            "pronostico": [
                {
                    "periodo": "2026-01",
                    "ventas_estimadas": "110",
                    "limite_inferior": "90",
                    "limite_superior": "130",
                    "prompt": "privado",
                }
            ],
        }
    )
    assert all("texto" not in row and "prompt" not in row for row in rows)
    spec = sales_forecast_chart(rows).to_dict()
    assert len(spec["layer"]) == 3
    assert "params" not in spec
