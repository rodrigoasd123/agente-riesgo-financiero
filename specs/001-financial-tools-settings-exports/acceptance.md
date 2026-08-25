# Acceptance — Configuración Gemini, herramientas financieras, reportes y guardrails

## AC-001 — Configuración segura de Gemini
**Covers:** FR-001, SEC-002

```gherkin
Given un usuario autenticado y una clave válida
When la prueba y guarda desde Configuración
Then el estado indica conexión correcta sin devolver ni mostrar la clave
```

## AC-002 — Respuesta sobre indicador calculado
**Covers:** FR-002

```gherkin
Given un análisis con ROA calculado
When el usuario pregunta para qué sirve el ROA
Then el agente usa la definición y valor estructurados aunque el PDF no contenga la palabra ROA
```

## AC-003 — Escenario financiero
**Covers:** FR-003, NFR-001

```gherkin
Given inversión, tasa y flujos explícitos válidos
When se calcula el escenario
Then se devuelven VAN, TIR si existe, recuperación y flujo acumulado reproducibles
```

## AC-004 — Exportaciones
**Covers:** FR-004, SEC-004

```gherkin
Given un análisis propio
When se exporta en CSV y PDF
Then ambos archivos contienen cifras, indicadores y alertas y el CSV neutraliza fórmulas
```

## AC-005 — Correo
**Covers:** FR-005, SEC-003

```gherkin
Given SMTP configurado y un destinatario válido
When se solicita el envío de un análisis propio
Then el servidor envía el PDF adjunto usando sólo el host configurado
```

## AC-006 — Guardrails
**Covers:** FR-006

```gherkin
Given una pregunta o respuesta con un término bloqueado
When atraviesa el chat
Then se detiene de forma respetuosa sin repetir el término ni invocar/entregar el modelo
```

## AC-007 — Autorización
**Covers:** SEC-001

```gherkin
Given un usuario sin acceso al análisis
When intenta proyectar, exportar o enviar
Then recibe 404/403 sin datos del propietario
```

## AC-008 — Interfaz operativa
**Covers:** FR-007, NFR-002, NFR-003

```gherkin
Given la aplicación local iniciada
When el usuario navega por Análisis, Proyecciones y Configuración
Then observa estados accionables, puede descargar reportes y no ve secretos
```

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | `tests/test_features_api.py`; estado UI inspeccionado | PASS (clave real pendiente del usuario) |
| AC-002 | E2E vivo: ROA encontrado y explicación contiene eficiencia | PASS |
| AC-003 | `tests/test_financial_tools.py`; endpoint vivo VAN 16986.54 | PASS |
| AC-004 | API viva: BOM CSV y firma PDF; PDF de 2 páginas renderizado | PASS |
| AC-005 | Servicio simulado y validación SMTP/destinatario | PASS (SMTP real no configurado) |
| AC-006 | `tests/test_moderation.py` y prueba de ruta | PASS |
| AC-007 | Pruebas JWT/ownership | PASS |
| AC-008 | Login, navegación y estados inspeccionados en localhost:8501 | PASS |
