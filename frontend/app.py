"""Interfaz Streamlit del agente financiero."""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation

import requests
import streamlit as st
from dotenv import load_dotenv

from frontend.dashboard import (
    alert_rows,
    alerts_chart,
    cashflow_chart,
    cashflow_rows,
    funding_chart,
    funding_rows,
    indicator_chart,
    indicator_rows,
    investment_evolution_chart,
    investment_series_rows,
    numeric_value,
    ordered_bar_chart,
    results_rows,
    sales_rows,
)


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 30
AI_TIMEOUT = 75
st.set_page_config(page_title="Agente de Riesgo Financiero", page_icon="📊", layout="wide")

for key, default in {
    "token": None,
    "current_user": None,
    "analysis": None,
    "chat_history": [],
    "projection": None,
    "projection_payload": None,
    "investment_sim": None,
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
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.current_user = {"username": data["username"], "role": data["role"]}
            st.rerun()
        elif response is not None:
            st.error("Usuario o contraseña incorrectos.")


def analysis_tab() -> None:
    st.header("Análisis del estado financiero")
    status_response = api("GET", "/settings/capabilities")
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
    status = api("GET", "/settings/capabilities")
    email_status = status.json() if status and status.status_code == 200 else {}
    email_ready = bool(email_status.get("email_configured"))
    if email_ready:
        st.success(f"Correo disponible mediante {email_status.get('email_provider', '').upper()}.")
    else:
        st.info("Conecta Gmail en Configuración. Usa HTTPS y sólo requiere autorizar la cuenta una vez.")
    with st.form("email_form"):
        recipient = st.text_input("Destinatario", placeholder="analista@empresa.com")
        send = st.form_submit_button("Enviar PDF y CSV", disabled=not email_ready)
    if send:
        body = {"recipient": recipient, "projection": payload}
        response = api("POST", f"/analyses/{analysis['analysis_id']}/email", json=body, timeout=60)
        if response is not None and response.status_code == 200:
            st.success("Reportes PDF y CSV enviados en el mismo correo.")
        elif response is not None:
            show_api_error(response)

    st.divider()
    st.subheader("💼 Simulación de Inversión y Excedente de Tesorería")
    st.caption("Diagnostica el efectivo libre del estado financiero y simula rendimientos netos con interés compuesto, comisiones e impuestos.")

    surplus_res = api("GET", f"/analyses/{analysis['analysis_id']}/treasury-surplus")
    surplus_data = surplus_res.json() if surplus_res is not None and surplus_res.status_code == 200 else {}
    
    if surplus_data:
        efectivo = float(surplus_data.get("efectivo_total") or 0)
        reserva = float(surplus_data.get("reserva_operativa") or 0)
        excedente = float(surplus_data.get("excedente_invertible") or 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Efectivo total en caja", f"${efectivo:,.2f}")
        c2.metric("Reserva operativa (20%)", f"${reserva:,.2f}")
        c3.metric("Excedente invertible sugerido", f"${excedente:,.2f}")
        
        perfiles = surplus_data.get("perfiles") or {}
        st.caption(
            f"Perfiles de colocación recomendados sobre el excedente: "
            f"Conservador (30%): **${float(perfiles.get('conservador') or 0):,.2f}** · "
            f"Moderado (60%): **${float(perfiles.get('moderado') or 0):,.2f}** · "
            f"Dinámico (90%): **${float(perfiles.get('dinamico') or 0):,.2f}**"
        )
        default_capital = excedente if excedente > 0 else 10000.0
    else:
        default_capital = 10000.0

    with st.form("investment_simulation_form"):
        col_cap, col_monthly, col_horizon = st.columns(3)
        capital_in = col_cap.number_input("Capital inicial a invertir ($)", min_value=1.0, value=float(default_capital), step=500.0)
        aporte_in = col_monthly.number_input("Aporte mensual adicional ($)", min_value=0.0, value=0.0, step=100.0)
        plazo_in = col_horizon.number_input("Plazo de inversión (meses)", min_value=1, max_value=360, value=12, step=1)

        col_rate, col_freq, col_tax = st.columns(3)
        tasa_in = col_rate.number_input("Tasa de rendimiento anual estimada (%)", min_value=-50.0, max_value=1000.0, value=10.0, step=0.5)
        freq_in = col_freq.selectbox(
            "Frecuencia de capitalización",
            ["mensual", "trimestral", "semestral", "anual", "diaria"],
            format_func=lambda x: x.capitalize(),
        )
        tax_in = col_tax.number_input("Impuesto a la ganancia de capital (%)", min_value=0.0, max_value=60.0, value=5.0, step=0.5)

        col_com_in, col_com_out = st.columns(2)
        com_in = col_com_in.number_input("Comisión de entrada / corretaje (%)", min_value=0.0, max_value=20.0, value=0.2, step=0.05)
        com_out = col_com_out.number_input("Comisión de salida / rescate (%)", min_value=0.0, max_value=20.0, value=0.2, step=0.05)

        run_sim = st.form_submit_button("Simular rendimiento de inversión", type="primary")

    if run_sim:
        sim_payload = {
            "capital_inicial": str(Decimal(str(capital_in))),
            "aporte_mensual": str(Decimal(str(aporte_in))),
            "plazo_meses": int(plazo_in),
            "tasa_anual_percent": str(Decimal(str(tasa_in))),
            "frecuencia_capitalizacion": str(freq_in),
            "comision_entrada_percent": str(Decimal(str(com_in))),
            "comision_salida_percent": str(Decimal(str(com_out))),
            "impuesto_ganancia_percent": str(Decimal(str(tax_in))),
        }
        with st.spinner("Calculando proyección financiera..."):
            sim_res = api("POST", f"/analyses/{analysis['analysis_id']}/investment-simulation", json=sim_payload)
        if sim_res is not None and sim_res.status_code == 200:
            st.session_state.investment_sim = sim_res.json()
            st.success("Simulación de inversión completada.")
        elif sim_res is not None:
            show_api_error(sim_res)

    sim = st.session_state.investment_sim
    if sim:
        st.subheader("Resultados de la simulación")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Saldo final neto", f"${float(sim['saldo_final_neto']):,.2f}")
        m2.metric("Ganancia neta total", f"${float(sim['ganancia_neta']):,.2f}")
        m3.metric("Rendimiento neto (ROI)", f"{float(sim['roi_neto_percent']):.2f} %")
        com_imp_total = float(sim['comisiones_totales']) + float(sim['impuestos_totales'])
        m4.metric("Fricción (Comis. + Imp.)", f"${com_imp_total:,.2f}")

        chart_rows = investment_series_rows(sim)
        if chart_rows:
            st.altair_chart(investment_evolution_chart(chart_rows), use_container_width=True)
            with st.expander("Ver tabla mensual detallada"):
                st.dataframe(chart_rows, use_container_width=True, hide_index=True)



def dashboard_tab() -> None:
    st.header("Dashboard financiero interactivo")
    st.caption(
        "Explora relaciones entre cifras calculadas. Los gráficos no sustituyen la revisión humana ni constituyen una decisión crediticia."
    )
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Analiza un estado financiero para habilitar el dashboard.")
        return

    cifras = analysis.get("cifras") or {}
    indicadores = analysis.get("indicadores") or {}
    alertas = analysis.get("alertas") or []
    st.caption(f"Documento activo: {analysis['filename']}")

    liquidity = numeric_value(indicadores.get("liquidez_corriente"))
    debt = numeric_value(indicadores.get("endeudamiento_total"))
    roa = numeric_value(indicadores.get("roa"))
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Liquidez corriente", "Sin dato" if liquidity is None else f"{liquidity:.2f}x")
    kpi2.metric("Endeudamiento", "Sin dato" if debt is None else f"{debt * 100:.2f}%")
    kpi3.metric("ROA", "Sin dato" if roa is None else f"{roa * 100:.2f}%")
    kpi4.metric("Alertas", len(alertas))

    funding = funding_rows(cifras)
    sales = sales_rows(cifras)
    results = results_rows(cifras)
    left, right = st.columns(2)
    with left:
        if funding:
            st.altair_chart(funding_chart(funding), use_container_width=True)
        else:
            st.info("Estructura financiera no disponible: se requieren pasivo total y patrimonio.")
    with right:
        if len(sales) == 2:
            st.altair_chart(
                ordered_bar_chart(sales, "periodo", "Evolución de ventas"),
                use_container_width=True,
            )
        else:
            st.info("Comparación de ventas no disponible: se requieren dos periodos.")

    if results:
        st.altair_chart(
            ordered_bar_chart(results, "concepto", "Ventas y resultados"),
            use_container_width=True,
        )
    else:
        st.info("No hay importes de ventas o utilidad para visualizar.")

    multiples, percentages = indicator_rows(indicadores)
    ratio_left, ratio_right = st.columns(2)
    with ratio_left:
        if multiples:
            st.altair_chart(
                indicator_chart(multiples, "Liquidez y cobertura", "Veces"),
                use_container_width=True,
            )
        else:
            st.info("No hay indicadores de liquidez o cobertura disponibles.")
    with ratio_right:
        if percentages:
            st.altair_chart(
                indicator_chart(percentages, "Rentabilidad, deuda y variación", "%"),
                use_container_width=True,
            )
        else:
            st.info("No hay indicadores porcentuales disponibles.")

    safe_alerts = alert_rows(alertas)
    if safe_alerts:
        st.altair_chart(alerts_chart(safe_alerts), use_container_width=True)
        st.caption("Rojo: alta · amarillo: media · azul: baja. Revisa el detalle en la pestaña Análisis.")
    else:
        st.success("No existen alertas financieras estructuradas para graficar.")

    flows = cashflow_rows(st.session_state.projection)
    if flows:
        st.altair_chart(cashflow_chart(flows), use_container_width=True)
    else:
        st.info("Calcula un escenario en Proyecciones y reportes para visualizar su flujo de caja.")


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

    st.divider()
    st.subheader("Usuarios y roles")
    st.caption("Los analistas pueden analizar y enviar reportes; sólo los administradores pueden cambiar proveedores y usuarios.")
    with st.form("create_user_form"):
        new_username = st.text_input("Nuevo usuario", autocomplete="off")
        new_password = st.text_input("Contraseña temporal (mínimo 12 caracteres)", type="password", autocomplete="new-password")
        new_role = st.selectbox("Rol", ["analyst", "admin"], format_func=lambda value: "Analista" if value == "analyst" else "Administrador")
        create_user_submitted = st.form_submit_button("Crear usuario")
    if create_user_submitted:
        response = api(
            "POST",
            "/auth/users",
            json={"username": new_username, "password": new_password, "role": new_role},
        )
        if response is not None and response.status_code == 201:
            st.success(f"Usuario {response.json()['username']} creado.")
            st.rerun()
        elif response is not None:
            show_api_error(response)

    users_response = api("GET", "/auth/users")
    if users_response is not None and users_response.status_code == 200:
        for user in users_response.json():
            col_user, col_role, col_state, col_action = st.columns([3, 2, 2, 2])
            col_user.write(user["username"])
            col_role.write("Administrador" if user["role"] == "admin" else "Analista")
            col_state.write("Activo" if user["is_active"] else "Inactivo")
            is_self = user["username"] == st.session_state.current_user["username"]
            action = "Desactivar" if user["is_active"] else "Activar"
            if col_action.button(action, key=f"toggle-user-{user['username']}", disabled=is_self):
                response = api(
                    "PATCH",
                    f"/auth/users/{user['username']}/active",
                    json={"is_active": not user["is_active"]},
                )
                if response is not None and response.status_code == 200:
                    st.rerun()
                elif response is not None:
                    show_api_error(response)


def main() -> None:
    if st.session_state.token is None:
        login()
        return
    if st.session_state.current_user is None:
        response = api("GET", "/auth/me")
        if response is None:
            return
        if response.status_code != 200:
            show_api_error(response)
            return
        st.session_state.current_user = response.json()
    identity = st.session_state.current_user
    st.sidebar.title("📊 Agente financiero")
    role_label = "Administrador" if identity["role"] == "admin" else "Analista"
    st.sidebar.success(f"Sesión: {identity['username']} · {role_label}")
    gmail_result = st.query_params.get("gmail")
    if gmail_result == "connected":
        st.sidebar.success("Gmail autorizado. Abre Configuración para comprobarlo.")
        st.query_params.clear()
    elif gmail_result in {"cancelled", "error"}:
        st.sidebar.warning("La conexión con Gmail no se completó. Inténtalo nuevamente.")
        st.query_params.clear()
    if st.sidebar.button("Cerrar sesión"):
        api("POST", "/auth/logout")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    labels = ["📄 Análisis", "📊 Dashboard", "📈 Proyecciones y reportes"]
    if identity["role"] == "admin":
        labels.append("⚙️ Configuración")
    tabs = st.tabs(labels)
    tab_analysis, tab_dashboard, tab_reports = tabs[:3]
    with tab_analysis:
        analysis_tab()
    with tab_dashboard:
        dashboard_tab()
    with tab_reports:
        reports_tab()
    if identity["role"] == "admin":
        with tabs[3]:
            settings_tab()


main()
