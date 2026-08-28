"""SPEC-008: bootstrap del analista y datasets seguros del dashboard."""

from pathlib import Path

import bcrypt
import pytest
from fastapi.testclient import TestClient

import backend.db.database as database
from backend.config import ANALYST_PASSWORD_HASH
from backend.main import app
from frontend.dashboard import (
    alert_rows,
    alerts_chart,
    cashflow_chart,
    cashflow_rows,
    funding_chart,
    funding_rows,
    indicator_chart,
    indicator_rows,
    ordered_bar_chart,
    results_rows,
    sales_rows,
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "analyst.db"))
    with TestClient(app) as test_client:
        yield test_client


def test_hash_y_bootstrap_analista_autentican_con_rol_limitado(client: TestClient):
    assert bcrypt.checkpw(b"analista123", ANALYST_PASSWORD_HASH.encode("utf-8"))
    response = client.post(
        "/auth/login", json={"username": "analista", "password": "analista123"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "analyst"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/analyses", headers=headers).status_code == 200
    assert client.get("/settings/status", headers=headers).status_code == 403
    assert client.get("/auth/users", headers=headers).status_code == 403


def test_bootstrap_no_sobrescribe_analista_existente(client: TestClient):
    replacement = bcrypt.hashpw(b"clave-personal-123", bcrypt.gensalt(rounds=12)).decode()
    with database.get_connection() as conn:
        conn.execute(
            """UPDATE users SET password_hash = ?, is_active = 0
               WHERE username = 'analista'""",
            (replacement,),
        )
    database.init_db()
    stored = database.obtener_usuario("analista")
    assert stored is not None
    assert stored["password_hash"] == replacement
    assert stored["is_active"] == 0


def test_dashboard_prepara_cifras_completas_sin_alterarlas():
    cifras = {
        "pasivo_total": 770000,
        "patrimonio": 330000,
        "ventas_periodo_anterior": 1150000,
        "ventas": 950000,
        "utilidad_operativa": 80000,
        "utilidad_neta": 45000,
        "periodo_anterior": "2024",
        "periodo_actual": "2025",
    }
    assert funding_rows(cifras) == [
        {"componente": "Pasivo total", "valor": 770000.0},
        {"componente": "Patrimonio", "valor": 330000.0},
    ]
    assert [row["valor"] for row in sales_rows(cifras)] == [1150000.0, 950000.0]
    assert [row["valor"] for row in results_rows(cifras)] == [950000.0, 80000.0, 45000.0]
    assert funding_chart(funding_rows(cifras)).to_dict()["mark"]["type"] == "arc"
    sales_spec = ordered_bar_chart(sales_rows(cifras), "periodo", "Ventas").to_dict()
    assert sales_spec["mark"]["type"] == "bar"
    assert sales_spec["encoding"]["color"]["field"] == "_sentido"
    assert sales_spec["encoding"]["color"]["scale"]["range"] == ["#0d9488", "#d9535f"]
    assert "params" not in sales_spec


def test_dashboard_separa_unidades_de_indicadores():
    multiples, percentages = indicator_rows(
        {
            "liquidez_corriente": 1.25,
            "cobertura_intereses": 2.5,
            "endeudamiento_total": 0.7,
            "roa": 0.12,
            "variacion_ventas_pct": -17.39,
        }
    )
    assert [row["valor"] for row in multiples] == [1.25, 2.5]
    assert [row["valor"] for row in percentages] == [70.0, 12.0, -17.39]
    indicator_spec = indicator_chart(multiples, "Ratios", "Veces").to_dict()
    assert indicator_spec["mark"]["type"] == "bar"
    assert indicator_spec["encoding"]["color"]["field"] == "_sentido"
    assert "params" not in indicator_spec


def test_dashboard_alertas_allowlisted_y_flujo_sin_recalculo():
    alerts = alert_rows(
        [
            {"codigo": "LIQUIDEZ_BAJA", "severidad": "alta", "mensaje": "contenido privado"},
            {"codigo": "CODIGO_INYECTADO", "severidad": "alta", "mensaje": "secreto"},
        ]
    )
    assert alerts == [{"codigo": "LIQUIDEZ_BAJA", "severidad": "alta"}]
    assert "contenido privado" not in str(alerts_chart(alerts).to_dict())

    projection = {
        "flujos": [
            {"periodo": 0, "flujo": "-100000.00", "flujo_acumulado": "-100000.00"},
            {"periodo": 1, "flujo": "60000.00", "flujo_acumulado": "-40000.00"},
        ]
    }
    rows = cashflow_rows(projection)
    assert rows == [
        {"periodo": 0, "flujo": -100000.0, "flujo_acumulado": -100000.0},
        {"periodo": 1, "flujo": 60000.0, "flujo_acumulado": -40000.0},
    ]
    cashflow_spec = cashflow_chart(rows).to_dict()
    assert len(cashflow_spec["layer"]) == 2
    assert cashflow_spec["layer"][0]["encoding"]["color"]["field"] == "_sentido"


def test_dashboard_datos_parciales_no_inventan_ceros():
    assert funding_rows({"pasivo_total": 10}) == []
    assert sales_rows({"ventas": 500}) == [
        {"periodo": "Periodo actual", "valor": 500.0, "orden": 1}
    ]
    assert results_rows({}) == []
    assert indicator_rows({}) == ([], [])
    assert cashflow_rows(None) == []
