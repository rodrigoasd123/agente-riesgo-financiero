# Plan de implementación — PDFs con disponibilidad de efectivo

## Enfoque

Extender la estructura `SCENARIOS` del generador existente y añadir una segunda página homogénea a cada PDF. La primera página conserva balance, resultados, notas y alertas; la segunda presenta parámetros, presupuesto mensual, método y resultado de disponibilidad.

## Componentes

| Componente | Cambio | Responsable |
|---|---|---|
| `data/generar_documentos_prueba.py` | Nuevos datos, tabla mensual y página de disponibilidad | Datos de prueba |
| `output/pdf/*.pdf` | Tres artefactos regenerados con nombres estables | Datos de prueba |
| `output/GUIA_PRUEBAS.md` | Preguntas y resultados esperados | Documentación |
| `tests/test_documentos_prueba.py` | Verificación de escenarios y contenido PDF | QA |

## Flujo de datos

`SCENARIOS` define cifras sintéticas → ReportLab genera las páginas → pdfplumber reabre y valida el texto → Poppler renderiza PNG → inspección visual confirma el diseño.

## Modelo y compatibilidad

- No hay migración ni cambios de API.
- Se añaden `cash_parameters`, `cash_budget`, `cash_result` y `cash_explanation` al modelo local del generador.
- Se conservan rutas y nombres de los tres PDF.

## Seguridad y privacidad

No se incorporan secretos, información personal ni datos de clientes. Los valores son escenarios ficticios explícitamente rotulados.

## Fallos y observabilidad

El generador imprime las rutas producidas. Las pruebas fallan si faltan textos, resultados o si el caso incompleto inventa disponibilidad.

## Despliegue y reversión

- Regenerar los tres PDF después de actualizar la fuente.
- La reversión consiste en restaurar el generador y los PDF del commit anterior.

## Verificación

- **Unitario:** validar resultados y valores críticos en `SCENARIOS`.
- **Integración:** generar en un directorio temporal y extraer el texto de cada PDF.
- **Manual:** renderizar las seis páginas y revisar tablas, saltos y pies de página.
