# Aceptación — SPEC-012

- **Estado:** VERIFIED

## AC-001 — Conversión de tasas

**Cubre:** FR-001, FR-002, FR-003, NFR-001

**Dado** una TEA, TNA o tasa efectiva bimestral, **cuando** se simula, **entonces** la TEM y TEA equivalentes coinciden con la convención declarada.

## AC-002 — Momento de aporte y costos

**Cubre:** FR-004, FR-005

**Dado** aportes y costos, **cuando** cambia el aporte de fin a inicio, **entonces** el aporte inicial genera un mes adicional de rendimiento y todos los costos quedan trazables.

## AC-003 — Resultado real

**Cubre:** FR-006

**Dado** inflación positiva, **cuando** termina el plazo, **entonces** el saldo real es menor al nominal y se reportan ganancia y ROI reales.

## AC-004 — Compatibilidad

**Cubre:** FR-007

**Dado** el payload anterior con `tasa_anual_percent`, **cuando** se procesa, **entonces** conserva el resultado TNA y los campos de respuesta existentes.

## AC-005 — Validación y aislamiento

**Cubre:** NFR-004, SEC-001, SEC-002

**Dado** un JWT ausente, análisis ajeno o base de tasa inválida, **cuando** se invoca el endpoint, **entonces** responde 401, 404 o 422 sin filtrar datos.

## AC-006 — Interfaz compatible

**Cubre:** FR-008, NFR-002, NFR-003, SEC-003

**Dado** un resultado avanzado, **cuando** se renderiza Streamlit/Altair, **entonces** se muestran equivalencias y saldo real sin parámetros Vega-Lite ni dependencias nuevas.

## Registro

| Criterio | Evidencia | Resultado |
|---|---|---|
| AC-001 | TEA 12 %, TNA 12 % y efectiva bimestral 2 % verificadas | PASS |
| AC-002 | Aporte inicial S/ 1,111 vs. final S/ 1,110; costos trazables | PASS |
| AC-003 | Saldo nominal/real e inflación verificados | PASS |
| AC-004 | Payload heredado conserva saldo S/ 11,268.25 | PASS |
| AC-005 | JWT, ownership y 422 en `test_investment_simulation.py` | PASS |
| AC-006 | UI real estrecha, gráfico de 3 capas y suite de 117 pruebas | PASS |
