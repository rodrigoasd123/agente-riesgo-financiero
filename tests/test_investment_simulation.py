from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.agent.financial_tools import (
    calcular_excedente_tesoreria,
    simular_inversion,
)
from backend.auth.security import create_access_token, issue_access_token
from backend.db.database import guardar_analisis, init_db
from backend.main import app


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sim.db"
    monkeypatch.setattr("backend.config.DB_PATH", str(test_db))
    monkeypatch.setattr("backend.db.database.DB_PATH", str(test_db))
    init_db()


def test_calcular_excedente_tesoreria():
    cifras = {
        "efectivo": 100000.0,
        "pasivo_corriente": 50000.0,
    }
    res = calcular_excedente_tesoreria(cifras, factor_reserva_percent=Decimal("20"))
    assert res["efectivo_total"] == Decimal("100000.00")
    assert res["pasivo_corriente"] == Decimal("50000.00")
    assert res["reserva_operativa"] == Decimal("10000.00")
    assert res["excedente_invertible"] == Decimal("90000.00")
    assert res["perfiles"]["conservador"] == Decimal("27000.00")
    assert res["perfiles"]["moderado"] == Decimal("54000.00")
    assert res["perfiles"]["dinamico"] == Decimal("81000.00")


def test_calcular_excedente_tesoreria_cero_o_negativo():
    cifras = {
        "efectivo": 5000.0,
        "pasivo_corriente": 50000.0,
    }
    res = calcular_excedente_tesoreria(cifras, factor_reserva_percent=Decimal("20"))
    assert res["reserva_operativa"] == Decimal("10000.00")
    assert res["excedente_invertible"] == Decimal("0.00")
    assert res["perfiles"]["conservador"] == Decimal("0.00")


def test_simular_inversion_basico():
    res = simular_inversion(
        capital_inicial=Decimal("10000"),
        plazo_meses=12,
        tasa_anual_percent=Decimal("12"),
        frecuencia_capitalizacion="mensual",
        comision_entrada_percent=Decimal("1"),
        comision_salida_percent=Decimal("1"),
        impuesto_ganancia_percent=Decimal("5"),
        aporte_mensual=Decimal("0"),
    )
    assert res["total_aportado"] == Decimal("10000.00")
    assert res["saldo_final_bruto"] > Decimal("10000.00")
    assert res["comisiones_totales"] > Decimal("100.00")
    assert res["impuestos_totales"] >= Decimal("0.00")
    assert res["ganancia_neta"] > Decimal("0.00")
    assert len(res["series"]) == 13  # mes 0 al 12


def test_simular_inversion_con_aportes_y_frecuencias():
    for freq in ("diaria", "mensual", "trimestral", "semestral", "anual"):
        res = simular_inversion(
            capital_inicial=Decimal("5000"),
            plazo_meses=24,
            tasa_anual_percent=Decimal("8"),
            frecuencia_capitalizacion=freq,
            aporte_mensual=Decimal("500"),
        )
        assert res["total_aportado"] == Decimal("17000.00")  # 5000 + 500*24
        assert res["saldo_final_bruto"] > Decimal("17000.00")
        assert len(res["series"]) == 25


def test_simular_inversion_validaciones():
    with pytest.raises(ValueError):
        simular_inversion(Decimal("1000"), plazo_meses=0, tasa_anual_percent=Decimal("5"))
    with pytest.raises(ValueError):
        simular_inversion(Decimal("-1000"), plazo_meses=12, tasa_anual_percent=Decimal("5"))


def test_api_surplus_and_investment_simulation():
    client = TestClient(app)
    token = issue_access_token("analista", "analyst")
    headers = {"Authorization": f"Bearer {token}"}

    guardar_analisis(
        analysis_id="sim-test-1",
        filename="test.pdf",
        created_by="analista",
        cifras={"efectivo": 80000.0, "pasivo_corriente": 30000.0},
        indicadores={},
        alertas=[],
        resumen="Test",
    )

    # 1. Test surplus endpoint
    res_surplus = client.get("/analyses/sim-test-1/treasury-surplus?reserve_percent=20", headers=headers)
    assert res_surplus.status_code == 200
    data_surplus = res_surplus.json()
    assert float(data_surplus["efectivo_total"]) == 80000.0
    assert float(data_surplus["reserva_operativa"]) == 6000.0
    assert float(data_surplus["excedente_invertible"]) == 74000.0

    # 2. Test simulation endpoint
    sim_payload = {
        "capital_inicial": "50000",
        "plazo_meses": 12,
        "tasa_anual_percent": "10",
        "frecuencia_capitalizacion": "mensual",
        "comision_entrada_percent": "0.2",
        "comision_salida_percent": "0.2",
        "impuesto_ganancia_percent": "5",
        "aporte_mensual": "1000",
    }
    res_sim = client.post("/analyses/sim-test-1/investment-simulation", json=sim_payload, headers=headers)
    assert res_sim.status_code == 200
    data_sim = res_sim.json()
    assert float(data_sim["total_aportado"]) == 62000.0
    assert float(data_sim["saldo_final_neto"]) > 62000.0
    assert "series" in data_sim
    assert len(data_sim["series"]) == 13

    # 3. Test unauthenticated request
    res_no_auth = client.get("/analyses/sim-test-1/treasury-surplus")
    assert res_no_auth.status_code == 401

    # 4. Test other user cannot access
    other_token = issue_access_token("admin", "admin")
    res_forbidden = client.get("/analyses/sim-test-1/treasury-surplus", headers={"Authorization": f"Bearer {other_token}"})
    assert res_forbidden.status_code == 404

