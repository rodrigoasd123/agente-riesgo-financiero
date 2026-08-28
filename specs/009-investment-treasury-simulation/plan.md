# Technical Plan: Investment simulation and treasury surplus analysis

- **ID:** SPEC-009
- **Status:** IMPLEMENTED
- **Related Spec:** `specs/009-investment-treasury-simulation/spec.md`

## Architecture & Modules

### 1. `backend/agent/financial_tools.py`
- Add `calcular_excedente_tesoreria(cifras: dict, indicadores: dict, factor_reserva: Decimal = Decimal("0.20")) -> dict`:
  - `efectivo`: extracted cash.
  - `pasivo_corriente`: short-term liabilities.
  - `reserva_operativa = max(0, pasivo_corriente * factor_reserva)`.
  - `excedente_disponible = max(0, efectivo - reserva_operativa)`.
  - Output structured breakdown and suggested allocation profiles.
- Add `simular_inversion(...) -> dict`:
  - Calculates month-by-month compound growth, cash additions, commissions on entry/exit, capital gains tax withholding, and net ROI.

### 2. `backend/api/routes_finance.py`
- Add Pydantic request & response models:
  - `InvestmentSimulationRequest`
  - `InvestmentSimulationResponse`
  - `TreasurySurplusResponse`
- Add endpoints:
  - `GET /{analysis_id}/treasury-surplus`
  - `POST /{analysis_id}/investment-simulation`

### 3. `frontend/dashboard.py` & `frontend/app.py`
- Add chart builder `investment_evolution_chart(rows: list[dict]) -> alt.LayerChart`.
- Add treasury diagnosis card & investment simulator UI in Streamlit.

### 4. `tests/test_investment_simulation.py`
- Unit tests for financial formulas.
- Integration tests for endpoints with authentication and authorization.
