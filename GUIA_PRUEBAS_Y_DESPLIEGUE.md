# Guía de pruebas y despliegue

## 1. Preparar el entorno

Requisitos: Windows, Python 3.12 y acceso de red a Gemini sólo si se probará el modo IA.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_env.py
```

Si `.env` ya existe, no ejecutes `setup_env.py --force`: reemplazaría el secreto JWT y cerraría sesiones activas.

Credenciales de demostración:

- Usuario: `admin`
- Contraseña: `admin123`
- El servidor compara la contraseña contra bcrypt costo 12; no almacena texto plano.

## 2. Configurar Gemini

1. Inicia backend y frontend.
2. Entra a **Configuración**.
3. Pega la clave en el campo secreto.
4. Pulsa **Probar y guardar**.
5. Confirma el estado verde “Gemini conectado”.

El modelo predeterminado es `gemini-3.6-flash`. La aplicación clasifica por separado clave inválida, modelo no disponible, cuota y bloqueo de red. Si pegaste la clave directamente en `.env`, pulsa **Probar clave actual**; ya no es necesario reiniciar.

La clave no se vuelve a mostrar. Si es inválida, no reemplaza la configuración activa. Alternativamente, edita localmente `GEMINI_API_KEY=` en `.env` y usa **Probar clave actual**.

## 3. Configurar Gmail API por OAuth (recomendado)

1. Abre [Google Cloud Console](https://console.cloud.google.com/) y crea o selecciona un proyecto.
2. En **APIs y servicios > Biblioteca**, busca y habilita **Gmail API**.
3. Configura la pantalla de consentimiento OAuth. Para una demo selecciona público externo y agrega tu Gmail en **Test users**.
4. En **Credenciales**, crea un **OAuth Client ID** de tipo **Web application**.
5. En *Authorized redirect URIs* registra exactamente:

   ```text
   http://localhost:8000/settings/gmail/callback
   ```

6. Inicia la aplicación y abre **Configuración > Correo**.
7. Pega el Client ID y Client Secret. La pantalla nunca vuelve a mostrar el secreto.
8. Pulsa **Preparar conexión con Gmail** y después **Abrir Google y autorizar Gmail**.
9. Selecciona tu cuenta, acepta el permiso de envío y vuelve a Configuración.
10. Pulsa **Probar Gmail**. Debe aparecer `Gmail conectado como ...`.

Esta autorización se realiza una sola vez. El backend guarda un refresh token cifrado con una clave derivada del secreto JWT y renueva el acceso automáticamente. Si la pantalla OAuth permanece en modo **Testing**, Google puede expirar la autorización; para una instalación estable cambia la pantalla a **Production** y completa los requisitos que Google solicite.

En un despliegue público cambia `GMAIL_REDIRECT_URI` a una URL HTTPS pública y registra exactamente la misma dirección en Google Cloud. Cambia también `FRONTEND_URL` a la URL pública de Streamlit.

### Fallback Resend opcional

Resend permanece disponible dentro del desplegable de alternativas en Configuración. Se utilizará sólo si Gmail no está autorizado. Para la demostración con `onboarding@resend.dev`, Resend limita el destinatario al correo propietario de su cuenta.

### Fallback SMTP opcional

Añade al `.env` los datos de tu proveedor:

```dotenv
SMTP_HOST=smtp.tu-proveedor.com
SMTP_PORT=587
SMTP_USERNAME=tu_usuario
SMTP_PASSWORD=tu_password_o_app_password
SMTP_FROM_EMAIL=reportes@tu-dominio.com
SMTP_USE_TLS=true
SMTP_TIMEOUT_SECONDS=20
```

Usa una contraseña de aplicación cuando el proveedor lo requiera. No subas `.env`; está ignorado por Git. Reinicia el backend después de cambiar SMTP.

## 4. Ejecutar

Terminal 1:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

Abre <http://localhost:8501>. Swagger está en <http://localhost:8000/docs>.

### Inspeccionar MLflow

Después de ejecutar al menos un análisis, abre una tercera terminal:

```powershell
.\.venv\Scripts\python.exe -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

