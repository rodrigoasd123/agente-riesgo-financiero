# Implementation plan — Gemini actualizado y correo HTTPS gratuito

## Approach

Mantener adaptadores directos y acotados. Gemini prueba la operación real y traduce códigos del proveedor a causas seguras. Resend usa `requests` contra endpoints fijos, adjunto base64 y configuración dinámica guardada en `.env`. El servicio de correo prioriza Resend y conserva SMTP.

## Components

| Component | Change |
|---|---|
| Gemini client/settings | modelo 3.6, validación real, recarga y causas |
| Email service/settings | adaptador Resend, prueba de key, runtime config |
| Finance route | respuesta de proveedor sin secretos |
| Streamlit | lenguaje Normal/OCR y configuración Resend |
| Tests/docs | contratos simulados, fallos y operación |

## Security

Los secretos sólo viajan del campo password al backend autenticado y al proveedor HTTPS. Se persisten tras prueba correcta. No se aceptan URLs ni hosts Resend del cliente. El adjunto se limita al PDF ya generado y autorizado.

## Verification

Unit tests de clasificación/adaptadores, integración de settings y correo, regresión completa, prueba Gemini real con egress autorizado, Resend simulado si no hay key, y UI desktop/narrow.

