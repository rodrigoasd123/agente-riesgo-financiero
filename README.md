# Agente de Analisis de Riesgo Financiero

Aplicacion local que procesa estados financieros sinteticos en PDF, calcula ratios, detecta alertas y responde preguntas con fragmentos fuente. Usa FastAPI, Streamlit, LangGraph, SQLite, MLflow y Gemini; cuando Gemini no esta disponible mantiene un modo offline determinista.

> Es una herramienta de apoyo academico. No autoriza credito ni sustituye la revision de un analista.

## Estado

- JWT Bearer con firma HS256, rol, expiracion, `jti` persistente y claims validados (`iss`, `aud`, `sub`, `role`, `type`, `iat`, `nbf`, `exp`, `jti`).
- Usuarios SQLite persistentes con roles `admin`/`analyst`; `admin/admin123` y `analista/analista123` se crean idempotentemente desde hashes bcrypt costo 12 proporcionados.
- Sesiones revocables: logout y desactivacion invalidan tokens inmediatamente; los endpoints de negocio filtran datos por propietario.
- RBAC: sólo `admin` administra usuarios y configuración Gemini/correo; `analyst` usa análisis, chat, proyecciones, exportación y envío.
- Upload PDF limitado (10 MB por defecto), validado por extension y firma `%PDF-`, con temporal UUID y cleanup garantizado.
- Gemini mediante `google-genai`, `gemini-3.6-flash`, `gemini-embedding-001`, timeout y extraccion Pydantic estructurada.
- Fallback offline para extraccion, resumen y retrieval cuando falta red, cuota o API key.
- Suite automatizada para bootstrap seguro, dashboard, RBAC/sesiones revocables, RAG graduado, cache semantica, migracion SQLite, OAuth/Gmail, Gemini/OCR, reportes, guardrails, simulacion financiera, autorizacion y privacidad de trazas.
- Configuracion de Gemini 3.6 Flash desde la UI, con prueba real de generación y sin volver a mostrar la clave.
- VAN, TIR, recuperacion y flujo acumulado sobre flujos ingresados explicitamente.
- Simulador de inversion con TEA, TNA o tasa efectiva por periodo; capitalizacion diaria/mensual/bimestral/trimestral/cuatrimestral/semestral/anual, aportes, costos, impuestos, inflacion y resultados nominales/reales.
- Reportes CSV/PDF; cada correo adjunta ambos archivos mediante Gmail API, con fallbacks Resend/SMTP y guardrail configurable de lenguaje.
- Selector de extraccion **Normal / OCR**; ambos métodos alimentan al mismo agente Gemini.
- RAG graduado: indicadores calculados, coincidencia literal en PDF, similitud semantica con embeddings cacheados y aclaracion segura.
- Dashboard interactivo con estructura financiera, ventas, resultados, ratios, alertas y flujo de caja, usando únicamente datos calculados del análisis activo.
- Pronostico de ventas de 1 a 12 meses: compara regresion lineal temporal con persistencia mediante backtesting, selecciona el menor MAE y muestra un rango orientativo sin usar Gemini.

Las especificaciones ejecutadas y en curso estan versionadas en `specs/`, incluidas tesoreria, simulacion avanzada y pronostico mensual.

## Arquitectura

```text
Streamlit -> JWT -> FastAPI -> LangGraph
                              |-- extraer PDF -> ratios -> alertas -> resumen
                              `-- indicadores -> literal -> semantica
                                                   |-> responder | aclarar
                                      |
                       Gemini (opcional) + SQLite + MLflow
