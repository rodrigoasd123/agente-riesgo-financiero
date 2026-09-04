# Integración del simulador de inversión y tesorería

- **ID:** SPEC-010
- **Estado:** VERIFIED
- **Fecha:** 2026-09-04
- **Origen:** adaptación de `feature/009-investment-treasury-simulation` sobre `master`

## Problema

La rama de simulación contiene una calculadora útil, pero no está integrada en la rama principal y entra en conflicto con las mejoras visuales y de compatibilidad del laboratorio. Además, mezcla `float` con importes `Decimal`, fija la moneda en dólares y presenta una estimación simplificada del excedente como recomendación.

## Usuarios y resultado

- Analistas y administradores autenticados.
- Tras analizar un PDF, pueden estimar un excedente de tesorería y simular una colocación educativa con supuestos explícitos.
- El sistema muestra cálculos transparentes, moneda configurable, advertencias y un gráfico compatible con el laboratorio.

## Alcance

### Incluido

- Diagnóstico de excedente basado en efectivo, efectivo restringido/reserva documental cuando estén disponibles y una reserva porcentual de respaldo.
- Simulación mensual determinística con capital inicial, aportes, tasa, frecuencia, comisiones e impuesto.
- API protegida y aislada por propietario.
- Interfaz integrada en la pestaña de proyecciones y reportes.
- Gráfico Altair sin parámetros Vega-Lite interactivos.
- Pruebas unitarias, de contrato, autorización y compatibilidad visual.

### Excluido

- Cotizaciones bursátiles, recomendaciones de instrumentos y ejecución de órdenes.
- Predicción de retornos con IA.
- Persistencia histórica de simulaciones.
- Asesoría legal, tributaria o de inversión.

## Requisitos funcionales

- **FR-001:** El sistema debe indicar si el excedente puede calcularse y no convertir datos ausentes en cero disponible.
- **FR-002:** El diagnóstico debe descontar efectivo restringido y usar la reserva mínima del documento cuando exista; en caso contrario debe usar el porcentaje configurado sobre el pasivo corriente.
- **FR-003:** La simulación debe aceptar capital, plazo, tasa, frecuencia, aportes, comisiones, impuesto y moneda.
- **FR-004:** La respuesta debe incluir evolución mensual, total aportado, saldo bruto/neto, ganancia neta, ROI, costos y una advertencia educativa.
- **FR-005:** La interfaz debe permitir usar escenarios de 30 %, 60 % y 90 % del excedente, identificándolos como escenarios y no como recomendaciones.
- **FR-006:** El frontend debe conservar los resultados ante errores recuperables y mostrar mensajes accionables.

## Requisitos no funcionales

- **NFR-001:** Todos los cálculos monetarios y de tasa deben usar `Decimal`; no se permiten conversiones a `float` en la lógica financiera.
- **NFR-002:** La funcionalidad no debe agregar dependencias nuevas.
- **NFR-003:** Los gráficos deben funcionar con la versión instalada de Altair y no generar `params` en Vega-Lite.
- **NFR-004:** La interfaz debe usar la composición y el tema actuales de `master`.
- **NFR-005:** El backend debe iniciar aunque PyMuPDF no esté disponible; solo el modo OCR puede depender de él.

## Seguridad

- **SEC-001:** Los endpoints deben exigir JWT válido.
- **SEC-002:** El análisis debe obtenerse usando el usuario autenticado; un usuario diferente recibe 404.
- **SEC-003:** Pydantic debe limitar importes, plazo, tasas, porcentajes, moneda y frecuencia.
- **SEC-004:** Los cálculos no deben invocar Gemini ni enviar datos a servicios externos.

## Riesgos y decisiones

- La disponibilidad calculada es una estimación educativa. La UI y la API deben explicarlo.
- Si el documento no contiene efectivo, el diagnóstico será `calculable=false`.
- La reserva documental tiene prioridad sobre el porcentaje estimado.
- Los aportes mensuales se aplican al final de cada mes.
