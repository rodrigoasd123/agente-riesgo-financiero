# Plan — SPEC-013

## Arquitectura

- `backend/agent/sales_forecasting.py`: dominio puro Decimal, validación, backtesting y proyección.
- `backend/api/routes_finance.py`: `GET /analyses/{id}/sales-forecast?horizon_months=6` con JWT/ownership.
- `frontend/dashboard.py`: normalización allowlisted y gráfico observado/pronosticado.
- `frontend/app.py`: métricas y estado de insuficiencia dentro del dashboard mensual.
- `tests/test_sales_forecast.py`: fórmulas, selección, límites, autorización y gráfico.

## Flujo

FastAPI obtiene el análisis del propietario, lee únicamente `ventas_mensuales`, entrena ambos candidatos con validación temporal y devuelve una respuesta tipada. Streamlit solicita el horizonte seleccionado y representa el resultado sin persistirlo ni llamar servicios externos.

## Compatibilidad y reversión

- Sin migraciones ni dependencias.
- Documentos sin serie mensual conservan el dashboard actual y muestran “pronóstico no disponible”.
- Reversión: retirar endpoint y bloque visual sin tocar datos persistidos.

## Verificación

- Tendencias creciente/decreciente, historia insuficiente, MAE y límites.
- JWT, propietario y validación 422.
- Gráfico sin `params`, Streamlit, suite completa y prueba real con PDF saludable.
