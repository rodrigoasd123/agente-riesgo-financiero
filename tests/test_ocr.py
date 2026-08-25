from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.agent.pdf_reader as pdf_reader
from backend.agent.gemini_client import GeminiUnavailableError
import backend.api.routes_analyze as analyze_routes
import backend.db.database as database
from backend.main import app


def test_procesar_pdf_ocr_transcribe_cada_pagina(monkeypatch: pytest.MonkeyPatch):
    calls = []
    monkeypatch.setattr(
        pdf_reader,
        "transcribe_page_image",
        lambda image: calls.append(image) or "Ventas netas: 1000",
    )
    monkeypatch.setattr(pdf_reader, "extraer_cifras_clave", lambda text: {"ventas": 1000})

    result = pdf_reader.procesar_pdf("data/estado_financiero_ejemplo.pdf", "ocr")

    assert result["extraction_mode"] == "ocr"
    assert calls and all(call.startswith(b"\x89PNG") for call in calls)
    assert result["cifras"]["ventas"] == 1000
    assert result["chunks"][0].startswith("[Pagina 1]")


def test_ocr_rechaza_documento_sobre_limite(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(pdf_reader, "OCR_MAX_PAGES", 0)
    with pytest.raises(pdf_reader.OCRPageLimitError):
        pdf_reader.procesar_pdf("data/estado_financiero_ejemplo.pdf", "ocr")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "ocr.db"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_ocr_sin_gemini_devuelve_conflicto(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(analyze_routes, "is_gemini_configured", lambda: False)
    sample = Path("data/estado_financiero_ejemplo.pdf")
    with sample.open("rb") as stream:
        response = client.post(
            "/analyze",
            headers=auth_headers,
            data={"extraction_mode": "ocr"},
            files={"file": (sample.name, stream, "application/pdf")},
        )
    assert response.status_code == 409
    assert "Configuracion" in response.json()["detail"]


def test_modo_invalido_es_rechazado(client: TestClient, auth_headers: dict):
    sample = Path("data/estado_financiero_ejemplo.pdf")
    with sample.open("rb") as stream:
        response = client.post(
            "/analyze",
            headers=auth_headers,
            data={"extraction_mode": "automatico"},
            files={"file": (sample.name, stream, "application/pdf")},
        )
    assert response.status_code == 422


def test_ocr_exitoso_persiste_modo(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    class FakeGraph:
        def invoke(self, state):
            assert state["extraction_mode"] == "ocr"
            return {"cifras": {"ventas": 1000}, "indicadores": {}, "alertas": [], "resumen": "OCR", "chunks": ["[Pagina 1]\nVentas: 1000"]}

    monkeypatch.setattr(analyze_routes, "is_gemini_configured", lambda: True)
    monkeypatch.setattr(analyze_routes, "analysis_graph", FakeGraph())
    sample = Path("data/estado_financiero_ejemplo.pdf")
    with sample.open("rb") as stream:
        response = client.post(
            "/analyze",
            headers=auth_headers,
            data={"extraction_mode": "ocr"},
            files={"file": (sample.name, stream, "application/pdf")},
        )
    assert response.status_code == 200, response.text
    assert response.json()["extraction_mode"] == "ocr"
    history = client.get("/analyses", headers=auth_headers).json()["analyses"]
    assert history[0]["extraction_mode"] == "ocr"


def test_fallo_proveedor_ocr_es_sanitizado(client: TestClient, auth_headers: dict, monkeypatch: pytest.MonkeyPatch):
    class BrokenGraph:
        def invoke(self, state):
            raise GeminiUnavailableError("detalle privado")

    monkeypatch.setattr(analyze_routes, "is_gemini_configured", lambda: True)
    monkeypatch.setattr(analyze_routes, "analysis_graph", BrokenGraph())
    sample = Path("data/estado_financiero_ejemplo.pdf")
    with sample.open("rb") as stream:
        response = client.post(
            "/analyze",
            headers=auth_headers,
            data={"extraction_mode": "ocr"},
            files={"file": (sample.name, stream, "application/pdf")},
        )
    assert response.status_code == 503
    assert "privado" not in response.text
