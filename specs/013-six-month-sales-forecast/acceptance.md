# Aceptación — SPEC-013

- **Estado:** VERIFIED

- **AC-001 (FR-001, FR-006):** menos de seis meses produce `calculable=false` sin puntos inventados.
- **AC-002 (FR-002, FR-004):** el backtesting registra MAE de ambos candidatos y selecciona el menor.
- **AC-003 (FR-003):** seis meses generan seis períodos consecutivos, estimaciones no negativas y límites ordenados.
- **AC-004 (SEC-001, SEC-003):** JWT ausente, análisis ajeno y horizonte inválido producen 401, 404 y 422.
- **AC-005 (FR-005, NFR-002, SEC-002):** el gráfico diferencia historia/pronóstico/rango, solo usa campos permitidos y no genera `params`.
- **AC-006 (NFR-001):** la suite completa y el entorno del laboratorio funcionan sin dependencias nuevas.

## Evidencia

- `tests/test_sales_forecast.py`: historia insuficiente, backtesting, seis períodos, límites, JWT, ownership, 422 y gráfico.
- `tests/test_frontend_dashboard.py`: pronóstico y modelo visibles sin excepción.
- API real con PDF saludable: 12 históricos, enero-junio 2026, regresión temporal, MAE S/ 2,299.59 y total S/ 1,023,174.83.
- Suite completa: 117 pruebas aprobadas; sin dependencias nuevas.
