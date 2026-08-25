# Implementation plan — Finalizacion, seguridad y Gemini del agente de riesgo financiero

## Approach

Conservar la arquitectura existente y cerrar sus brechas en la capa responsable: configuracion validada al arrancar, auth JWT/bcrypt, repositorio SQLite con ownership, adaptador Gemini tipado, validacion de archivos en la ruta y pruebas API completas. No se agrega una plataforma de usuarios ni infraestructura externa.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| `backend/config.py` | configuracion tipada, secretos fuertes, modelos/limites/timeouts | Backend |
| `backend/auth/` | JWT completo, bcrypt y contratos acotados | Security |
| `backend/db/database.py` | claves foraneas y consultas por propietario | Backend |
| `backend/api/` | contratos explicitos, upload seguro, errores sanitizados | Backend |
| `backend/agent/` | Gemini estructurado, prompt versionado, citas por pagina | AI |
| `backend/observability/` | trazas redacted y tolerantes a fallo | AI/Operations |
| `frontend/app.py` | expiracion/errores de sesion y timeouts | Frontend |
| `tests/` | auth, API, ownership, archivos y agente offline | QA |
| `.env.example`, README | operacion reproducible sin secretos | Operations |

## Data and control flow

1. Login valida Pydantic -> bcrypt -> JWT con claims cerrados.
2. Analyze valida token -> tamano/firma PDF -> archivo temporal aleatorio -> LangGraph -> persistencia con `created_by` -> respuesta tipada -> borrado.
3. Chat valida token -> carga analisis por `(id, created_by)` -> retrieval -> respuesta/clarification -> persiste pregunta del mismo actor.
4. Gemini recibe solo el texto necesario; la extraccion se valida con Pydantic. Los calculos, ownership y persistencia nunca dependen del modelo.

## Data model and API changes

- Migrations: inicializacion idempotente habilita claves foraneas e indices de propietario; compatible con la tabla existente.
- Compatibility: se mantienen rutas y campos actuales; health agrega detalle. Los errores se vuelven menos verbosos.
- API contracts: modelos Pydantic con longitudes, filename sanitizado para respuesta, limite de upload configurable.

## Security and privacy

- Authentication: HS256 fijado, claims `iss`, `aud`, `sub`, `type`, `iat`, `nbf`, `exp`, `jti` validados.
- Authorization: actor derivado exclusivamente del JWT; queries por propietario.
- Secrets: `.env` ignorado; arranque falla si faltan hash o secreto seguro fuera de tests.
- Uploads: limite, magic bytes `%PDF-`, nombre interno UUID, cleanup garantizado.
- AI: documentos son datos no confiables, salida tipada y calculos deterministas.

## Observability and failure handling

- MLflow registra version de prompt/modelo, duracion y nombres de campos, no textos ni secretos.
- Excepciones de Gemini activan fallback; endpoints devuelven mensajes estables y se conserva detalle solo en logging local sanitizado.
- Readiness refleja configuracion de Gemini sin llamar al proveedor.

## Rollout and rollback

- Deployment order: copiar `.env.example` -> establecer secretos -> instalar -> probar -> iniciar API -> iniciar Streamlit.
- No migracion destructiva. Rollback: revertir codigo; el esquema SQLite conserva columnas existentes.
- El `.env` extraido se elimina del arbol de trabajo tras verificar que no contiene una clave que deba preservarse.

## Verification strategy

- Unit: bcrypt/JWT, ratios, alertas, retrieval y validacion de configuracion.
- Integration: login, auth requerida, PDF valido/invalido/grande, ownership, chat y health con TestClient.
- End-to-end local: login -> analizar PDF sintetico -> preguntar -> historial usando fallback sin red.
- Manual: smoke opcional de Gemini cuando el usuario agregue su clave.
