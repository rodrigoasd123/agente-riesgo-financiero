# Selección de extracción PDF normal u OCR con Gemini

- **ID:** SPEC-002
- **Status:** VERIFIED
- **Created:** 2026-08-24
- **Owner:** Product and engineering

## Problem

La carga actual sólo extrae la capa de texto del PDF. Los estados financieros escaneados no contienen texto consultable y requieren OCR, pero el usuario necesita decidir cuándo asumir el mayor tiempo y consumo del modelo.

## Scope

### Included

- Selector Normal / OCR con Gemini antes del análisis.
- Contrato API compatible mediante campo multipart opcional `extraction_mode`.
- Render de páginas a imagen y transcripción acotada con Gemini.
- Estado de disponibilidad OCR en Configuración/API.
- Registro del modo usado en la respuesta y persistencia del análisis.
- Pruebas, documentación y paquete actualizado.

### Excluded

- Tesseract u otro OCR instalado globalmente.
- Procesamiento OCR sin una clave Gemini válida.
- Detección automática que cambie silenciosamente de modo.
- OCR manuscrito o garantía de exactitud; las cifras siguen requiriendo revisión humana.

## Requirements

### Functional

- **FR-001:** El usuario puede elegir `normal` u `ocr`; normal permanece predeterminado.
- **FR-002:** Normal conserva la extracción de texto existente.
- **FR-003:** OCR renderiza cada página admitida, solicita una transcripción literal a Gemini y procesa ese texto con el flujo financiero existente.
- **FR-004:** OCR sin Gemini configurado falla antes de procesar con un mensaje accionable.
- **FR-005:** La respuesta de análisis indica el modo realmente utilizado.

### Non-functional

- **NFR-001:** OCR limita cantidad de páginas, resolución y timeout para controlar latencia/costo.
- **NFR-002:** Los errores de proveedor no exponen claves, imágenes ni trazas internas.
- **NFR-003:** La UI explica el costo/latencia y preserva la selección tras errores recuperables.
- **NFR-004:** El modo normal y todos los contratos previos siguen siendo compatibles.

### Security and privacy

- **SEC-001:** JWT, validación PDF, límite de tamaño, temporales UUID y cleanup se aplican a ambos modos.
- **SEC-002:** Las imágenes OCR se mantienen en memoria y no se persisten ni registran.
- **SEC-003:** El texto visible se trata como datos no confiables; el prompt sólo permite transcripción literal.

## Constraints and risks

- OCR requiere Gemini conectado y puede consumir cuota por página.
- Las tablas complejas pueden perder alineación; el reporte debe advertir revisión.
- Los PDF mayores al límite de páginas OCR se rechazan antes de llamadas al proveedor.
- No hay preguntas bloqueantes: el selector nombrará explícitamente “OCR con Gemini”.

## References

- `specs/001-financial-tools-settings-exports`
