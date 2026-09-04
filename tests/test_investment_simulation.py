"""SPEC-010: simulador integrado, determinístico y aislado por propietario."""

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.db.database as database
from backend.agent.financial_tools import (
    calcular_excedente_tesoreria,
    simular_inversion,
)
from backend.db.database import guardar_analisis
from backend.main import app
from frontend.dashboard import investment_evolution_chart, investment_series_rows


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "investment.db"))
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _analysis(owner: str = "analista", analysis_id: str = "investment-1") -> None:
    guardar_analisis(
        analysis_id=analysis_id,
        filename="estado.pdf",
        created_by=owner,
        cifras={
            "efectivo": 350000,
            "efectivo_restringido": 20000,
            "reserva_minima_operativa": 120000,
            "saldo_minimo_proyectado": 330000,
            "pasivo_corriente": 260000,
            "moneda": "PEN",
        },
        indicadores={},
        alertas=[],
        resumen="Prueba",
    )


def test_treasury_surplus_uses_document_values():
    result = calcular_excedente_tesoreria(
        {
            "efectivo": 350000,
            "efectivo_restringido": 20000,
            "reserva_minima_operativa": 120000,
            "saldo_minimo_proyectado": 330000,
            "pasivo_corriente": 260000,
            "moneda": "PEN",
        }
    )
    assert result["calculable"] is True
    assert result["efectivo_no_restringido"] == Decimal("330000.00")
    assert result["reserva_operativa"] == Decimal("120000.00")
    assert result["excedente_invertible"] == Decimal("210000.00")
    assert result["metodo_reserva"] == "reserva_documental"
    assert result["escenarios"]["prudente_30"] == Decimal("63000.00")


def test_treasury_surplus_missing_cash_is_not_zero():
    result = calcular_excedente_tesoreria({"pasivo_corriente": 50000})
    assert result["calculable"] is False
    assert result["excedente_invertible"] is None
    assert result["escenarios"] == {}
    assert "efectivo" in result["motivo"].lower()


def test_investment_simulation_exact_decimal_result():
    result = simular_inversion(
        capital_inicial=Decimal("10000"),
        plazo_meses=12,
        tasa_anual_percent=Decimal("12"),
        frecuencia_capitalizacion="mensual",
        moneda="PEN",
    )
    assert result["total_aportado"] == Decimal("10000.00")
    assert result["saldo_final_bruto"] == Decimal("11268.25")
    assert result["saldo_final_neto"] == Decimal("11268.25")
    assert result["ganancia_neta"] == Decimal("1268.25")
    assert result["roi_neto_percent"] == Decimal("12.68")
    assert len(result["series"]) == 13
    assert result["tipo_tasa"] == "tna"
    assert result["tasa_efectiva_mensual_percent"] == Decimal("1.000000")
    assert result["tasa_efectiva_anual_percent"] == Decimal("12.682503")
    assert "no representa" in result["advertencia"].lower()


def test_tea_and_bimonthly_effective_rate_are_converted_correctly():
    tea = simular_inversion(
        Decimal("1000"), 12, Decimal("12"), tipo_tasa="tea"
    )
    bimonthly = simular_inversion(
        Decimal("1000"),
        12,
        Decimal("2"),
        tipo_tasa="efectiva_periodo",
        periodicidad_tasa="bimestral",
    )

    assert tea["tasa_efectiva_anual_percent"] == Decimal("12.000000")
    assert tea["tasa_efectiva_mensual_percent"] == Decimal("0.948879")
    assert tea["saldo_final_neto"] == Decimal("1120.00")
    assert bimonthly["tasa_efectiva_mensual_percent"] == Decimal("0.995049")
    assert bimonthly["tasa_efectiva_anual_percent"] == Decimal("12.616242")


def test_contribution_timing_inflation_and_maintenance_are_traceable():
    end = simular_inversion(
        Decimal("1000"), 1, Decimal("12"), aporte_mensual=Decimal("100")
    )
    beginning = simular_inversion(
        Decimal("1000"),
        1,
        Decimal("12"),
        aporte_mensual=Decimal("100"),
        momento_aporte="inicio_periodo",
    )
    real = simular_inversion(
        Decimal("1000"),
        12,
        Decimal("12"),
        tipo_tasa="tea",
        inflacion_anual_percent=Decimal("12"),
        costo_mantenimiento_mensual=Decimal("10"),
    )

    assert end["saldo_final_neto"] == Decimal("1110.00")
    assert beginning["saldo_final_neto"] == Decimal("1111.00")
    assert real["costos_mantenimiento"] == Decimal("120.00")
    assert real["saldo_final_real"] < real["saldo_final_neto"]
    assert real["roi_real_percent"] < real["roi_neto_percent"]


