# Plan técnico - SPEC-010

- **Estado:** IMPLEMENTING

## Componentes

1. `backend/agent/pdf_reader.py`
   - Ampliar el contrato con moneda, efectivo restringido y reserva mínima operativa opcionales.
   - Añadir patrones de respaldo sin volver obligatorios los nuevos campos.

2. `backend/agent/financial_tools.py`
   - Incorporar `calcular_excedente_tesoreria` y `simular_inversion`.
   - Mantener toda la aritmética en `Decimal` y devolver valores redondeados.

3. `backend/api/routes_finance.py`
   - Definir contratos Pydantic y endpoints autenticados.
   - Reutilizar `_owned` para aislamiento por propietario.

4. `frontend/dashboard.py`
   - Añadir normalización allowlisted y gráfico de evolución.
   - Reutilizar `_style_chart` y evitar `.interactive()`.

5. `frontend/app.py`
   - Integrar el flujo en Proyecciones y reportes.
   - Añadir moneda, escenarios, estados vacío/error/éxito y advertencia educativa.

6. `tests/test_investment_simulation.py`
   - Probar cálculos exactos, datos ausentes, reserva documental, validación, JWT, aislamiento y gráfico sin `params`.

## Flujo de datos

`analysis_id + JWT -> FastAPI -> análisis del propietario -> cifras JSON -> diagnóstico/simulación Decimal -> JSON -> Streamlit/Altair`

## Compatibilidad y despliegue

- Sin migración de base de datos.
- Sin nuevas dependencias.
- Los campos nuevos del PDF son opcionales y compatibles con análisis anteriores.
- La rama original no se fusiona directamente; se adapta sobre la versión actual de los archivos.

## Verificación

1. Pruebas específicas del simulador.
2. Pruebas del dashboard y API existentes.
3. Suite completa.
4. Inicio de FastAPI y Streamlit en los puertos usados por el proyecto.
5. Prueba visual de escritorio y viewport estrecho.
