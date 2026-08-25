# Gemini actualizado y correo HTTPS gratuito

- **ID:** SPEC-003
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

La cuenta Gemini del usuario rechaza el modelo 2.5 para usuarios nuevos y la validación no distingue modelo, red, clave o cuota. El despliegue de demostración puede bloquear puertos SMTP. Además, la etiqueta “OCR con Gemini” confunde el método de lectura con el motor del agente.

## Scope

### Included

- Migrar el modelo predeterminado a Gemini 3.6 Flash.
- Validar la capacidad real de generación y clasificar errores sin filtrar secretos.
- Detectar/validar una clave pegada directamente en `.env` sin reinicio.
- Presentar al agente como Gemini y al método de extracción únicamente como Normal/OCR.
- Integrar Resend por HTTPS como proveedor principal, con API key configurada desde UI y PDF adjunto.
- Mantener SMTP como fallback compatible.
- Documentar límites gratuitos y dominio de prueba.

### Excluded

- Crear cuentas, claves o dominios Resend por el usuario.
- Prometer entrega a destinatarios arbitrarios con `onboarding@resend.dev`.
- Eliminar SMTP o convertir el correo en un sistema de campañas.
- Cambiar cálculos financieros deterministas por resultados del modelo.

## Requirements

### Functional

- **FR-001:** Una clave Gemini válida se prueba mediante una generación mínima en el modelo configurado.
- **FR-002:** La prueba informa una causa accionable para red, clave/permisos, cuota o modelo no disponible.
- **FR-003:** “Probar clave actual” carga de forma segura el valor guardado en `.env` y lo activa tras validarlo.
- **FR-004:** La UI explica que Gemini analiza en ambos métodos y que Normal/OCR sólo cambia la extracción.
- **FR-005:** Un administrador puede probar y guardar una clave Resend y remitente sin que la clave se devuelva.
- **FR-006:** Los reportes se envían con PDF por Resend HTTPS cuando está configurado; SMTP queda como fallback.
- **FR-007:** La UI informa restricciones de `onboarding@resend.dev` y permite un remitente de dominio verificado.

### Non-functional

- **NFR-001:** Las llamadas externas tienen timeout y errores sanitizados.
- **NFR-002:** El cambio conserva JWT, ownership, descargas y cálculos.
- **NFR-003:** El proveedor de correo se selecciona en el servidor, nunca desde parámetros de usuario.

### Security and privacy

- **SEC-001:** Claves Gemini/Resend/SMTP no se muestran, registran ni incluyen en excepciones o reportes.
- **SEC-002:** Las URLs de Google y Resend están fijadas por código para evitar SSRF.
- **SEC-003:** Destinatario, remitente y tamaño del adjunto se validan; el reporte sólo puede enviarlo su propietario.
- **SEC-004:** El correo es una acción explícita y no se reintenta automáticamente para evitar duplicados.

## Constraints and risks

- Resend Free ofrece 3,000 correos/mes y 100/día según su página oficial consultada el 2026-08-24.
- `onboarding@resend.dev` sólo entrega al correo de la propia cuenta; otros destinatarios requieren dominio verificado.
- El entorno actual bloquea egress dentro del sandbox; la aplicación desplegada necesita HTTPS saliente.
- Gemini 2.5 respondió que no está disponible para usuarios nuevos; 3.6 es la migración indicada por el proveedor.

## Open questions

Ninguna bloqueante.

## References

- https://ai.google.dev/gemini-api/docs/models
- https://resend.com/pricing
- https://resend.com/docs/api-reference/emails/send-email
