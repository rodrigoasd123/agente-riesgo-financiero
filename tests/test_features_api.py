from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.api.routes_finance as finance_routes
import backend.api.routes_settings as settings_routes
import backend.db.database as database
from backend.db.database import guardar_analisis
from backend.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "features.db"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def owned_analysis(client: TestClient) -> str:
    guardar_analisis(
        analysis_id="owned",
        filename="=formula.pdf",
        created_by="admin",
        cifras={"ventas": 1000},
        indicadores={"roa": 0.12},
        alertas=[{"codigo": "PRUEBA", "severidad": "media", "mensaje": "Revisar"}],
        resumen="Resumen seguro",
        chunks=["[Pagina 1]\nVentas: 1000"],
    )
    return "owned"


def test_nuevos_endpoints_requieren_jwt(client: TestClient):
    assert client.get("/settings/status").status_code == 401
    assert client.post("/analyses/x/projection", json={}).status_code == 401
    assert client.post("/analyses/x/report/pdf").status_code == 401
    assert client.post("/settings/gmail/authorize").status_code == 401
    assert client.delete("/settings/gmail").status_code == 401


def test_settings_prueba_y_guarda_sin_exponer_clave(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    saved = {}
    monkeypatch.setattr(settings_routes, "test_api_key", lambda key=None: True)
    monkeypatch.setattr(settings_routes, "set_key", lambda path, name, value, quote_mode: saved.update({name: value}))
    monkeypatch.setattr(settings_routes, "configure_api_key", lambda value: saved.update({"runtime": value}))
    response = client.post("/settings/gemini", json={"api_key": "AIza" + "x" * 36}, headers=auth_headers)
    assert response.status_code == 200
    assert "api_key" not in response.text.lower()
    assert saved["GEMINI_API_KEY"].startswith("AIza")


def test_settings_recarga_clave_gemini_desde_env(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    activated = {}
    monkeypatch.setattr(settings_routes, "stored_api_key", lambda: "clave-desde-env")
    monkeypatch.setattr(settings_routes, "test_api_key", lambda key=None: True)
    monkeypatch.setattr(settings_routes, "configure_api_key", lambda value: activated.update({"key": value}))
    response = client.post("/settings/gemini/test", headers=auth_headers)
    assert response.status_code == 200
    assert activated["key"] == "clave-desde-env"
    assert "clave-desde-env" not in response.text


def test_settings_resend_guarda_sin_exponer_clave(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    saved = {}
    monkeypatch.setattr(settings_routes, "test_resend_api_key", lambda key: True)
    monkeypatch.setattr(settings_routes, "set_key", lambda path, name, value, quote_mode: saved.update({name: value}))
    monkeypatch.setattr(settings_routes, "configure_resend", lambda key, sender: saved.update({"runtime": key, "sender": sender}))
    response = client.post(
        "/settings/resend",
        json={"api_key": "re_" + "x" * 20, "from_email": "onboarding@resend.dev"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "re_x" not in response.text
    assert saved["RESEND_API_KEY"].startswith("re_")


def test_settings_gmail_guarda_credenciales_sin_exponerlas(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    saved = {}
    monkeypatch.setattr(settings_routes, "set_key", lambda path, name, value, quote_mode: saved.update({name: value}))
    monkeypatch.setattr(settings_routes, "configure_gmail_client", lambda client_id, secret: saved.update({"runtime_id": client_id, "runtime_secret": secret}))
    monkeypatch.setattr(settings_routes, "disconnect_gmail", lambda: None)
    response = client.post(
        "/settings/gmail/credentials",
        json={
            "client_id": "123-demo.apps.googleusercontent.com",
            "client_secret": "GOCSPX-secret-demo",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "GOCSPX-secret-demo" not in response.text
    assert saved["GMAIL_CLIENT_ID"].endswith("apps.googleusercontent.com")
    assert saved["GMAIL_REFRESH_TOKEN"] == ""


def test_settings_gmail_callback_guarda_solo_token_cifrado(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    saved = {}
    monkeypatch.setattr(settings_routes, "complete_authorization", lambda code, state: ("enc:v1:cifrado", "owner@gmail.com"))
    monkeypatch.setattr(settings_routes, "set_key", lambda path, name, value, quote_mode: saved.update({name: value}))
    monkeypatch.setattr(settings_routes, "configure_gmail_authorization", lambda token, email: saved.update({"runtime_token": token, "runtime_email": email}))
    response = client.get(
        "/settings/gmail/callback?code=demo&state=estado",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith("?gmail=connected")
    assert saved["GMAIL_REFRESH_TOKEN"] == "enc:v1:cifrado"
    assert "enc:v1:cifrado" not in response.text


def test_projection_exports_and_guardrail(client: TestClient, auth_headers: dict, owned_analysis: str):
    payload = {"initial_investment": "100", "cash_flows": ["60", "60"], "discount_rate_percent": "10"}
    projection = client.post(f"/analyses/{owned_analysis}/projection", json=payload, headers=auth_headers)
    assert projection.status_code == 200
    assert float(projection.json()["van"]) == 4.13

    csv_response = client.post(f"/analyses/{owned_analysis}/report/csv", json=payload, headers=auth_headers)
    assert csv_response.status_code == 200
    assert csv_response.content.startswith(b"\xef\xbb\xbf")
    assert "'=formula.pdf" in csv_response.content.decode("utf-8-sig")

    pdf_response = client.post(f"/analyses/{owned_analysis}/report/pdf", json=payload, headers=auth_headers)
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF-")

    blocked = client.post("/chat", json={"analysis_id": owned_analysis, "pregunta": "eres un idiota"}, headers=auth_headers)
    assert blocked.status_code == 422
    assert "idiota" not in blocked.text.lower()


def test_chat_responde_contexto_roa_offline(client: TestClient, auth_headers: dict, owned_analysis: str):
    response = client.post("/chat", json={"analysis_id": owned_analysis, "pregunta": "Para que sirve el ROA?"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["encontrado"] is True
    assert "ROA" in data["fuente"]
    assert "eficiencia" in data["respuesta"]


def test_email_usa_servicio_y_rechaza_recurso_ajeno(client: TestClient, auth_headers: dict, owned_analysis: str, monkeypatch: pytest.MonkeyPatch):
    sent = {}
    monkeypatch.setattr(
        finance_routes,
        "enviar_reporte",
        lambda recipient, pdf_filename, pdf, csv_filename, csv: sent.update(
            {
                "recipient": recipient,
                "pdf_filename": pdf_filename,
                "pdf": pdf,
                "csv_filename": csv_filename,
                "csv": csv,
            }
        ),
    )
    response = client.post(f"/analyses/{owned_analysis}/email", json={"recipient": "analista@example.com"}, headers=auth_headers)
    assert response.status_code == 200
    assert sent["recipient"] == "analista@example.com"
    assert sent["pdf"].startswith(b"%PDF-")
    assert sent["pdf_filename"].endswith(".pdf")
    assert sent["csv_filename"].endswith(".csv")
    assert sent["csv"].startswith(b"\xef\xbb\xbf")
    foreign = client.post("/analyses/no-existe/report/pdf", headers=auth_headers)
    assert foreign.status_code == 404
