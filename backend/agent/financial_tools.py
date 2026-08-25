"""Calculos puros de escenarios de flujo de caja."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext


getcontext().prec = 28
CENT = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _npv(rate: Decimal, flows: list[Decimal]) -> Decimal:
    return sum((flow / ((Decimal(1) + rate) ** period) for period, flow in enumerate(flows)), Decimal(0))


def calcular_tir(flows: list[Decimal]) -> Decimal | None:
    if not any(flow < 0 for flow in flows) or not any(flow > 0 for flow in flows):
        return None
    low, high = Decimal("-0.9999"), Decimal("100")
    low_value, high_value = _npv(low, flows), _npv(high, flows)
    if low_value == 0:
        return low
    if high_value == 0:
        return high
    if low_value * high_value > 0:
        return None
    for _ in range(240):
        mid = (low + high) / 2
        value = _npv(mid, flows)
        if abs(value) < Decimal("0.0000001"):
            return mid
        if low_value * value <= 0:
            high = mid
        else:
            low, low_value = mid, value
    return (low + high) / 2


def calcular_escenario(initial_investment: Decimal, cash_flows: list[Decimal], discount_rate_percent: Decimal) -> dict:
    flows = [-initial_investment, *cash_flows]
    rate = discount_rate_percent / Decimal(100)
    cumulative = Decimal(0)
    payback: Decimal | None = None
    rows = []
    previous = Decimal(0)
    for period, flow in enumerate(flows):
        previous = cumulative
        cumulative += flow
        rows.append({"periodo": period, "flujo": _q(flow), "flujo_acumulado": _q(cumulative)})
        if period > 0 and payback is None and cumulative >= 0:
            payback = Decimal(period - 1) + ((-previous / flow) if flow else Decimal(0))
    irr = calcular_tir(flows)
    return {
        "van": _q(_npv(rate, flows)),
        "tir_percent": _q(irr * 100) if irr is not None else None,
        "periodo_recuperacion": _q(payback) if payback is not None else None,
        "flujos": rows,
    }
