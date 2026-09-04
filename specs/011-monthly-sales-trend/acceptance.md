# Criterios de aceptación - SPEC-011

- **Estado:** VERIFIED (109 pruebas automatizadas y nueve páginas inspeccionadas el 2026-09-04)

- **AC-001:** Los tres PDF contienen exactamente doce meses y la suma coincide con la venta anual. Evidencia: `test_documentos_generados_incluyen_presupuesto_formula_y_resultado` y extracción real (950000, 1600000, 400000).
- **AC-002:** El fallback extrae los meses presentes en orden sin completar datos ausentes. Evidencia: `test_fallback_extracts_monthly_sales_without_inventing_missing_months`.
- **AC-003:** El dashboard transforma únicamente campos allowlisted y el gráfico no contiene `params`. Evidencia: pruebas de `sales_rows` y `sales_trend_chart`.
- **AC-004:** Una cifra sin desglose mensual conserva la comparación anual existente. Evidencia: regresión de `sales_rows`.
- **AC-005:** Las nueve páginas generadas no presentan cortes ni superposiciones. Evidencia: renderizado Poppler a 120 DPI e inspección visual completa.