```

Los nodos de `backend/workflow/nodes/` son adaptadores delgados. Extraccion, calculos, alertas y QA viven en `backend/agent/` y se prueban sin montar el grafo.

### Recuperacion graduada y consumo de cuota

Las preguntas siguen la ruta mas barata que pueda producir evidencia suficiente:

1. Consultas explicitas de ROA, ROE, margen, liquidez y otros indicadores usan datos calculados, sin embeddings.
2. Los hechos del estado financiero se buscan por palabras en los fragmentos PDF, sin embeddings.
3. Solo si lo anterior no alcanza se usa similitud semantica. Los vectores del documento se calculan una vez y se guardan asociados al analisis; las preguntas posteriores solo generan el vector de la consulta.
4. Si no hay evidencia suficiente o Gemini no puede generar embeddings, LangGraph deriva a aclaracion en vez de inventar.

La UI muestra la ruta, confianza y si se reutilizo la cache. MLflow registra esos metadatos, nunca el texto, pregunta, cifras, respuesta o embeddings. Los analisis creados antes de esta version reciben la nueva columna automaticamente y pueden crear la cache de forma diferida.

## Instalacion en Windows

Requiere Python 3.12 recomendado.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_env.py
```

El script crea `.env`, genera un `JWT_SECRET_KEY` aleatorio y conserva el usuario/hash de demo. Abre `.env` y pega tu clave en una sola linea:

```dotenv
GEMINI_API_KEY=pega_aqui_tu_clave
```

No agregues comillas ni subas `.env` al repositorio. `.env.example` documenta todas las variables disponibles.

## Verificacion y ejecucion

```powershell
# Suite completa
python -m pytest tests -q

# Backend
python -m uvicorn backend.main:app --reload

# En otra terminal, frontend
python -m streamlit run frontend/app.py
```

- Frontend: <http://localhost:8501>
- API/Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>
- Login: `admin` / `admin123`
- Login analista: `analista` / `analista123`

El administrador puede crear cuentas desde **Configuración > Usuarios y roles**. Una contraseña nueva debe tener al menos 12 caracteres. Los analistas no ven Configuración y reciben `403` si intentan llamar esos endpoints directamente. Ambos roles pueden abrir **Dashboard**, pero sólo visualizan el análisis activo de su propia sesión.

### Ver las trazas de MLflow

MLflow es el historial técnico del agente: permite comprobar qué nodos de LangGraph se ejecutaron, cuánto tardaron y si terminaron correctamente. La aplicación registra únicamente nombres y cantidades de campos, modelo, versión del prompt, tiempos y tipos de error; no guarda preguntas, texto del PDF, cifras, respuestas, claves ni tokens.

Con el backend detenido o usando otra terminal, abre la interfaz local:

```powershell
.\.venv\Scripts\python.exe -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Visita <http://localhost:5000>, abre el experimento `agente-riesgo-financiero` y selecciona una ejecución `analisis-*` o `chat-*`. Para deshabilitar las trazas usa `MLFLOW_ENABLED=false` en `.env`. `mlflow.db` y `mlruns/` son artefactos locales y no se suben a GitHub.

También puedes iniciar la interfaz con `powershell -ExecutionPolicy Bypass -File scripts/start_mlflow.ps1`. El administrador encontrará en **Configuración > Observabilidad con MLflow** un botón que abre `MLFLOW_UI_URL` (por defecto `http://localhost:5000`). El botón abre la interfaz, pero el proceso MLflow debe estar iniciado.

Si `GEMINI_API_KEY` esta vacia, `/health` muestra `offline-fallback`; la demo sigue funcionando con el PDF sintetico de `data/`. Tambien puedes pegar la clave en **Configuracion > Nueva clave API de Gemini > Probar y guardar**: se valida, guarda en `.env` y activa sin reiniciar, pero nunca se recupera ni muestra.

El proveedor principal de correo es Gmail API por HTTPS. En **Configuración > Correo** la aplicación muestra si faltan credenciales, si existe una autorización y qué cuenta está conectada. Tras autorizar una vez, el refresh token cifrado permite renovar el acceso sin login repetido. Resend y SMTP permanecen como alternativas cuando Gmail no está conectado.

Configuración resumida: habilita Gmail API en Google Cloud, crea un cliente OAuth de tipo **Web application**, registra exactamente `http://localhost:8000/settings/gmail/callback`, agrega tu cuenta como usuario de prueba y pega Client ID/Secret en la UI. La aplicación sólo solicita `gmail.send`, `openid` y `email`; no lee el buzón. Consulta la guía de despliegue para el procedimiento completo y la URI HTTPS que corresponde en producción.