En <http://localhost:5000> selecciona el experimento `agente-riesgo-financiero`. Una ejecución `analisis-*` muestra los nodos `extractor`, `indicadores`, `alertas` y `resumen`; una ejecución `chat-*` muestra `retrieval` y `answer` o `clarification`. Por nodo se registran duración, estado y nombres/cantidades de campos de entrada y salida. La política `metadata-only-v1` evita almacenar los valores financieros, preguntas, texto del PDF, respuestas y secretos.

## 5. Casos de aceptación manual

1. Inicia sesión con `admin/admin123`.
2. Selecciona **Normal** y carga `data/estado_financiero_ejemplo.pdf` o uno de `output/pdf/`.
3. Verifica cifras, ratios, alertas, resumen y la etiqueta `Extracción: Normal`.
4. Pregunta “¿Para qué sirve el ROA?”: debe responder usando la definición calculada, aunque el PDF no contenga “ROA”.
5. Escribe una consulta con un término de `GUARDRAIL_BLOCKED_TERMS`: debe rechazarse sin invocar al agente.
6. En Proyecciones ingresa inversión `100000`, tasa `10` y flujos `30000, 35000, 40000, 45000`.
7. Verifica VAN, TIR, recuperación y tabla acumulada. Son un escenario del usuario, no datos inferidos.
8. Prepara y descarga CSV/PDF; abre ambos y comprueba cifras y advertencia profesional.
9. Con Gmail conectado, envía el reporte a un buzón de prueba y verifica remitente y los dos adjuntos: PDF y CSV.
10. En Configuración prueba la clave actual y confirma que la UI nunca muestra su valor.
11. Con Gemini conectado, selecciona **OCR** y carga un PDF escaneado de prueba. Confirma `Extracción: OCR` y revisa manualmente todas las cifras; se realiza una llamada por página.
12. Pregunta “¿Qué indican mi ROA y ROE?” y confirma `Recuperación: indicadores calculados`; esta ruta no usa embeddings.
13. Pregunta “¿Cuáles fueron las ventas?” y confirma `Recuperación: coincidencia en el PDF` y una evidencia que empieza por `[Pagina ...]`.
14. Formula una pregunta conceptualmente relacionada pero sin palabras literales. Si Gemini tiene cuota, confirma `similitud semántica`; al repetirla debe aparecer `caché reutilizada`.

## 6. Pruebas automatizadas

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Resultado de esta entrega: `80 passed`. Además se verificaron contra el proveedor real Gemini Normal, OCR y chat ROA. El RAG graduado se verificó con rutas estructurada/literal/semántica/sin evidencia, reducción de llamadas, cache compatible, aislamiento por propietario y metadata privada. Gmail OAuth se verificó con pruebas herméticas del consentimiento, cifrado, renovación, MIME con PDF/CSV, endpoints y fallos. MLflow se verificó con pruebas de trazas exitosas, fallidas, privacidad de valores y tolerancia a indisponibilidad. La advertencia deprecada de ReportLab pertenece a una dependencia. En algunos Windows restringidos, pytest puede mostrar al salir un aviso de permisos sobre su directorio temporal después de completar correctamente las pruebas.

## 7. Archivos para subir

Incluye código, `requirements.txt`, `.env.example`, README, esta guía, `SECURITY.md`, `specs/`, `data/`, `tests/` y `docs/pruebas_api.http`.

No subas `.env`, `.venv/`, bases `*.db`, `mlruns/`, temporales, reportes con datos reales ni credenciales. Verifica antes:

```powershell
git status --short
git check-ignore .env .venv mlflow.db
```

Para un despliegue público todavía se requieren HTTPS, secret manager, rate limiting, RBAC multiusuario, cifrado/backup y sandbox/antivirus para PDFs. Esta entrega está preparada como aplicación local/académica, no como sistema de decisión crediticia de producción.
