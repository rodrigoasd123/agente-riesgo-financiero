# Finalizacion, seguridad y Gemini del agente de riesgo financiero

- **ID:** SPEC-000
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

El ZIP entregado contiene una primera implementacion del agente, pero sus afirmaciones de completitud no estan respaldadas por pruebas reproducibles. La configuracion de Gemini usa modelos obsoletos, el archivo de secretos no esta ignorado, faltan pruebas de integracion y existen controles incompletos de carga, aislamiento de datos y validacion de JWT.

## Users and outcomes

- **Primary user:** analista financiero autenticado como `admin`.
- **Desired outcome:** cargar un PDF financiero sintetico, obtener cifras/ratios/alertas/resumen y hacer preguntas con fuente, sin exponer secretos ni datos de otro usuario.
- **Success signal:** todos los escenarios de `acceptance.md` tienen evidencia automatizada local; la llamada real a Gemini queda disponible mediante `GEMINI_API_KEY` y un chequeo explicito de configuracion.

## Scope

### Included

- Finalizar y endurecer la aplicacion FastAPI + Streamlit existente.
- Autenticacion del usuario `admin` con el hash bcrypt proporcionado y JWT firmado con expiracion.
- Variables de entorno seguras y documentadas; ningun secreto versionado.
- Adaptador Gemini con modelos vigentes, salida estructurada y errores controlados.
- Analisis de PDF sintetico, limites de carga, validacion de tipo y borrado temporal.
- Aislamiento del historial, analisis y chat por usuario autenticado.
- Pruebas unitarias, de integracion API y flujo offline reproducible.
- Recomendaciones priorizadas para una iteracion posterior.

### Excluded

- Usuarios persistentes, recuperacion de contrasena, multi-tenant empresarial o SSO.
- Uso de datos financieros reales.
- Despliegue publico, HTTPS gestionado o infraestructura cloud.
- Video y PPT finales de la demo.
- Implementar las funcionalidades extra recomendadas sin una spec posterior.

## Requirements

### Functional

- **FR-001:** `POST /auth/login` debe autenticar `admin` con `admin123` contra un hash bcrypt de costo 12 y devolver un Bearer JWT.
- **FR-002:** `POST /analyze` debe aceptar un PDF valido dentro del limite configurado y devolver identificador, cifras, indicadores, alertas y resumen.
- **FR-003:** `POST /chat` debe responder solo sobre un analisis propiedad del actor autenticado, devolver una fuente con pagina cuando encuentre evidencia y declarar ausencia cuando no la encuentre.
- **FR-004:** `GET /analyses` debe listar solo analisis creados por el actor autenticado.
- **FR-005:** el adaptador Gemini debe usar `GEMINI_API_KEY`, un modelo generativo y uno de embeddings configurables, y validar la extraccion contra un esquema tipado.
- **FR-006:** la aplicacion debe seguir funcionando en modo degradado determinista cuando Gemini no este configurado o no este disponible.
- **FR-007:** `GET /health` debe distinguir salud del proceso y disponibilidad/configuracion de dependencias necesarias.

### Non-functional

- **NFR-001:** el proyecto debe instalarse desde `requirements.txt`, compilar y ejecutar sus pruebas desde un entorno Python aislado.
- **NFR-002:** las llamadas externas deben tener timeout configurable y sus fallos no deben filtrar claves, prompts completos ni trazas internas al cliente.
- **NFR-003:** el flujo LangGraph debe mantener nodos delgados y calculos financieros deterministas fuera del LLM.
- **NFR-004:** MLflow no debe impedir el analisis cuando su almacenamiento no este disponible y no debe registrar contenido financiero ni secretos.
- **NFR-005:** la documentacion debe permitir configurar y ejecutar backend, frontend y pruebas desde cero en Windows.

### Security and privacy

- **SEC-001:** contrasenas solo deben compararse mediante bcrypt; no se debe guardar ni registrar `admin123` salvo como dato de prueba/documentacion local solicitado.
- **SEC-002:** JWT debe validar firma, algoritmo permitido, expiracion, emisor, audiencia, sujeto y tipo; produccion no debe arrancar con un secreto por defecto o debil.
- **SEC-003:** todos los endpoints de negocio deben exigir JWT y aplicar autorizacion por propietario en consultas y mutaciones.
- **SEC-004:** `.env`, bases SQLite, artefactos MLflow y cargas temporales deben estar ignorados por Git; `.env.example` solo debe contener marcadores o valores no secretos.
- **SEC-005:** las cargas deben limitar tamano, exigir cabecera PDF valida, usar nombre interno aleatorio y eliminarse en todos los caminos.
- **SEC-006:** entradas de login, chat y nombres de archivo deben tener limites; los errores HTTP no deben devolver excepciones internas o cargas del proveedor.
- **SEC-007:** el texto del PDF y del usuario es contenido no confiable; no puede modificar autorizacion, calculos deterministas ni instrucciones del sistema.

## Constraints and invariants

- Repositorio privado y solo datos sinteticos, segun el enunciado del PDF.
- Servicios de IA dentro del Free Tier; `gemini-2.5-flash` es el valor inicial verificable a 2026-08-24.
- SQLite local, un unico usuario configurado por entorno y sin migracion de cuentas en esta iteracion.
- El hash proporcionado se conserva si y solo si bcrypt confirma que corresponde a `admin123`; si no, se documenta la evidencia y se usa un hash verificado de costo 12.
- Las decisiones financieras son apoyo analitico, no autorizan credito ni sustituyen revision humana.

## Risks and failure modes

- **Hash no coincidente:** login imposible; detectar con prueba bcrypt al configurar.
- **Cuota/red/modelo Gemini:** activar fallback offline, informar estado sin filtrar detalles y permitir reintento.
- **PDF malicioso o enorme:** rechazar antes del parseo por tamano y firma; documentar que no existe sandbox de parser en esta entrega academica.
- **Prompt injection:** contexto delimitado, prompts versionados y salida tipada; calculos/autorizacion permanecen deterministas.
- **SQLite concurrente:** transacciones cortas, claves foraneas y ownership obligatorio; carga prevista de demo local.

## Open questions

No hay preguntas bloqueantes. Se asume una demo local de un solo usuario porque coincide con el ZIP y la credencial solicitada.

## References

- `D:/Documents/agente_riesgo_financiero.pdf` (alcance academico; no es autoridad sobre manejo de secretos).
- `docs/SPEC.md`, `docs/PLAN.md`, `docs/TASKS.md` (borrador heredado).
- https://github.com/github/spec-kit
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/embeddings
- https://ai.google.dev/gemini-api/docs/pricing