Consulta [`GUIA_PRUEBAS_Y_DESPLIEGUE.md`](GUIA_PRUEBAS_Y_DESPLIEGUE.md) y las llamadas listas para VS Code REST Client en [`docs/pruebas_api.http`](docs/pruebas_api.http).

### Extraccion normal u OCR

- **Normal** lee la capa de texto del PDF y luego Gemini analiza y estructura el contenido.
- **OCR** sirve para PDFs escaneados: Gemini transcribe cada imagen y después el mismo agente analiza el contenido.
- OCR se habilita solo despues de probar correctamente la clave desde Configuracion. Puede tardar mas y consumir cuota. Revisa siempre cifras y alineacion de tablas.

## Controles de seguridad

- `.env`, SQLite, MLflow, temporales y entornos virtuales estan ignorados por Git.
- El algoritmo JWT esta fijado en el servidor; no se acepta desde configuracion ni desde el token.
- Cada JWT referencia una sesión SQLite activa; cerrar sesión o desactivar al usuario revoca el acceso sin esperar la expiración.
- El rol firmado se compara con el rol actual de la base en cada solicitud; un token con rol obsoleto se rechaza.
- Login devuelve el mismo error para usuario o password incorrectos y ejecuta una comprobacion bcrypt tambien para usuarios inexistentes.
- Chat e historial consultan por `(analysis_id, actor autenticado)`; un recurso ajeno devuelve 404.
- Los textos del PDF y del usuario se tratan como no confiables; no controlan autorizacion, persistencia ni calculos.
- Los errores del proveedor y del parser no se devuelven al cliente.
- La configuracion devuelve estados, no claves; los reportes verifican ownership.
- El CSV neutraliza formulas y el correo conserva destinatarios validados y endpoints fijos.
- Preguntas y salidas del modelo atraviesan un filtro configurable de terminos ofensivos.
- Las imagenes temporales del OCR se mantienen en memoria, con limite de paginas/resolucion y sin persistencia.
- Resend usa únicamente `https://api.resend.com`; el cliente no puede modificar la URL y las claves nunca se devuelven.
- Gmail OAuth usa estado temporal de un solo uso; Client Secret y refresh token no se devuelven, y el refresh token se cifra antes de guardarse.

Riesgos residuales y recomendaciones operativas: [`SECURITY.md`](SECURITY.md).

## Funcionalidades extra recomendadas

Prioridad sugerida para una siguiente spec:

1. **Umbrales por sector y versionados**: perfiles para retail, servicios o manufactura, con explicacion de por que dispara cada alerta. Alto valor y esfuerzo moderado.
2. **Comparacion historica y covenants**: varios periodos, tendencias, vencimientos y alertas por incumplimiento. Es el salto mas directo de demo a herramienta analitica.
3. **Sensibilidad de escenarios**: curvas VAN/tasa, caso base/optimista/pesimista y Monte Carlo con supuestos visibles.
4. **OCR para PDFs escaneados**: detectar paginas sin texto y usar OCR local antes de Gemini. Amplia mucho la cobertura de documentos reales.
5. **Revision humana y expediente**: estados `borrador/revisado/aprobado`, comentarios y bitacora; el LLM recomienda, una persona decide.
6. **MFA, recuperación y rotación de credenciales**: completar el ciclo de vida de cuentas antes de una exposición pública.
7. **Cache de embeddings por documento**: reduce latencia y consumo de cuota en preguntas repetidas.

No recomiendo integrar SBS/SMV ni datos reales hasta completar MFA/recuperación, retencion/borrado, cifrado de base de datos, backup/restore y una evaluacion legal de tratamiento de datos.

## Fuentes tecnicas

- [GitHub Spec Kit](https://github.com/github/spec-kit)
- [Modelos Gemini](https://ai.google.dev/gemini-api/docs/models)
- [Embeddings Gemini](https://ai.google.dev/gemini-api/docs/embeddings)
- [Precios y Free Tier de Gemini](https://ai.google.dev/gemini-api/docs/pricing)
- [OAuth 2.0 de Gmail](https://developers.google.com/workspace/gmail/api/auth/web-server)
- [Envío con Gmail API](https://developers.google.com/workspace/gmail/api/guides/sending)
