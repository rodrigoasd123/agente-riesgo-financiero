# Acceptance — Gmail OAuth email provider

## AC-001 — Inicio autorizado
Given credenciales OAuth y JWT válido, when se inicia la conexión, then se devuelve una URL Google con estado temporal y alcance mínimo.

## AC-002 — Callback seguro
Given código y estado válidos, when vuelve Google, then se consume una vez, cifra el refresh token y redirige sin secretos; estados inválidos/repetidos se rechazan.

## AC-003 — Diagnóstico persistente
Given autorización almacenada, when se prueba Gmail tras reiniciar, then el backend renueva acceso, identifica la cuenta y marca Gmail conectado.

## AC-004 — Envío
Given análisis propio y Gmail conectado, when se envía el reporte, then Gmail recibe un MIME Base64URL con PDF y el endpoint responde proveedor `gmail`.

## AC-005 — Fallos y fallback
Given Gmail ausente o revocado, when corresponde, then la UI pide configurar/reconectar y Resend/SMTP siguen disponibles sin filtrar secretos.

## AC-006 — Operación
Given una cuenta conectada, when el administrador la desconecta, then se borra la autorización cifrada y Gmail deja de ser el proveedor activo.

## AC-007 — Reporte completo por correo
Given un análisis propio y un escenario opcional, when se envía el reporte, then un único mensaje contiene un PDF y un CSV generados con los mismos datos.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | URL OAuth fija, alcance mínimo, estado temporal y JWT probados | PASS |
| AC-002 | Intercambio, cifrado y rechazo de reutilización probados | PASS |
| AC-003 | Renovación y diagnóstico de cuenta probados con proveedor simulado | PASS |
| AC-004 | MIME Base64URL, PDF y prioridad Gmail probados | PASS |
| AC-005 | Errores sanitizados y fallbacks conservados; envío real espera credenciales del usuario | PASS |
| AC-006 | Endpoint autenticado y eliminación local de autorización cubiertos | PASS |
| AC-007 | Pruebas MIME/Resend/SMTP y ruta de reporte confirman PDF+CSV en un solo envío | PASS |
| Regresión/UI | `64 passed`; API 1.5.1 activa con Gmail como proveedor | PASS |
