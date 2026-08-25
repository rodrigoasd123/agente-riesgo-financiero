"""Integracion API: auth, upload, ownership, chat e historial."""

import json

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.api.routes_analyze as analyze_routes
import backend.agent.qa as qa
import backend.db.database as database
from backend.db.database import guardar_analisis
from backend.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_endpoints_de_negocio_requieren_token(client: TestClient):
    assert client.get("/analyses").status_code == 401
    assert client.post("/chat", json={"analysis_id": "x", "pregunta": "ventas"}).status_code == 401
    assert client.post(
        "/analyze", files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")}
    ).status_code == 401


def test_login_incorrecto_no_autentica(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "incorrecta"},
    )
    assert response.status_code == 401
    assert "access_token" not in response.text


def test_rechaza_extension_y_firma_invalidas(client: TestClient, auth_headers: dict):
    wrong_extension = client.post(
        "/analyze",
        files={"file": ("estado.txt", b"%PDF-1.4", "text/plain")},
        headers=auth_headers,
    )
    assert wrong_extension.status_code == 400

    wrong_signature = client.post(
        "/analyze",
        files={"file": ("estado.pdf", b"esto no es pdf", "application/pdf")},
        headers=auth_headers,
    )
    assert wrong_signature.status_code == 400


def test_rechaza_pdf_que_excede_limite(
    client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(analyze_routes, "MAX_UPLOAD_BYTES", 12)
    response = client.post(
        "/analyze",
        files={"file": ("grande.pdf", b"%PDF-" + b"x" * 20, "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_flujo_e2e_offline_con_fuente_e_historial(
    client: TestClient, auth_headers: dict
):
    sample = Path("data/estado_financiero_ejemplo.pdf")
    with sample.open("rb") as stream:
        analysis_response = client.post(
            "/analyze",
            files={"file": ("../estado.pdf", stream, "application/pdf")},
            headers=auth_headers,
        )

    assert analysis_response.status_code == 200, analysis_response.text
    analysis = analysis_response.json()
    assert analysis["filename"] == "estado.pdf"
    assert analysis["analysis_id"]
    assert analysis["extraction_mode"] == "normal"
    assert analysis["indicadores"]
    assert analysis["alertas"]
    assert "offline" in analysis["resumen"].lower()

    found = client.post(
        "/chat",
        json={"analysis_id": analysis["analysis_id"], "pregunta": "Cuales fueron las ventas?"},
        headers=auth_headers,
    )
    assert found.status_code == 200, found.text
    assert found.json()["encontrado"] is True
    assert found.json()["fuente"].startswith("[Pagina ")
    assert found.json()["retrieval_route"] == "literal"
    assert 0 <= found.json()["retrieval_confidence"] <= 1

    missing = client.post(
        "/chat",
        json={"analysis_id": analysis["analysis_id"], "pregunta": "temperatura de Marte"},
        headers=auth_headers,
    )
    assert missing.status_code == 200
    assert missing.json()["encontrado"] is False
    assert missing.json()["fuente"] is None
    assert missing.json()["retrieval_route"] == "sin_evidencia"

    history = client.get("/analyses", headers=auth_headers)
    assert history.status_code == 200
    assert [item["id"] for item in history.json()["analyses"]] == [analysis["analysis_id"]]


def test_no_expone_analisis_de_otro_actor(client: TestClient, auth_headers: dict):
    guardar_analisis(
        analysis_id="de-otro",
        filename="otro.pdf",
        created_by="otro-usuario",
        cifras={},
        indicadores={},
        alertas=[],
        resumen="privado",
        chunks=["[Pagina 1]\nVentas: 10"],
    )
    history = client.get("/analyses", headers=auth_headers).json()["analyses"]
    assert all(item["id"] != "de-otro" for item in history)

    response = client.post(
        "/chat",
        json={"analysis_id": "de-otro", "pregunta": "ventas"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_health_declara_modo_offline(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert response.json()["mode"] == "offline-fallback"
    assert response.json()["gemini_configured"] is False


def test_chat_semantico_crea_y_reutiliza_cache(
    client: TestClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []

    def fake_embed(text: str, *, task_type: str) -> list[float]:
        calls.append(task_type)
        return [1.0, 0.0]

    monkeypatch.setattr(qa, "embed_text", fake_embed)
    guardar_analisis(
        analysis_id="semantic",
        filename="semantic.pdf",
        created_by="admin",
        cifras={},
        indicadores={},
        alertas=[],
        resumen="ok",
        chunks=["[Pagina 1]\nLa compañía conserva reservas abundantes."],
    )

    first = client.post(
        "/chat",
        json={"analysis_id": "semantic", "pregunta": "holgura monetaria futura"},
        headers=auth_headers,
    )
    assert first.status_code == 200, first.text
    assert first.json()["retrieval_route"] == "semantica"
    assert first.json()["retrieval_cache_hit"] is False
    assert calls == ["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]
    stored = database.obtener_analisis("semantic", "admin")
    assert len(json.loads(stored["embeddings_json"])) == 1

    calls.clear()
    second = client.post(
        "/chat",
        json={"analysis_id": "semantic", "pregunta": "holgura monetaria futura"},
        headers=auth_headers,
    )
    assert second.status_code == 200
    assert second.json()["retrieval_cache_hit"] is True
    assert calls == ["RETRIEVAL_QUERY"]


def test_analysis_precalcula_y_persiste_embeddings(
    client: TestClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(analyze_routes, "is_gemini_configured", lambda: True)
    monkeypatch.setattr(
        analyze_routes,
        "crear_embeddings_documento",
        lambda chunks: [[float(index), 1.0] for index, _ in enumerate(chunks)],
    )
    with Path("data/estado_financiero_ejemplo.pdf").open("rb") as stream:
        response = client.post(
            "/analyze",
            files={"file": ("cache.pdf", stream, "application/pdf")},
            headers=auth_headers,
        )

    assert response.status_code == 200, response.text
    stored = database.obtener_analisis(response.json()["analysis_id"], "admin")
    chunks = json.loads(stored["chunks_json"])
    embeddings = json.loads(stored["embeddings_json"])
    assert len(embeddings) == len(chunks)
    assert all(len(vector) == 2 for vector in embeddings)
