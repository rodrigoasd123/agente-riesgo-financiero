# Seguridad

## Alcance de esta entrega

Aplicacion academica local, un usuario administrador, datos exclusivamente sinteticos y sin despliegue publico. JWT y bcrypt protegen la API, pero no convierten por si solos la aplicacion en un servicio financiero de produccion.

## Activos y fronteras

- Secretos: `GEMINI_API_KEY`, OAuth Client Secret/refresh token de Gmail, `RESEND_API_KEY`, `JWT_SECRET_KEY`, hash del password y credenciales SMTP.
- Datos: PDF temporal, texto/chunks, cifras, ratios, preguntas e historial SQLite.
- Fronteras: navegador -> Streamlit -> FastAPI -> SQLite/MLflow/Gemini/Google OAuth/Gmail/Resend/SMTP.
- Contenido no confiable: nombres/bytes del archivo, texto del PDF, preguntas y respuestas del proveedor.

## Controles verificados

- bcrypt costo 12 y prueba positiva/negativa.
- JWT firmado con claims requeridos y rechazo de token ausente, invalido o expirado.
- Ownership en historial, lectura y persistencia de preguntas.
- Limite de upload, magic bytes, nombre interno UUID y cleanup.
- Salida Gemini tipada; errores sanitizados y fallback offline.
- `.env`, bases, temporales y trazas fuera de Git.
- Configuracion Gemini de escritura unidireccional: prueba previa, sin lectura del secreto.
- Exportaciones bajo ownership, neutralizacion de formulas CSV y nombres saneados.
- SMTP controlado por entorno para evitar SSRF; destinatarios acotados y validados.
- Resend limitado a un endpoint HTTPS fijo, clave de escritura unidireccional, adjunto acotado y sin reintentos automáticos.
- Gmail limitado a endpoints HTTPS fijos, alcance `gmail.send`, estado OAuth temporal/de un uso y refresh token cifrado en reposo; no hay reintento automático del envío.
- Guardrail determinista en pregunta y salida; no sustituye moderacion especializada.
- OCR con limite de paginas/resolucion; las imagenes renderizadas existen solo en memoria y no se registran ni persisten.

## Riesgos residuales antes de produccion

- No hay HTTPS gestionado, rate limiting distribuido, MFA, revocacion de JWT ni recuperacion segura de cuentas.
- SQLite y MLflow no estan cifrados en reposo y no existe politica automatica de retencion/borrado.
- Los parsers PDF no se ejecutan en un sandbox separado; archivos hostiles siguen siendo un riesgo.
- El Free Tier de Gemini puede usar datos para mejorar productos segun la configuracion/terminos vigentes; no enviar datos reales.
- Los umbrales financieros son generales y no estan calibrados por industria ni validados para decisiones crediticias.
- El filtro de palabras puede tener evasiones o falsos positivos; produccion requiere evaluacion adversarial y una politica versionada.
- OCR con Gemini transmite las paginas renderizadas al proveedor y puede cometer errores de transcripcion; no usar documentos reales sin revisar privacidad, terminos y base legal.
- El cifrado del refresh token depende de `JWT_SECRET_KEY`; al rotarlo será necesario volver a conectar Gmail.

Antes de exponer la app: proxy HTTPS, secret manager, RBAC persistente, rate limiting, antivirus/sandbox de archivos, cifrado/backup, auditoria inmutable, evaluaciones de prompt injection y revision legal de datos.
