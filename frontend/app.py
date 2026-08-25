"""Interfaz Streamlit del agente financiero."""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 30
AI_TIMEOUT = 75
st.set_page_config(page_title="Agente de Riesgo Financiero", page_icon="📊", layout="wide")

for key, default in {
    "token": None,
    "analysis": None,
    "chat_history": [],
    "projection": None,
    "projection_payload": None,
    "csv_report": None,
    "pdf_report": None,
    "gmail_auth_url": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api(method: str, path: str, **kwargs):
    kwargs.setdefault("timeout", TIMEOUT)
    if path != "/auth/login":
        headers = kwargs.pop("headers", {})
        kwargs["headers"] = {**headers, **auth_headers()}
    try:
        response = requests.request(method, f"{BACKEND_URL}{path}", **kwargs)
    except requests.Timeout:
        st.error("La operación tardó más de lo esperado. El backend sigue disponible; intenta nuevamente.")
        return None
    except requests.RequestException:
        st.error("No se pudo conectar con el backend. Comprueba que FastAPI esté ejecutándose.")
        return None
    if response.status_code == 401:
        st.session_state.token = None
        st.session_state.analysis = None
        st.warning("La sesión expiró. Inicia sesión nuevamente.")
        st.rerun()
    return response


def show_api_error(response) -> None:
    try:
        detail = response.json().get("detail", "La operación no pudo completarse.")
    except (ValueError, AttributeError):
        detail = "La operación no pudo completarse."
    st.error(str(detail))


def login() -> None:
    st.title("📊 Agente de análisis de riesgo financiero")
    st.caption("Análisis explicable, escenarios de flujo de caja y reportes auditables")
    with st.form("login_form"):
        username = st.text_input("Usuario", value="admin")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")
    if submitted:
        response = api("POST", "/auth/login", json={"username": username, "password": password})
        if response is not None and response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.rerun()
        elif response is not None:
            st.error("Usuario o contraseña incorrectos.")


def analysis_tab() -> None:
    st.header("Análisis del estado financiero")
    status_response = api("GET", "/settings/status")
    settings = status_response.json() if status_response is not None and status_response.status_code == 200 else {}
    extraction_label = st.radio(
        "Método de extracción",
        ["Normal", "OCR"],
        horizontal=True,
        help="Normal lee la capa de texto; OCR lee páginas escaneadas. En ambos casos el agente Gemini analiza el contenido.",
    )
    extraction_mode = "ocr" if extraction_label == "OCR" else "normal"
    ocr_available = bool(settings.get("ocr_available"))
    st.caption("Gemini analiza el documento y responde preguntas en ambos métodos; Normal/OCR sólo cambia cómo se obtiene el texto.")
    if extraction_mode == "ocr":
        if ocr_available:
            st.info("OCR activo: puede tardar más y realiza una llamada a Gemini por página.")
        else:
            st.error("OCR requiere que el agente Gemini esté conectado desde la pestaña Configuración.")
    uploaded = st.file_uploader("Estado financiero en PDF", type=["pdf"], help="Máximo configurado: 10 MB")
    cannot_analyze = uploaded is None or (extraction_mode == "ocr" and not ocr_available)
    if st.button("Analizar documento", type="primary", disabled=cannot_analyze):
        message = "Aplicando OCR página por página..." if extraction_mode == "ocr" else "Extrayendo cifras y calculando indicadores..."
        with st.spinner(message):
            response = api(
                "POST",
                "/analyze",
                files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                data={"extraction_mode": extraction_mode},
                timeout=120,
            )
        if response is not None and response.status_code == 200:
            st.session_state.analysis = response.json()
            st.session_state.chat_history = []
            st.session_state.projection = None
            st.session_state.projection_payload = None
            st.success("Análisis completado.")
        elif response is not None:
            show_api_error(response)

    analysis = st.session_state.analysis
    if not analysis:
        st.info("Carga un PDF para habilitar indicadores, preguntas, proyecciones y reportes.")
        return

    used_mode = "OCR" if analysis.get("extraction_mode") == "ocr" else "Normal"
    st.caption(f"Documento activo: {analysis['filename']} · Extracción: {used_mode}")
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Indicadores")
        st.dataframe(
            [{"indicador": key, "valor": value} for key, value in analysis["indicadores"].items()],
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("Alertas")
        if analysis["alertas"]:
            for alert in analysis["alertas"]:
                icon = "🔴" if alert["severidad"] == "alta" else "🟡"
                st.warning(f"{icon} **{alert['codigo']}**: {alert['mensaje']}")
        else:
            st.success("No se detectaron alertas con los umbrales configurados.")
    with right:
        st.subheader("Resumen ejecutivo")
        st.write(analysis["resumen"])
        with st.expander("Cifras extraídas"):
            st.json(analysis["cifras"])

    st.divider()
    st.subheader("Preguntas fundamentadas")
    st.caption("El agente consulta tanto el PDF como los indicadores calculados (ROA, ROE, liquidez y otros).")
    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input("Pregunta", placeholder="Ejemplo: ¿para qué sirve el ROA?")
        ask = st.form_submit_button("Preguntar")
    if ask and question.strip():
        with st.spinner("Buscando evidencia..."):
            response = api(
                "POST",
                "/chat",
                json={"analysis_id": analysis["analysis_id"], "pregunta": question},
                timeout=AI_TIMEOUT,
            )
        if response is not None and response.status_code == 200:
            st.session_state.chat_history.insert(0, {"pregunta": question, **response.json()})
        elif response is not None:
            show_api_error(response)
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(turn["pregunta"])
        with st.chat_message("assistant"):
            st.write(turn["respuesta"])
            route_labels = {
                "estructurada": "indicadores calculados",
                "literal": "coincidencia en el PDF",
                "semantica": "similitud semántica",
                "sin_evidencia": "sin evidencia suficiente",
            }
            if turn.get("retrieval_route"):
                confidence = float(turn.get("retrieval_confidence", 0)) * 100
                cache_note = " · caché reutilizada" if turn.get("retrieval_cache_hit") else ""
                st.caption(
                    f"Recuperación: {route_labels.get(turn['retrieval_route'], turn['retrieval_route'])} "
                    f"· confianza {confidence:.0f}%{cache_note}"
                )
            if turn.get("fuente"):
                with st.expander("Ver evidencia"):
                    st.caption(turn["fuente"])


def parse_flows(raw: str) -> list[str]:
    values = [item.strip() for item in raw.replace(";", ",").split(",") if item.strip()]
    if not values:
        raise ValueError("Ingresa al menos un flujo.")
    try:
        return [str(Decimal(value)) for value in values]
    except InvalidOperation as exc:
        raise ValueError("Los flujos deben ser números separados por comas.") from exc


def reports_tab() -> None:
    st.header("Proyecciones y reportes")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Primero analiza un PDF en la pestaña Análisis.")
        return
    st.warning("Los flujos de caja se ingresan explícitamente; no se infieren del estado financiero.")
    with st.form("projection_form"):
        investment = st.number_input("Inversión inicial", min_value=0.01, value=100000.0, step=1000.0)
        rate = st.number_input("Tasa de descuento anual (%)", min_value=-98.0, max_value=1000.0, value=10.0, step=0.5)
        flows_raw = st.text_input("Flujos por periodo, separados por comas", value="30000, 35000, 40000, 45000")
        calculate = st.form_submit_button("Calcular VAN, TIR y recuperación", type="primary")
    if calculate:
        try:
            payload = {
                "initial_investment": str(Decimal(str(investment))),
                "cash_flows": parse_flows(flows_raw),
                "discount_rate_percent": str(Decimal(str(rate))),
            }
        except ValueError as exc:
            st.error(str(exc))
        else:
            response = api("POST", f"/analyses/{analysis['analysis_id']}/projection", json=payload)
            if response is not None and response.status_code == 200:
                st.session_state.projection = response.json()
                st.session_state.projection_payload = payload
                st.session_state.csv_report = None
                st.session_state.pdf_report = None
            elif response is not None:
                show_api_error(response)

    projection = st.session_state.projection
    if projection:
        a, b, c = st.columns(3)
        a.metric("VAN", projection["van"])
        b.metric("TIR", "No disponible" if projection["tir_percent"] is None else f"{projection['tir_percent']} %")
        c.metric("Recuperación", "No alcanzada" if projection["periodo_recuperacion"] is None else f"{projection['periodo_recuperacion']} periodos")
        st.dataframe(projection["flujos"], use_container_width=True, hide_index=True)

    st.subheader("Exportar")
    st.caption("El reporte incluye cifras, indicadores, alertas y, si existe, el escenario actual.")
    payload = st.session_state.projection_payload
    col_csv, col_pdf = st.columns(2)
    with col_csv:
        if st.button("Preparar CSV", use_container_width=True):
            response = api("POST", f"/analyses/{analysis['analysis_id']}/report/csv", json=payload) if payload else api("POST", f"/analyses/{analysis['analysis_id']}/report/csv")
            if response is not None and response.status_code == 200:
                st.session_state.csv_report = response.content
            elif response is not None:
                show_api_error(response)
        if st.session_state.csv_report:
            st.download_button("Descargar CSV", st.session_state.csv_report, file_name="reporte_financiero.csv", mime="text/csv", use_container_width=True)
    with col_pdf:
        if st.button("Preparar PDF", use_container_width=True):
            response = api("POST", f"/analyses/{analysis['analysis_id']}/report/pdf", json=payload) if payload else api("POST", f"/analyses/{analysis['analysis_id']}/report/pdf")
            if response is not None and response.status_code == 200:
                st.session_state.pdf_report = response.content
            elif response is not None:
                show_api_error(response)
        if st.session_state.pdf_report:
            st.download_button("Descargar PDF", st.session_state.pdf_report, file_name="reporte_financiero.pdf", mime="application/pdf", use_container_width=True)

    st.subheader("Enviar por correo")
    status = api("GET", "/settings/status")
    email_status = status.json() if status and status.status_code == 200 else {}
    email_ready = bool(email_status.get("email_configured"))
    if email_ready:
        st.success(f"Correo disponible mediante {email_status.get('email_provider', '').upper()}.")
    else:
        st.info("Conecta Gmail en Configuración. Usa HTTPS y sólo requiere autorizar la cuenta una vez.")
    with st.form("email_form"):
        recipient = st.text_input("Destinatario", placeholder="analista@empresa.com")
        send = st.form_submit_button("Enviar PDF", disabled=not email_ready)
    if send:
        body = {"recipient": recipient, "projection": payload}
        response = api("POST", f"/analyses/{analysis['analysis_id']}/email", json=body, timeout=60)
        if response is not None and response.status_code == 200:
            st.success("Reportes PDF y CSV enviados en el mismo correo.")
        elif response is not None:
            show_api_error(response)


def settings_tab() -> None:
    st.header("Configuración")
    status_response = api("GET", "/settings/status")
    if status_response is None or status_response.status_code != 200:
        if status_response is not None:
            show_api_error(status_response)
        return
    status = status_response.json()
    if status["gemini_connected"] is True:
        st.success(f"Gemini conectado · modelo {status['gemini_model']}")
    elif status["gemini_key_stored"]:
        st.warning("Hay una clave configurada, pero todavía no se verificó en esta ejecución.")
    else:
        st.error("Gemini no está configurado. El agente está usando su modo offline.")
    if status.get("last_tested_at"):
        st.caption(f"Última prueba UTC: {status['last_tested_at']}")
    if status.get("ocr_available"):
        st.success(f"Extracción OCR disponible (máximo {status.get('ocr_max_pages', 15)} páginas por documento).")
    else:
        st.caption("El selector OCR se habilitará después de validar una clave Gemini.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Probar clave actual", disabled=not status["gemini_key_stored"], use_container_width=True):
            with st.spinner("Validando con Gemini..."):
                response = api("POST", "/settings/gemini/test", timeout=60)
            if response is not None and response.status_code == 200:
                st.success("La conexión con Gemini funciona correctamente.")
                st.rerun()
            elif response is not None:
                show_api_error(response)
    with col2:
        st.caption("La clave nunca se muestra ni se devuelve desde el backend.")

    with st.form("gemini_key_form"):
        api_key = st.text_input("Nueva clave API de Gemini", type="password", autocomplete="off")
        save = st.form_submit_button("Probar y guardar", type="primary")
    if save:
        if not api_key.strip():
            st.error("Pega una clave antes de continuar.")
        else:
            with st.spinner("Probando la clave antes de guardarla..."):
                response = api("POST", "/settings/gemini", json={"api_key": api_key}, timeout=60)
            if response is not None and response.status_code == 200:
                st.success("Clave validada y guardada. Gemini ya está activo sin reiniciar.")
                st.rerun()
            elif response is not None:
                show_api_error(response)

    st.divider()
    st.subheader("Correo")
    st.write("**Proveedor principal: Gmail API**")
    st.caption("La autorización es OAuth 2.0 y se renueva automáticamente. La aplicación sólo solicita permiso para enviar correo; no lee tu bandeja.")
    st.write("URI de redirección que debes registrar en Google Cloud:")
    st.code(status.get("gmail_redirect_uri", "http://localhost:8000/settings/gmail/callback"), language=None)

    if status.get("gmail_connected") is True:
        st.success(f"Gmail conectado como {status.get('gmail_account') or 'cuenta autorizada'}.")
    elif status.get("gmail_authorized"):
        st.warning("Existe una autorización Gmail guardada. Pulsa Probar Gmail para confirmar que sigue vigente.")
    elif status.get("gmail_credentials_configured"):
        st.info("Credenciales OAuth configuradas. Falta autorizar tu cuenta Gmail una vez.")
    else:
        st.warning("Gmail aún no tiene Client ID y Client Secret configurados.")

    with st.expander("Cómo crear las credenciales en Google Cloud", expanded=not status.get("gmail_credentials_configured")):
        st.markdown(
            "1. Crea o selecciona un proyecto en Google Cloud.\n"
            "2. Habilita **Gmail API**.\n"
            "3. Configura la pantalla de consentimiento OAuth y agrega tu correo como usuario de prueba.\n"
            "4. Crea un **OAuth Client ID** de tipo *Web application*.\n"
            "5. Registra exactamente la URI mostrada arriba.\n"
            "6. Copia el Client ID y Client Secret en este formulario."
        )

    with st.form("gmail_credentials_form"):
        gmail_client_id = st.text_input("Google OAuth Client ID", autocomplete="off")
        gmail_client_secret = st.text_input("Google OAuth Client Secret", type="password", autocomplete="off")
        save_gmail_credentials = st.form_submit_button("Guardar credenciales OAuth")
    if save_gmail_credentials:
        if not gmail_client_id.strip() or not gmail_client_secret.strip():
            st.error("Completa el Client ID y Client Secret.")
        else:
            response = api(
                "POST",
                "/settings/gmail/credentials",
                json={"client_id": gmail_client_id, "client_secret": gmail_client_secret},
            )
            if response is not None and response.status_code == 200:
                st.session_state.gmail_auth_url = None
                st.success("Credenciales guardadas. Ahora autoriza la cuenta Gmail.")
                st.rerun()
            elif response is not None:
                show_api_error(response)

    if status.get("gmail_credentials_configured") and not status.get("gmail_authorized"):
        if st.button("Preparar conexión con Gmail", type="primary", use_container_width=True):
            response = api("POST", "/settings/gmail/authorize")
            if response is not None and response.status_code == 200:
                st.session_state.gmail_auth_url = response.json()["authorization_url"]
            elif response is not None:
                show_api_error(response)
        if st.session_state.gmail_auth_url:
            st.link_button(
                "Abrir Google y autorizar Gmail",
                st.session_state.gmail_auth_url,
                type="primary",
                use_container_width=True,
            )
            st.caption("Al terminar volverás a la aplicación. Si esta pestaña no se actualiza, recárgala.")

    if status.get("gmail_authorized"):
        test_col, disconnect_col = st.columns(2)
        with test_col:
            if st.button("Probar Gmail", use_container_width=True):
                with st.spinner("Renovando acceso y comprobando la cuenta..."):
                    response = api("POST", "/settings/gmail/test", timeout=60)
                if response is not None and response.status_code == 200:
                    st.success("Gmail está conectado y se renovará automáticamente.")
                    st.rerun()
                elif response is not None:
                    show_api_error(response)
        with disconnect_col:
            if st.button("Desconectar Gmail", use_container_width=True):
                response = api("DELETE", "/settings/gmail")
                if response is not None and response.status_code == 200:
                    st.session_state.gmail_auth_url = None
                    st.success("Autorización Gmail eliminada de esta aplicación.")
                    st.rerun()
                elif response is not None:
                    show_api_error(response)

    if status.get("gmail_last_tested_at"):
        st.caption(f"Última prueba Gmail UTC: {status['gmail_last_tested_at']}")

    with st.expander("Alternativa: Resend por HTTPS"):
        st.caption("Plan gratuito: hasta 3,000 correos/mes y 100/día. Se usa sólo si Gmail no está conectado.")
        if status.get("resend_connected") is True:
            st.success("Resend conectado.")
        elif status.get("resend_key_stored"):
            st.warning("Hay una clave Resend guardada pendiente de validación.")
        else:
            st.info("Resend no está configurado.")

        if st.button("Probar clave Resend actual", disabled=not status.get("resend_key_stored"), use_container_width=True):
            with st.spinner("Validando Resend por HTTPS..."):
                response = api("POST", "/settings/resend/test", timeout=60)
            if response is not None and response.status_code == 200:
                st.success("Resend está conectado.")
                st.rerun()
            elif response is not None:
                show_api_error(response)

        with st.form("resend_key_form"):
            resend_key = st.text_input("API key de Resend", type="password", autocomplete="off")
            from_email = st.text_input("Correo remitente", value="onboarding@resend.dev")
            save_resend = st.form_submit_button("Probar y guardar Resend")
        if save_resend:
            if not resend_key.strip():
                st.error("Pega una API key de Resend antes de continuar.")
            else:
                with st.spinner("Probando Resend antes de guardar..."):
                    response = api("POST", "/settings/resend", json={"api_key": resend_key, "from_email": from_email}, timeout=60)
                if response is not None and response.status_code == 200:
                    st.success("Resend validado y activado.")
                    st.rerun()
                elif response is not None:
                    show_api_error(response)

    if status["smtp_configured"] and not status.get("resend_configured"):
        st.caption("SMTP está configurado como alternativa; se usará sólo mientras Resend no esté activo.")


def main() -> None:
    if st.session_state.token is None:
        login()
        return
    st.sidebar.title("📊 Agente financiero")
    st.sidebar.success("Sesión iniciada como admin")
    gmail_result = st.query_params.get("gmail")
    if gmail_result == "connected":
        st.sidebar.success("Gmail autorizado. Abre Configuración para comprobarlo.")
        st.query_params.clear()
    elif gmail_result in {"cancelled", "error"}:
        st.sidebar.warning("La conexión con Gmail no se completó. Inténtalo nuevamente.")
        st.query_params.clear()
    if st.sidebar.button("Cerrar sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    tab_analysis, tab_reports, tab_settings = st.tabs(["📄 Análisis", "📈 Proyecciones y reportes", "⚙️ Configuración"])
    with tab_analysis:
        analysis_tab()
    with tab_reports:
        reports_tab()
    with tab_settings:
        settings_tab()


main()
