# Implementation plan — Gmail OAuth email provider

## Approach

Añadir un adaptador Gmail REST al servicio de correo existente. El backend crea el consentimiento OAuth, consume un estado efímero, cifra el refresh token con una clave derivada del secreto JWT y renueva access tokens para cada prueba o envío.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| `backend/gmail_service.py` | OAuth, cifrado, renovación, diagnóstico y envío | Backend |
| `backend/api/routes_settings.py` | Contratos de estado, inicio, prueba, callback y desconexión | Backend |
| `backend/email_service.py` | Prioridad Gmail y fallbacks | Backend |
| `frontend/app.py` | Estado, instrucciones y botones Gmail | Frontend |
| `.env.example` y guías | Configuración Google Cloud | Operations |

## Data and control flow

JWT autenticado → URL OAuth con estado temporal → Google → callback público con estado/código → token endpoint fijo → cifrado y persistencia local → redirect al frontend. Para enviar: autorización del análisis → PDF generado → refresh HTTPS → Gmail `messages.send`.

## Data model and API changes

- **Migrations:** ninguna; secretos operativos permanecen en `.env`.
- **Compatibility:** `/analyses/{id}/email` no cambia.
- **API contracts:** `POST /settings/gmail/authorize`, `GET /settings/gmail/callback`, `POST /settings/gmail/test`, `DELETE /settings/gmail`.

## Security and privacy

- JWT para acciones de administración; callback por estado de 256 bits, TTL 10 minutos y uso único.
- Refresh token cifrado con Fernet y clave derivada de `JWT_SECRET_KEY`.
- Endpoints Google constantes, sin redirecciones, con timeout.
- Ningún token aparece en respuestas ni errores.

## Observability and failure handling

Estado seguro por categorías: no configurado, reconexión requerida, red, cuota o proveedor. Sin reintento automático del envío.

## Rollout and rollback

- Añadir variables Gmail, reiniciar backend y conectar desde UI.
- Sin Gmail conectado, Resend/SMTP conservan el comportamiento anterior.
- Rollback: desconectar Gmail o eliminar las variables Gmail.

## Verification strategy

- **Unit:** estado OAuth, cifrado, token refresh, send MIME, errores y endpoints fijos.
- **Integration:** rutas autenticadas, callback y selección de proveedor.
- **End-to-end:** UI local en escritorio y viewport estrecho.
- **Manual:** confirmar valores de configuración y flujo pendiente cuando aún no hay credenciales reales.
