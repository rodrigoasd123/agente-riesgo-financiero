# Acceptance — Selección de extracción PDF normal u OCR con Gemini

## AC-001 — Compatibilidad normal
Given una carga sin modo, when se analiza, then usa normal y conserva resultados previos.

## AC-002 — OCR exitoso
Given Gemini configurado y páginas escaneadas, when se elige OCR, then transcribe cada página y devuelve cifras con `extraction_mode=ocr`.

## AC-003 — OCR no disponible
Given Gemini no configurado, when se elige OCR, then devuelve 409 accionable sin llamadas ni archivos persistidos.

## AC-004 — Límites y seguridad
Given demasiadas páginas o modo inválido, when se carga, then rechaza la solicitud sin exponer datos internos; auth/upload/cleanup permanecen activos.

## AC-005 — Interfaz
Given un usuario autenticado, when elige el modo, then ve requisitos y estado OCR, y la selección viaja al backend.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | E2E vivo normal; regresión completa | PASS |
| AC-002 | Render PNG y adaptador Gemini simulados por página | PASS (clave real pendiente del usuario) |
| AC-003 | API viva sin clave devuelve 409 | PASS |
| AC-004 | Enum, límite y fallo de proveedor sanitizado | PASS |
| AC-005 | Navegador desktop y 390x844, sin errores de consola | PASS |
