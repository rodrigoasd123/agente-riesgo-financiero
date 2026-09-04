"""Smoke de Streamlit para el dashboard autenticado del analista."""

from streamlit.testing.v1 import AppTest


class FakeResponse:
    status_code = 200
    content = b""

    def json(self) -> dict:
        return {
            "ocr_available": True,
            "email_configured": False,
            "email_provider": None,
        }


def test_analista_renderiza_dashboard_completo_sin_configuracion(monkeypatch):
    monkeypatch.setattr("requests.request", lambda *args, **kwargs: FakeResponse())
    at = AppTest.from_file("frontend/app.py")
    at.session_state["token"] = "token-prueba"
    at.session_state["current_user"] = {"username": "analista", "role": "analyst"}
    at.session_state["analysis"] = {
        "analysis_id": "dashboard",
        "filename": "estado.pdf",
        "cifras": {
            "pasivo_total": 770000,
            "patrimonio": 330000,
            "ventas_periodo_anterior": 1150000,
            "ventas": 950000,
            "utilidad_operativa": 80000,
            "utilidad_neta": 45000,
        },
        "indicadores": {
            "liquidez_corriente": 1.25,
            "cobertura_intereses": 2.5,
            "endeudamiento_total": 0.7,
            "roa": 0.12,
            "roe": 0.2,
        },
        "alertas": [
            {"codigo": "ENDEUDAMIENTO_ALTO", "severidad": "alta", "mensaje": "Revisar"}
        ],
        "resumen": "Resumen",
        "extraction_mode": "normal",
    }
    at.session_state["projection"] = {
        "van": "100.00",
        "tir_percent": "12.00",
        "periodo_recuperacion": "2.00",
        "flujos": [
            {"periodo": 0, "flujo": "-100.00", "flujo_acumulado": "-100.00"},
            {"periodo": 1, "flujo": "120.00", "flujo_acumulado": "20.00"},
        ],
    }
    at.run(timeout=20)

    assert not at.exception
    assert [tab.label for tab in at.tabs] == [
        "📄 Análisis",
        "📊 Dashboard",
        "📈 Proyecciones y reportes",
    ]
    assert "Dashboard financiero interactivo" in [header.value for header in at.header]
    assert len(at.metric) >= 7
    assert all("Configuración" not in tab.label for tab in at.tabs)


def test_dashboard_muestra_pronostico_explicable(monkeypatch):
    class ForecastResponse(FakeResponse):
        def __init__(self, payload):
            self.payload = payload

        def json(self) -> dict:
            return self.payload

    forecast = {
        "calculable": True,
        "modelo": "regresion_lineal_temporal",
        "confianza": "baja",
        "mae": "1000.00",
        "total_pronosticado": "900000.00",
        "variacion_total_percent": "8.50",
        "historico": [{"periodo": "2025-12", "ventas": "150000.00"}],
        "pronostico": [
            {
                "periodo": "2026-01",
                "ventas_estimadas": "155000.00",
                "limite_inferior": "150000.00",
                "limite_superior": "160000.00",
            }
        ],
        "advertencia": "Pronóstico orientativo.",
    }

    def fake_request(method, url, **kwargs):
        if url.endswith("/sales-forecast"):
            return ForecastResponse(forecast)
        return FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)
    at = AppTest.from_file("frontend/app.py")
    at.session_state["token"] = "token-prueba"
    at.session_state["current_user"] = {"username": "analista", "role": "analyst"}
    at.session_state["analysis"] = {
        "analysis_id": "forecast-ui",
        "filename": "ventas.pdf",
        "cifras": {
            "moneda": "PEN",
            "ventas": 150000,
            "ventas_mensuales": [
                {"mes": "Noviembre", "periodo": "2025-11", "ventas": 145000},
                {"mes": "Diciembre", "periodo": "2025-12", "ventas": 150000},
            ],
        },
        "indicadores": {},
        "alertas": [],
        "resumen": "Resumen",
        "extraction_mode": "normal",
    }
    at.run(timeout=20)

    assert not at.exception
    assert "Pronóstico estadístico de ventas" in [header.value for header in at.subheader]
    assert any(
        metric.label == "Modelo seleccionado" and metric.value == "Regresión"
        for metric in at.metric
    )
    assert any("Modelo completo: Regresión lineal temporal" in caption.value for caption in at.caption)
    assert any("Confianza cualitativa: Baja" in caption.value for caption in at.caption)


def test_admin_ve_acceso_a_mlflow(monkeypatch):
    class PayloadResponse(FakeResponse):
        def __init__(self, payload):
            self.payload = payload

        def json(self) -> dict:
            return self.payload

    status = {
        "gemini_connected": True,
        "gemini_key_stored": True,
        "gemini_model": "gemini-test",
        "last_tested_at": None,
        "ocr_available": True,
        "ocr_max_pages": 15,
        "mlflow_enabled": True,
        "mlflow_experiment_name": "agente-riesgo-financiero",
        "mlflow_ui_url": "http://localhost:5000",
        "gmail_redirect_uri": "http://localhost:8000/settings/gmail/callback",
        "gmail_connected": False,
        "gmail_authorized": False,
        "gmail_credentials_configured": False,
        "gmail_last_tested_at": None,
        "resend_connected": False,
        "resend_key_stored": False,
        "smtp_configured": False,
    }

    def fake_request(method, url, **kwargs):
        if url.endswith("/settings/status"):
            return PayloadResponse(status)
        if url.endswith("/auth/users"):
            return PayloadResponse([])
        return FakeResponse()

    monkeypatch.setattr("requests.request", fake_request)
    at = AppTest.from_file("frontend/app.py")
    at.session_state["token"] = "token-admin"
    at.session_state["current_user"] = {"username": "admin", "role": "admin"}
    at.run(timeout=20)

    assert not at.exception
    assert "Observabilidad con MLflow" in [header.value for header in at.subheader]
    links = at.get("link_button")
    assert any(
        link.label == "Abrir observabilidad en MLflow"
        and link.url == "http://localhost:5000"
        for link in links
    )
