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
