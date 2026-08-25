# Acceptance — Gemini actualizado y correo HTTPS gratuito

## AC-001 — Gemini funcional
Given una clave válida, when se prueba, then una generación mínima con Gemini 3.6 funciona y el agente se activa.

## AC-002 — Diagnóstico seguro
Given un fallo de red, clave, cuota o modelo, when se prueba, then se devuelve una causa accionable sin detalles/secretos.

## AC-003 — Clave desde entorno
Given una clave pegada en `.env` después del arranque, when se pulsa Probar clave actual, then se valida y activa sin reiniciar.

## AC-004 — Métodos claros
Given la pantalla de análisis, when se elige Normal u OCR, then la UI explica que ambos alimentan al agente Gemini.

## AC-005 — Resend
Given una clave Resend válida, when se configura y envía un análisis propio, then el PDF se entrega mediante HTTPS.

## AC-006 — Fallback y seguridad
Given Resend ausente y SMTP configurado, when se envía, then usa SMTP; recursos ajenos, remitentes inválidos y errores de proveedor se rechazan sin secretos.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | Prueba real `/settings/gemini/test`, análisis Normal/OCR y chat ROA con `gemini-3.6-flash` | PASS |
| AC-002..AC-003 | Pruebas de clasificación y recarga dinámica; clave nunca incluida en respuestas | PASS |
| AC-004 | Verificación visual: selector `Normal`/`OCR` y texto que confirma Gemini en ambos | PASS |
| AC-005 | Pruebas del endpoint HTTPS fijo, adjunto PDF Base64 y proveedor reportado | PASS |
| AC-006 | Pruebas de fallback SMTP, autorización, remitente/CRLF y redirecciones bloqueadas | PASS |
| Regresión | `55 passed` el 2026-08-24; API 1.4.0 reiniciada y saludable | PASS |
