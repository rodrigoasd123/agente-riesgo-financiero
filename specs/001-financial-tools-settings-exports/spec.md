# Configuración Gemini, herramientas financieras, reportes y guardrails

- **ID:** SPEC-001
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

La aplicación no permite verificar ni actualizar la clave de Gemini desde la interfaz, y las preguntas sobre indicadores calculados (por ejemplo ROA) sólo consultan texto extraído del PDF. Tampoco ofrece proyecciones financieras, exportaciones, envío por correo ni moderación básica del chat.

## Users and outcomes

- Primary user: analista financiero autenticado.
- Desired outcome: configurar Gemini de forma segura, comprender los indicadores, calcular escenarios explícitos y distribuir un reporte reproducible.
- Success signal: los flujos funcionan en UI/API, los cálculos son deterministas y las pruebas de seguridad y aceptación pasan.

## Scope

### Included

- Estado, prueba y almacenamiento local de una clave Gemini mediante un campo secreto.
- Contexto estructurado de indicadores calculados para responder preguntas como “¿para qué sirve el ROA?”.
- VAN, TIR, recuperación y tabla de flujo a partir de inversión y flujos ingresados explícitamente.
- Exportación CSV y PDF del análisis y escenario; envío del PDF por SMTP configurado por entorno.
- Filtro de términos ofensivos en entrada y salida del agente.
- Interfaz Streamlit y documentación operativa/pruebas.

### Excluded

- Inferir flujos de caja ausentes del estado financiero.
- Mostrar o recuperar la clave Gemini almacenada.
- Servicio de correo incorporado o credenciales SMTP provistas por la aplicación.
- Reemplazar la revisión profesional o dar recomendaciones de inversión autónomas.

## Requirements

### Functional

- **FR-001:** Un usuario autenticado puede consultar si Gemini está configurado y probar/guardar una clave válida sin recibirla de vuelta.
- **FR-002:** El chat incluye cifras, indicadores, definiciones y alertas del análisis como contexto además del texto del PDF.
- **FR-003:** El sistema calcula VAN, TIR y periodo de recuperación a partir de una inversión inicial, tasa de descuento y flujos explícitos, y explica cuando TIR/recuperación no existen.
- **FR-004:** Un usuario puede descargar el análisis autorizado como CSV UTF-8 y PDF, opcionalmente con el escenario financiero actual.
- **FR-005:** Un usuario puede enviar el PDF a una dirección válida cuando SMTP está configurado.
- **FR-006:** El chat rechaza lenguaje ofensivo configurado y evita entregar una salida ofensiva.
- **FR-007:** La UI ofrece secciones claras de Análisis, Proyecciones y reportes, y Configuración.

### Non-functional

- **NFR-001:** Los cálculos financieros usan aritmética decimal y resultados deterministas.
- **NFR-002:** Los fallos de Gemini/SMTP producen mensajes accionables, sin revelar secretos ni trazas internas.
- **NFR-003:** El PDF es legible, paginado y visualmente verificado; el CSV abre correctamente en hojas de cálculo.
- **NFR-004:** Las capacidades existentes de carga, análisis, autenticación y chat mantienen compatibilidad.

### Security and privacy

- **SEC-001:** Todos los endpoints nuevos exigen JWT; exportación y correo verifican la propiedad del análisis.
- **SEC-002:** Claves Gemini/SMTP nunca se devuelven, registran ni incluyen en reportes; la clave Gemini sólo se persiste tras una prueba correcta.
- **SEC-003:** El servidor SMTP se toma exclusivamente del entorno, no de datos controlados por el usuario.
- **SEC-004:** El CSV neutraliza celdas de texto que puedan interpretarse como fórmulas.
- **SEC-005:** Los nombres de archivo, destinatarios y entradas financieras se validan y acotan.

## Constraints and invariants

- Gemini usa el SDK oficial `google-genai` y el modelo configurado por entorno.
- La clave se guarda en el `.env` local del proyecto; producción debe usar un gestor de secretos.
- La TIR requiere al menos un flujo negativo y uno positivo; no se inventan datos faltantes.
- El PDF identifica cifras calculadas y mantiene una advertencia de revisión humana.

## Risks and failure modes

- Clave inválida/cuota agotada: la prueba falla y no reemplaza la configuración activa.
- Escenario sin cambio de signo o múltiples TIR: se informa resultado no disponible/estimación acotada.
- SMTP ausente o caído: se conserva la descarga y se devuelve un error 503 sanitizado.
- Inyección de prompt: el agente recibe instrucciones de usar sólo contexto financiero y no exponer configuración.

## Open questions

Ninguna bloqueante. El usuario proveerá la clave Gemini y, si desea correo real, credenciales SMTP.

## References

- `specs/000-project-completion-security-gemini`
- https://github.com/github/spec-kit
