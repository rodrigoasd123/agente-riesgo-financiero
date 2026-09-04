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
    sales_forecast_chart,
    sales_forecast_rows,
    sales_trend_chart,
)
from frontend.theme import context_strip, inject_theme, section_eyebrow, sidebar_brand


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 30
AI_TIMEOUT = 75
st.set_page_config(page_title="Agente de Riesgo Financiero", page_icon="📊", layout="wide")
inject_theme()

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
    st.markdown('<div class="auth-shell"></div>', unsafe_allow_html=True)
    hero, access = st.columns([1.35, 0.85], gap="large")
    with hero:
        st.markdown('<div class="auth-kicker">Inteligencia financiera aplicada</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="auth-title">Decisiones más claras.<br><span>Riesgos visibles.</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="auth-lead">Convierte estados financieros en indicadores, alertas y escenarios auditables. '
            'Cada respuesta conserva su evidencia y mantiene al analista en control.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="feature-grid">
                <div class="feature-card"><b>Indicadores</b><span>Liquidez, deuda y rentabilidad</span></div>
                <div class="feature-card"><b>Evidencia</b><span>Respuestas vinculadas al documento</span></div>
                <div class="feature-card"><b>Escenarios</b><span>VAN, TIR y recuperación</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with access:
        st.markdown('<div class="login-panel-title">Bienvenido</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-panel-copy">Ingresa con tu cuenta para abrir el espacio de análisis.</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Usuario", value="admin", placeholder="Tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Tu contraseña")
            submitted = st.form_submit_button("Ingresar al agente", type="primary", use_container_width=True)
        st.markdown(
            '<div class="legal-note">Herramienta de apoyo analítico. No sustituye la revisión profesional ni autoriza decisiones crediticias.</div>',
            unsafe_allow_html=True,
        )
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
    section_eyebrow("Documento y evidencia")
    st.header("Análisis del estado financiero")
    st.caption("Carga un documento, elige el método de lectura y obtén una evaluación trazable.")
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
            st.session_state.investment_sim = None
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


def format_money(value, currency: str) -> str:
    symbols = {"PEN": "S/", "USD": "$", "EUR": "€"}
    return f"{symbols.get(currency, currency)} {float(value or 0):,.2f}"


def reports_tab() -> None:
    section_eyebrow("Planeación financiera")
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

    st.divider()
    st.subheader("Simulación educativa de inversión")
    st.caption(
        "Estima la caja potencialmente disponible y prueba supuestos de rendimiento, "
        "aportes, comisiones e impuestos. No ejecuta operaciones ni recomienda instrumentos."
    )
    settings_left, settings_right = st.columns(2)
    currency = settings_left.selectbox(
        "Moneda del escenario",
        ["PEN", "USD", "EUR"],
        format_func=lambda item: {"PEN": "Soles (PEN)", "USD": "Dólares (USD)", "EUR": "Euros (EUR)"}[item],
    )
    reserve_percent = settings_right.number_input(
        "Reserva estimada sobre pasivo corriente (%)",
        min_value=0.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
        help="Solo se usa si el PDF no contiene una reserva mínima operativa explícita.",
    )
    surplus_response = api(
        "GET",
        f"/analyses/{analysis['analysis_id']}/treasury-surplus",
        params={"reserve_percent": str(Decimal(str(reserve_percent))), "moneda": currency},
    )
    surplus = (
        surplus_response.json()
        if surplus_response is not None and surplus_response.status_code == 200
        else {}
    )
    scenarios = {}
    if surplus.get("calculable"):
        detected_currency = str(surplus.get("moneda") or currency)
        scenarios = surplus.get("escenarios") or {}
        cash_col, reserve_col, surplus_col = st.columns(3)
        cash_col.metric(
            "Efectivo no restringido",
            format_money(surplus.get("efectivo_no_restringido"), detected_currency),
        )
        reserve_col.metric(
            "Reserva operativa",
            format_money(surplus.get("reserva_operativa"), detected_currency),
        )
        surplus_col.metric(
            "Excedente máximo estimado",
            format_money(surplus.get("excedente_invertible"), detected_currency),
        )
        method_label = {
            "reserva_documental": "reserva extraída del documento",
            "porcentaje_pasivo_corriente": "porcentaje aplicado al pasivo corriente",
        }.get(surplus.get("metodo_reserva"), "método no identificado")
        st.caption(f"Método de reserva: {method_label}. El excedente es una estimación, no una recomendación.")
    elif surplus:
        st.info(f"Excedente no calculable: {surplus.get('motivo', 'faltan datos verificables')} Puedes simular un capital ingresado manualmente.")
    elif surplus_response is not None:
        show_api_error(surplus_response)

    scenario_labels = {
        "manual": "Capital manual",
        "prudente_30": "Escenario 30 % del excedente",
        "balanceado_60": "Escenario 60 % del excedente",
        "amplio_90": "Escenario 90 % del excedente",
    }
    available_scenarios = ["manual", *[key for key in scenario_labels if key in scenarios]]
    selected_scenario = st.selectbox(
        "Capital de referencia",
        available_scenarios,
        format_func=lambda key: scenario_labels[key],
    )
    suggested_capital = float(scenarios.get(selected_scenario) or 10000)

    rate_type_labels = {
        "tea": "TEA · Tasa efectiva anual",
        "tna": "TNA · Tasa nominal anual",
        "efectiva_periodo": "Tasa efectiva de un período",
    }
    rate_type = st.selectbox(
        "Tipo de tasa",
        list(rate_type_labels),
        format_func=lambda key: rate_type_labels[key],
        help="TEA ya incorpora capitalización; TNA necesita una frecuencia; la tasa efectiva corresponde al período elegido.",
    )
    if rate_type == "tea":
        st.caption("La TEA se convertirá a su tasa efectiva mensual equivalente (TEM).")
    elif rate_type == "tna":
        st.caption("La TNA se dividirá según la capitalización y luego se convertirá a TEA y TEM.")
    else:
        st.caption("Indica si la tasa efectiva corresponde a un mes, bimestre, trimestre u otro período.")

    with st.form("investment_simulation_form"):
        capital_col, contribution_col, horizon_col = st.columns(3)
        capital_in = capital_col.number_input(
            "Capital inicial",
            min_value=0.01,
            value=max(0.01, suggested_capital),
            step=500.0,
            key=f"investment_capital_{analysis['analysis_id']}_{selected_scenario}",
        )
        contribution_in = contribution_col.number_input(
            "Aporte mensual", min_value=0.0, value=0.0, step=100.0
        )
        months_in = horizon_col.number_input(
            "Plazo (meses)", min_value=1, max_value=600, value=12, step=1
        )
        rate_col, frequency_col, base_col = st.columns(3)
        rate_in = rate_col.number_input(
            "Valor de la tasa (%)",
            min_value=-99.99,
            max_value=1000.0,
            value=10.0,
            step=0.5,
        )
        periodicities = ["mensual", "bimestral", "trimestral", "cuatrimestral", "semestral", "anual"]
        if rate_type == "tna":
            frequency_in = frequency_col.selectbox(
                "Capitalización de la TNA",
                ["mensual", "bimestral", "trimestral", "cuatrimestral", "semestral", "anual", "diaria"],
                format_func=str.capitalize,
            )
            periodicity_in = "anual"
            base_days = base_col.selectbox(
                "Base de días (si es diaria)", [360, 365], index=1
            )
        elif rate_type == "efectiva_periodo":
            periodicity_in = frequency_col.selectbox(
                "Período de la tasa efectiva", periodicities, format_func=str.capitalize
            )
            frequency_in = "mensual"
            base_days = 365
            base_col.caption("La tasa se aplicará al período seleccionado.")
        else:
            frequency_in = "anual"
            periodicity_in = "anual"
            base_days = 365
            frequency_col.caption("La TEA ya incorpora la capitalización anual.")

        timing_col, inflation_col, maintenance_col = st.columns(3)
        contribution_timing = timing_col.selectbox(
            "Momento del aporte",
            ["fin_periodo", "inicio_periodo"],
            format_func=lambda item: "Fin de cada mes" if item == "fin_periodo" else "Inicio de cada mes",
        )
        inflation_in = inflation_col.number_input(
            "Inflación anual esperada (%)",
            min_value=-99.99,
            max_value=1000.0,
            value=3.0,
            step=0.25,
            help="Se usa para expresar el resultado en poder adquisitivo del inicio.",
        )
        maintenance_cost = maintenance_col.number_input(
            "Costo de mantenimiento mensual",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

        entry_col, exit_col, tax_col = st.columns(3)
        entry_fee = entry_col.number_input(
            "Comisión de entrada (%)", min_value=0.0, max_value=50.0, value=0.2, step=0.05
        )
        exit_fee = exit_col.number_input(
            "Comisión de salida (%)", min_value=0.0, max_value=50.0, value=0.2, step=0.05
        )
        tax_in = tax_col.number_input(
            "Impuesto sobre ganancia (%)",
            min_value=0.0,
            max_value=60.0,
            value=5.0,
            step=0.5,
        )
        run_investment = st.form_submit_button("Simular inversión", type="primary")

    if run_investment:
        investment_payload = {
            "capital_inicial": str(Decimal(str(capital_in))),
            "aporte_mensual": str(Decimal(str(contribution_in))),
            "plazo_meses": int(months_in),
            "tasa_percent": str(Decimal(str(rate_in))),
            "tipo_tasa": rate_type,
            "periodicidad_tasa": periodicity_in,
            "frecuencia_capitalizacion": frequency_in,
            "base_dias": base_days,
            "momento_aporte": contribution_timing,
            "inflacion_anual_percent": str(Decimal(str(inflation_in))),
            "costo_mantenimiento_mensual": str(Decimal(str(maintenance_cost))),
            "comision_entrada_percent": str(Decimal(str(entry_fee))),
            "comision_salida_percent": str(Decimal(str(exit_fee))),
            "impuesto_ganancia_percent": str(Decimal(str(tax_in))),
            "moneda": currency,
        }
        maximum_surplus = Decimal(str(surplus.get("excedente_invertible") or "0"))
        if surplus.get("calculable") and Decimal(str(capital_in)) > maximum_surplus:
            st.warning(
                "El capital supera el excedente máximo estimado del documento. "
                "La simulación continuará como escenario manual, no como disponibilidad validada."
            )
        with st.spinner("Calculando el escenario..."):
            simulation_response = api(
                "POST",
                f"/analyses/{analysis['analysis_id']}/investment-simulation",
                json=investment_payload,
            )
        if simulation_response is not None and simulation_response.status_code == 200:
            st.session_state.investment_sim = simulation_response.json()
            st.success("Simulación completada.")
        elif simulation_response is not None:
            show_api_error(simulation_response)

    simulation = st.session_state.investment_sim
    if simulation:
        simulation_currency = str(simulation.get("moneda") or currency)
        result_a, result_b, result_c, result_d = st.columns(4)
        result_a.metric("Saldo final neto", format_money(simulation["saldo_final_neto"], simulation_currency))
        result_b.metric("Ganancia neta", format_money(simulation["ganancia_neta"], simulation_currency))
        result_c.metric("ROI neto", f"{float(simulation['roi_neto_percent']):.2f} %")
        result_d.metric("Costos e impuestos", format_money(simulation["costos_totales"], simulation_currency))
        rate_a, rate_b, rate_c = st.columns(3)
        rate_a.metric("TEM equivalente", f"{float(simulation['tasa_efectiva_mensual_percent']):.4f} %")
        rate_b.metric("TEA equivalente", f"{float(simulation['tasa_efectiva_anual_percent']):.4f} %")
        rate_c.metric("Saldo real", format_money(simulation["saldo_final_real"], simulation_currency))
        st.caption(simulation.get("descripcion_tasa"))
        real_a, real_b, real_c = st.columns(3)
        real_a.metric("Ganancia real", format_money(simulation["ganancia_real"], simulation_currency))
        real_b.metric("ROI real", f"{float(simulation['roi_real_percent']):.2f} %")
        real_c.metric("Costos de mantenimiento", format_money(simulation["costos_mantenimiento"], simulation_currency))
        chart_rows = investment_series_rows(simulation)
        if chart_rows:
            st.altair_chart(investment_evolution_chart(chart_rows), use_container_width=True)
            with st.expander("Ver evolución mensual"):
                st.dataframe(chart_rows, use_container_width=True, hide_index=True)
        st.warning(simulation.get("advertencia"))

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


def dashboard_tab() -> None:
    section_eyebrow("Vista ejecutiva")
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
        if len(sales) > 2:
            st.altair_chart(sales_trend_chart(sales), use_container_width=True)
        elif len(sales) == 2:
            st.altair_chart(
                ordered_bar_chart(sales, "periodo", "Evolución de ventas"),
                use_container_width=True,
            )
        else:
            st.info("Evolución de ventas no disponible: se requieren al menos dos periodos.")

    if results:
        st.altair_chart(
            ordered_bar_chart(results, "concepto", "Ventas y resultados"),
            use_container_width=True,
        )
    else:
        st.info("No hay importes de ventas o utilidad para visualizar.")

    st.subheader("Pronóstico estadístico de ventas")
    forecast_horizon = st.selectbox(
        "Horizonte del pronóstico",
        [3, 6, 9, 12],
        index=1,
        format_func=lambda value: f"{value} meses",
        key=f"forecast_horizon_{analysis['analysis_id']}",
    )
    forecast_response = api(
        "GET",
        f"/analyses/{analysis['analysis_id']}/sales-forecast",
        params={"horizon_months": forecast_horizon},
    )
    forecast = (
        forecast_response.json()
        if forecast_response is not None and forecast_response.status_code == 200
        else {}
    )
    if forecast.get("calculable"):
        forecast_rows = sales_forecast_rows(forecast)
        forecast_currency = str(cifras.get("moneda") or "PEN")
        forecast_a, forecast_b, forecast_c, forecast_d = st.columns(4)
        forecast_a.metric(
            "Ventas proyectadas",
            format_money(forecast.get("total_pronosticado"), forecast_currency),
        )
        variation = numeric_value(forecast.get("variacion_total_percent"))
        forecast_b.metric(
            "Variación vs. período comparable",
            "Sin base" if variation is None else f"{variation:+.2f} %",
        )
        forecast_c.metric(
            "Error histórico (MAE)",
            format_money(forecast.get("mae"), forecast_currency),
        )
        model_label = {
            "regresion_lineal_temporal": "Regresión",
            "persistencia": "Persistencia",
        }.get(forecast.get("modelo"), "No identificado")
        forecast_d.metric("Modelo seleccionado", model_label)
        if forecast_rows:
            st.altair_chart(sales_forecast_chart(forecast_rows), use_container_width=True)
        st.caption(
            f"Modelo completo: {'Regresión lineal temporal' if forecast.get('modelo') == 'regresion_lineal_temporal' else model_label}. "
            f"Confianza cualitativa: {str(forecast.get('confianza') or 'no disponible').capitalize()}. "
            "Se selecciona por menor MAE en backtesting temporal."
        )
        st.warning(forecast.get("advertencia"))
    elif forecast:
        st.info(f"Pronóstico no disponible: {forecast.get('motivo', 'historia mensual insuficiente')}")
    elif forecast_response is not None:
        show_api_error(forecast_response)

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
    section_eyebrow("Administración segura")
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
    st.subheader("Observabilidad con MLflow")
    if status.get("mlflow_enabled"):
        st.success(
            f"Trazas activas · experimento {status.get('mlflow_experiment_name', 'agente-riesgo-financiero')}"
        )
        st.caption(
            "Cada ejecución muestra los nodos realmente recorridos, su duración, estado y los nombres/cantidades de campos. "
            "No se guardan preguntas, texto del PDF, cifras, respuestas ni secretos."
        )
        st.link_button(
            "Abrir observabilidad en MLflow",
            status.get("mlflow_ui_url", "http://localhost:5000"),
            type="primary",
            use_container_width=True,
        )
        st.caption(
            "La interfaz MLflow debe estar ejecutándose en el puerto configurado. "
            "En análisis verás extractor, indicadores, alertas y resumen; en chat, retrieval y answer o clarification."
        )
    else:
        st.warning("MLflow está desactivado mediante MLFLOW_ENABLED=false.")

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
    sidebar_brand()
    role_label = "Administrador" if identity["role"] == "admin" else "Analista"
    st.sidebar.success(f"{identity['username']} · {role_label}")
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
    context_items = [f"Sesión · {identity['username']}", f"Rol · {role_label}"]
    if st.session_state.analysis:
        context_items.append(f"Documento · {st.session_state.analysis['filename']}")
    context_strip(context_items)
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
