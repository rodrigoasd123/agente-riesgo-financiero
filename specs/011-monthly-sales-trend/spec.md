# Evolución mensual de ventas en documentos de prueba

- **ID:** SPEC-011
- **Estado:** VERIFIED
- **Fecha:** 2026-09-04

## Problema

Los PDF sintéticos solo contienen ventas anuales de dos periodos. El dashboard muestra dos barras y no permite evidenciar estacionalidad, deterioro gradual o crecimiento dentro del año.

## Alcance

- Añadir doce ventas mensuales sintéticas de 2025 a cada PDF de prueba.
- Mantener la suma mensual consistente con la venta anual publicada.
- Extraer la serie como datos estructurados mediante Gemini o fallback determinístico.
- Mostrar una línea de evolución mensual en el dashboard.
- Conservar las dos barras anuales cuando un documento no contenga desglose mensual.

## Requisitos

- **FR-001:** Cada PDF debe incluir enero a diciembre en orden y la suma debe coincidir con ventas 2025.
- **FR-002:** La extracción debe devolver `ventas_mensuales` sin inventar meses ausentes.
- **FR-003:** El dashboard debe preferir la serie mensual y mostrar importe y variación mensual en tooltip.
- **FR-004:** Documentos anteriores deben seguir mostrando comparación anual.
- **NFR-001:** No se deben añadir dependencias.
- **NFR-002:** El gráfico no debe generar `params` de Vega-Lite para conservar compatibilidad con el laboratorio.
- **SEC-001:** Solo se grafican mes, orden, importe y variación; el texto del PDF no se pasa al gráfico.

## Exclusiones

- Pronósticos de ventas.
- Datos reales de empresas.
- Inferencia de meses no presentes.
