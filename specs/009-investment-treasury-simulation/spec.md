# Investment simulation and treasury surplus analysis

- **ID:** SPEC-009
- **Status:** IMPLEMENTED
- **Created:** 2026-08-28
- **Owner:** Product and engineering

## Problem

After analyzing a financial statement, analysts and business managers know their historical liquidity and risk ratios, but lack deterministic tools to assess how much idle cash can be safely deployed into external investment instruments (such as money market funds, fixed income, or equity index portfolios) and what the net expected wealth evolution would be after compounding, broker commissions, and capital gains taxes.

## Users and outcomes

- **Primary user:** authenticated financial analyst or corporate treasurer.
- **Secondary user:** administrator evaluating financial scenarios.
- **Desired outcome:** automatic detection of idle cash surplus from the analyzed PDF, coupled with a transparent, configurable investment simulator accounting for real-world market friction (compounding frequencies, entry/exit commissions, and tax withholding).
- **Success signal:** the user receives a grounded surplus recommendation based on document figures and can interactively simulate and visualize investment paths without manual calculation errors.

## Scope

### Included

- Deterministic calculation of operational cash reserve and invertible treasury surplus from analyzed financial statement figures.
- Multi-frequency compound interest simulation (daily, monthly, quarterly, semiannual, annual) with optional recurring monthly contributions.
- Strict accounting for entry commission, exit commission, and capital gains tax deductions using `Decimal` arithmetic.
- Authenticated REST API endpoints under `/analyses/{analysis_id}/` for surplus diagnosis and simulation runs.
- Interactive Altair charts in the Streamlit frontend illustrating capital contributions vs. accumulated net returns over time.
- Preset investment profiles (Conservative, Moderate, Growth/Equity).

### Excluded

- Real-time stock ticker or live brokerage API integrations.
- Automated order execution or algorithmic trading.
- Legal, fiscal or binding investment advice.

## Requirements

### Functional

- **FR-001:** The system must compute the operational safety reserve and invertible surplus from extracted cash and short-term debt.
- **FR-002:** The investment simulator must support initial capital, time horizon (months), annual return rate, compounding frequency, entry/exit commission percentages, tax rate percentage, and optional monthly additions.
- **FR-003:** Calculations must be deterministic, period-by-period, using high-precision decimal arithmetic.
- **FR-004:** The API must expose owner-scoped endpoints `GET /analyses/{analysis_id}/treasury-surplus` and `POST /analyses/{analysis_id}/investment-simulation`.
- **FR-005:** The frontend must render interactive evolution charts (principal vs. net gains) and summary metric cards.
- **FR-006:** Invalid inputs (negative periods, extreme rates > 1000%, invalid compounding keys) must be rejected with 422 Unprocessable Entity.

### Non-functional

- **NFR-001:** Zero LLM calls are needed for pure financial surplus and simulation calculations, preserving provider quota.
- **NFR-002:** Chart rendering must remain responsive and compatible with Altair 5 and Streamlit.
- **NFR-003:** All numeric currency outputs must be formatted to two decimal places.

### Security and privacy

- **SEC-001:** Surplus diagnosis and simulation endpoints must require valid JWT authentication and match the owner of the analysis ID.
- **SEC-002:** Input boundaries must prevent arithmetic overflows and denial-of-service attempts.

## Constraints and invariants

- Financial calculations must use `Decimal` with `ROUND_HALF_UP` rounding.
- Output metrics must disclaim that projections are educational and not guaranteed returns.

## References

- `backend/agent/financial_tools.py`
- `backend/api/routes_finance.py`
- `frontend/dashboard.py`
- `frontend/app.py`
