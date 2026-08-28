# Acceptance Evidence: Investment simulation and treasury surplus analysis

- **ID:** SPEC-009
- **Status:** VERIFIED
- **Verification Date:** 2026-08-28

## Acceptance Verification

### 1. Functional Verification
- `calcular_excedente_tesoreria` accurately extracts cash and subtracts operating reserve.
- `simular_inversion` accurately computes monthly compound interest, entry/exit commissions, and tax withholding with `Decimal` precision.
- REST endpoints `/analyses/{analysis_id}/treasury-surplus` and `/analyses/{analysis_id}/investment-simulation` enforce owner isolation and return expected JSON payloads.
- Streamlit UI provides one-click surplus transfer to simulator, preset strategy buttons, and Altair chart visualization.

### 2. Automated Test Suite
- Test file `tests/test_investment_simulation.py` covering:
  - Cash surplus calculation with normal and zero-cash inputs.
  - Multi-frequency compounding (monthly, quarterly, annual, daily).
  - Commission deduction and capital gains tax deductions.
  - API validation boundaries and authentication checks.
