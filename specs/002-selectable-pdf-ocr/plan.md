# Implementation plan — Selección de extracción PDF normal u OCR con Gemini

## Approach

Añadir un parámetro enum al endpoint actual y al estado de LangGraph. Mantener la ruta normal intacta. Para OCR, renderizar páginas con PyMuPDF a PNG en memoria y usar una llamada Gemini directa y acotada por página; luego reutilizar chunks, extracción estructurada, indicadores, alertas y reportes.

## Components

| Component | Change |
|---|---|
| Config/Gemini adapter | límites y transcripción de imagen |
| PDF reader/graph | estrategia seleccionada y metadata |
| Analyze API/DB | campo multipart compatible y modo persistido |
| Settings/health | disponibilidad OCR |
| Streamlit | selector, ayuda, bloqueo y resultado |
| Tests/docs | contratos, fallos y regresión |

## Compatibility and rollout

`extraction_mode` es opcional y por defecto `normal`. La columna SQLite se agrega con migración idempotente y valor por defecto. Rollback ignora la columna adicional.

## Verification

Pruebas unitarias con cliente Gemini simulado; integración de enum, auth y persistencia; regresión completa; UI real en escritorio y viewport estrecho. La conexión OCR real queda condicionada a la clave del usuario.

