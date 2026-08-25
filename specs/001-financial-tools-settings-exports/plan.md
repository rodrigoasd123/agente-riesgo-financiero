# Implementation plan — Configuración Gemini, herramientas financieras, reportes y guardrails

## Approach

Ampliar el monolito FastAPI/Streamlit con servicios puros para cálculos, moderación y generación de reportes. Mantener las credenciales y destinos de infraestructura en configuración del servidor, y reutilizar la comprobación de propiedad existente para todas las operaciones sobre análisis.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| Gemini client/settings routes | configuración dinámica, prueba y estado seguro | Backend |
| Financial tools | VAN/TIR/recuperación deterministas | Backend |
| Chat context/moderation | indicadores estructurados y guardrails | AI/backend |
| Reporting/email | CSV, PDF y SMTP | Backend |
| Streamlit | tres flujos de usuario y estados de error | Frontend |
| Tests/docs | regresión, aceptación y operación | QA |

## Data and control flow

La UI envía JWT en cada llamada. Configuración prueba una clave con Gemini antes de actualizar memoria y `.env`. Proyecciones consumen únicamente números explícitos. Reportes cargan el análisis mediante el repositorio autorizado, generan bytes en memoria y los descargan o adjuntan por SMTP. El chat modera entrada, construye contexto estructurado y modera salida.

## Data model and API changes

- Migrations: ninguna; escenarios y reportes son efímeros.
- Compatibility: endpoints existentes se mantienen.
- API contracts: `/settings/status`, `/settings/gemini`, `/analyses/{id}/projection`, `/analyses/{id}/report/csv`, `/analyses/{id}/report/pdf`, `/analyses/{id}/email`.

## Security and privacy

- JWT obligatorio y propiedad por `user_id` para recursos.
- Secretos sólo en memoria/entorno; respuestas exponen booleanos y modelo, no valores.
- SMTP fijo por entorno; destinatario validado; CSV neutralizado; filenames saneados.
- Guardrails en ambos límites del modelo y errores externos sanitizados.

## Observability and failure handling

Errores de proveedor se clasifican como configuración/no disponibilidad y no incluyen payloads sensibles. Se registran sólo eventos genéricos. No hay reintentos automáticos de correo para evitar duplicados.

## Rollout and rollback

- Desplegar código y variables opcionales; funciones de descarga trabajan sin SMTP/Gemini.
- No hay migraciones. El rollback consiste en volver al código anterior y retirar las nuevas variables.

## Verification strategy

- Unit: cálculos, moderación, contexto, sanitización.
- Integration: auth/ownership, settings simulados, CSV/PDF, correo simulado.
- End-to-end: login, análisis existente, proyección, descargas y estado Gemini en Streamlit.
- Manual evidence: PDF renderizado y captura/inspección de la UI local.

