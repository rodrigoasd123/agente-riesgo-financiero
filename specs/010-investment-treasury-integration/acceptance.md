# Criterios de aceptación - SPEC-010

- **Estado:** VERIFIED (109 pruebas automatizadas; health, login de analista y recorrido API real verificados el 2026-09-04)

## AC-001 - Excedente con evidencia documental

**Dado** un análisis con efectivo, efectivo restringido y reserva mínima,
**cuando** se consulta tesorería,
**entonces** se descuentan los dos conceptos y se identifica el método documental.

Evidencia: `test_treasury_surplus_uses_document_values` y análisis real del PDF saludable (`S/ 210,000`).

## AC-002 - Datos insuficientes

**Dado** un análisis sin efectivo,
**cuando** se consulta tesorería,
**entonces** la respuesta indica `calculable=false` y no recomienda capital.

Evidencia: `test_treasury_surplus_missing_cash_is_not_zero`.

## AC-003 - Simulación determinística

**Dado** un conjunto válido de supuestos,
**cuando** se simula la inversión,
**entonces** los importes coinciden con valores Decimal esperados e incluyen advertencia.

Evidencia: `test_investment_simulation_exact_decimal_result` y ejecución API (`S/ 11,268.25`, 13 puntos).

## AC-004 - Validación y autorización

**Dado** un endpoint protegido,
**cuando** falta el JWT, el análisis pertenece a otro usuario o el payload excede límites,
**entonces** se obtienen respectivamente 401, 404 o 422.

Evidencia: pruebas API en `tests/test_investment_simulation.py`.

## AC-005 - Compatibilidad visual

**Dado** un resultado de simulación,
**cuando** se construye el gráfico,
**entonces** Vega-Lite no contiene `params` y los datos se mantienen allowlisted.

Evidencia: `test_investment_chart_has_no_vegalite_params`.

## AC-006 - Aplicación ejecutable en laboratorio

**Dado** el entorno del laboratorio con dependencias actuales,
**cuando** se inicia backend y frontend,
**entonces** ambos responden sin requerir paquetes adicionales y OCR sigue siendo opcional.

Evidencia: health `ready=true`, Streamlit HTTP 200, login real de `analista` y suite completa de 109 pruebas.
