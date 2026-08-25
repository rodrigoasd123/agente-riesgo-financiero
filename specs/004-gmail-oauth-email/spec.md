# Gmail OAuth email provider

- **ID:** SPEC-004
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

El usuario prefiere enviar reportes desde su cuenta Gmail sin puertos SMTP y sin iniciar sesión en cada envío. Debe poder conocer desde la aplicación si las credenciales OAuth existen, si una cuenta quedó autorizada y si la renovación sigue funcionando.

## Users and outcomes

- **Primary user:** administrador local de la demostración.
- **Desired outcome:** conectar Gmail una vez, enviar PDF por HTTPS y diagnosticar la conexión.
- **Success signal:** cuenta identificada, renovación válida y proveedor `gmail` activo.

## Scope

### Included

- OAuth 2.0 web con acceso offline y alcance mínimo `gmail.send`.
- Callback protegido por estado impredecible, temporal y de un solo uso.
- Cifrado local del refresh token y exclusión de entregables.
- Gmail como proveedor prioritario; Resend y SMTP siguen como fallback.
- Estado, prueba y desconexión desde la configuración autenticada.
- Guía paso a paso para Google Cloud local y desplegado.

### Excluded

- Campañas o envíos masivos.
- Lectura del buzón, contactos o mensajes.
- Administración de múltiples cuentas Gmail.

## Requirements

### Functional

- **FR-001:** El sistema debe generar una URL OAuth sólo para un administrador autenticado cuando Client ID, Client Secret y redirect URI estén configurados.
- **FR-002:** El callback debe intercambiar el código, guardar la autorización y redirigir a la aplicación sin mostrar secretos.
- **FR-003:** Configuración debe mostrar credenciales presentes, cuenta conectada, correo autorizado y última prueba.
- **FR-004:** Una autorización persistente debe permitir renovar el acceso y enviar un PDF sin login repetido.
- **FR-005:** Gmail debe ser el proveedor principal, conservando Resend y SMTP como fallback cuando Gmail no esté conectado.
- **FR-006:** El administrador debe poder probar y desconectar Gmail.
- **FR-007:** Cada envío de reporte debe adjuntar en un solo mensaje el PDF y el CSV generados para el mismo análisis y escenario.

### Non-functional

- **NFR-001:** Todas las llamadas a Google deben usar HTTPS, endpoints fijos, timeout y redirecciones deshabilitadas.
- **NFR-002:** Los errores deben ser accionables y no exponer tokens ni respuestas internas.
- **NFR-003:** La integración debe conservar compatibilidad con los endpoints existentes de reportes.

### Security and privacy

- **SEC-001:** La autorización debe solicitar sólo `openid email` y `gmail.send`.
- **SEC-002:** El estado OAuth debe expirar, ser de un solo uso y compararse de forma segura.
- **SEC-003:** El refresh token debe almacenarse cifrado y nunca devolverse por API, UI, logs o ZIP.
- **SEC-004:** Probar, iniciar conexión y desconectar debe requerir JWT válido; sólo el callback validado puede ser público.
- **SEC-005:** Destinatarios y adjuntos deben conservar sus validaciones actuales.

## Constraints and invariants

- Google exige un redirect URI exacto registrado en Google Cloud.
- En modo Testing, una autorización con alcance Gmail puede expirar; para uso estable se publica la pantalla de consentimiento.
- El remitente es siempre la cuenta Google autorizada.

## Risks and failure modes

- Credenciales ausentes: UI muestra instrucciones y no ofrece una conexión falsa.
- Redirect URI diferente: Google rechaza antes del callback; la guía muestra el valor exacto.
- Refresh token revocado/expirado: prueba y envío piden reconectar Gmail.
- Callback repetido o CSRF: estado consumido/rechazado.
- Envío incierto: no se reintenta automáticamente para evitar duplicados.
- Generación parcial: ambos adjuntos se construyen y validan antes de invocar al proveedor; no se envía un correo incompleto.

## Open questions

Ninguna. Se adopta una única cuenta Gmail administradora y fallback compatible.

## References

- `specs/003-gemini-model-resend-email/`
- https://developers.google.com/workspace/gmail/api/auth/web-server
- https://developers.google.com/workspace/gmail/api/guides/sending
