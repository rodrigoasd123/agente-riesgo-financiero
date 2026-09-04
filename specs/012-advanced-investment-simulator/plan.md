# Plan de implementación — SPEC-012

## Enfoque

Ampliar la función pura existente y su contrato Pydantic, manteniendo los nombres de respuesta anteriores. La interfaz presenta los supuestos en grupos: tasa, flujos/costos y resultados. El gráfico añade saldo real solo cuando está disponible.

## Componentes

| Componente | Cambio | Responsabilidad |
|---|---|---|
| `financial_tools.py` | Conversión de tasas y simulación nominal/real | Dominio financiero |
| `routes_finance.py` | Contratos compatibles y límites | API FastAPI |
| `frontend/app.py` | Formulario explicativo y resultados | Flujo Streamlit |
| `frontend/dashboard.py` | Serie y curva real allowlisted | Visualización |
| `tests/test_investment_simulation.py` | Fórmulas, compatibilidad, 422 y autorización | Evidencia |

## Flujo de datos

1. Usuario autenticado selecciona tipo de tasa y supuestos.
2. FastAPI valida enums, importes y porcentajes y comprueba propiedad del análisis.
3. El dominio convierte la tasa a TEM/TEA, proyecta mes por mes, aplica costos/impuestos y deflacta por inflación.
4. La API devuelve un contrato explícito; Streamlit muestra equivalencias, métricas y serie.

## Contrato y compatibilidad

- Sin migración ni persistencia nueva.
- `tasa_anual_percent` continúa aceptado como TNA heredada.
- Nuevos campos: `tipo_tasa`, `tasa_percent`, `periodicidad_tasa`, `momento_aporte`, `inflacion_anual_percent`, `costo_mantenimiento_mensual` y métricas equivalentes/reales.

## Seguridad

- Se conservan JWT y `_owned`.
- Toda validación monetaria se ejecuta en backend.
- No hay llamadas externas ni exposición de texto del PDF.

## Despliegue y reversión

- Backend y frontend se despliegan juntos; el backend acepta clientes antiguos.
- Reversión: restaurar los tres módulos sin migraciones ni datos que revertir.

## Verificación

- Unitarias: equivalencia TEA/TNA/tasa bimestral, momento de aporte, inflación y costos.
- Integración: contrato nuevo, contrato heredado, 422, JWT y propietario.
- Frontend: gráfico sin `params`, aplicación Streamlit sin excepciones.
- Manual: backend health, login y simulación real en la API/UI.