def test_investment_function_rejects_invalid_frequency():
    with pytest.raises(ValueError, match="Frecuencia"):
        simular_inversion(Decimal("1000"), 12, Decimal("5"), "semanal")


def test_api_requires_auth_validates_and_isolates_owner(client: TestClient):
    analyst_headers = _login(client, "analista", "analista123")
    admin_headers = _login(client, "admin", "admin123")
    _analysis()

    missing_auth = client.get("/analyses/investment-1/treasury-surplus")
    assert missing_auth.status_code == 401

    foreign_analysis = client.get(
        "/analyses/investment-1/treasury-surplus", headers=admin_headers
    )
    assert foreign_analysis.status_code == 404

    invalid_reserve = client.get(
        "/analyses/investment-1/treasury-surplus?reserve_percent=101",
        headers=analyst_headers,
    )
    assert invalid_reserve.status_code == 422

    invalid_frequency = client.post(
        "/analyses/investment-1/investment-simulation",
        headers=analyst_headers,
        json={
            "capital_inicial": "10000",
            "plazo_meses": 12,
            "tasa_anual_percent": "10",
            "frecuencia_capitalizacion": "semanal",
        },
    )
    assert invalid_frequency.status_code == 422


def test_api_returns_surplus_and_simulation(client: TestClient):
    headers = _login(client, "analista", "analista123")
    _analysis()
    surplus = client.get(
        "/analyses/investment-1/treasury-surplus?reserve_percent=20&moneda=PEN",
        headers=headers,
    )
    assert surplus.status_code == 200, surplus.text
    assert surplus.json()["excedente_invertible"] == "210000.00"

    simulation = client.post(
        "/analyses/investment-1/investment-simulation",
        headers=headers,
        json={
            "capital_inicial": "10000",
            "plazo_meses": 12,
            "tasa_anual_percent": "12",
            "frecuencia_capitalizacion": "mensual",
            "moneda": "PEN",
        },
    )
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["saldo_final_neto"] == "11268.25"

    advanced = client.post(
        "/analyses/investment-1/investment-simulation",
        headers=headers,
        json={
            "capital_inicial": "10000",
            "plazo_meses": 12,
            "tasa_percent": "2",
            "tipo_tasa": "efectiva_periodo",
            "periodicidad_tasa": "bimestral",
            "inflacion_anual_percent": "3",
            "costo_mantenimiento_mensual": "10",
            "momento_aporte": "inicio_periodo",
            "moneda": "PEN",
        },
    )
    assert advanced.status_code == 200, advanced.text
    assert advanced.json()["tipo_tasa"] == "efectiva_periodo"
    assert advanced.json()["tasa_efectiva_anual_percent"] == "12.616242"
    assert Decimal(advanced.json()["saldo_final_real"]) < Decimal(
        advanced.json()["saldo_final_neto"]
    )

    missing_rate = client.post(
        "/analyses/investment-1/investment-simulation",
        headers=headers,
        json={"capital_inicial": "10000", "plazo_meses": 12},
    )
    assert missing_rate.status_code == 422


def test_investment_chart_has_no_vegalite_params():
    rows = investment_series_rows(
        {
            "series": [
                {
                    "mes": 0,
                    "capital_aportado": "10000.00",
                    "ganancia_acumulada": "-20.00",
                    "saldo": "9980.00",
                    "dato_no_permitido": "privado",
                },
                {
                    "mes": 1,
                    "capital_aportado": "10000.00",
                    "ganancia_acumulada": "80.00",
                    "saldo": "10080.00",
                },
            ]
        }
    )
    assert all("dato_no_permitido" not in row for row in rows)
    spec = investment_evolution_chart(rows).to_dict()
    assert len(spec["layer"]) == 2
    assert "params" not in spec


def test_investment_chart_adds_allowlisted_real_balance():
    rows = investment_series_rows(
        {
            "series": [
                {
                    "mes": 0,
                    "capital_aportado": "10000.00",
                    "ganancia_acumulada": "0.00",
                    "saldo": "10000.00",
                    "saldo_real": "10000.00",
                    "texto_pdf": "no debe salir",
                },
                {
                    "mes": 1,
                    "capital_aportado": "10000.00",
                    "ganancia_acumulada": "100.00",
                    "saldo": "10100.00",
                    "saldo_real": "10070.00",
                },
            ]
        }
    )
    assert all("texto_pdf" not in row for row in rows)
    spec = investment_evolution_chart(rows).to_dict()
    assert len(spec["layer"]) == 3
    assert "params" not in spec
