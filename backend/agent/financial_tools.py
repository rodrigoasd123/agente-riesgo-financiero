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


def calcular_excedente_tesoreria(
    cifras: dict,
    factor_reserva_percent: Decimal = Decimal("20"),
) -> dict:
    """Calcula la caja operativa de seguridad y el excedente disponible para invertir."""
    efectivo = Decimal(str(cifras.get("efectivo") or 0))
    pasivo_corriente = Decimal(str(cifras.get("pasivo_corriente") or 0))
    factor = max(Decimal(0), min(factor_reserva_percent, Decimal(100))) / Decimal(100)
    reserva = _q(max(Decimal(0), pasivo_corriente * factor))
    excedente = _q(max(Decimal(0), efectivo - reserva))
    
    return {
        "efectivo_total": _q(efectivo),
        "pasivo_corriente": _q(pasivo_corriente),
        "factor_reserva_percent": _q(factor_reserva_percent),
        "reserva_operativa": reserva,
        "excedente_invertible": excedente,
        "perfiles": {
            "conservador": _q(excedente * Decimal("0.30")),
            "moderado": _q(excedente * Decimal("0.60")),
            "dinamico": _q(excedente * Decimal("0.90")),
        },
    }


FRECUENCIAS_CAPITALIZACION = {
    "diaria": 365,
    "mensual": 12,
    "trimestral": 4,
    "semestral": 2,
    "anual": 1,
}


def simular_inversion(
    capital_inicial: Decimal,
    plazo_meses: int,
    tasa_anual_percent: Decimal,
    frecuencia_capitalizacion: str = "mensual",
    comision_entrada_percent: Decimal = Decimal(0),
    comision_salida_percent: Decimal = Decimal(0),
    impuesto_ganancia_percent: Decimal = Decimal(0),
    aporte_mensual: Decimal = Decimal(0),
) -> dict:
    """Simula el crecimiento de capital con interés compuesto, comisiones e impuestos."""
    if plazo_meses < 1:
        raise ValueError("El plazo debe ser de al menos 1 mes.")
    if capital_inicial < Decimal(0) or aporte_mensual < Decimal(0):
        raise ValueError("Los importes de capital no pueden ser negativos.")
    
    frecuencia = frecuencia_capitalizacion.lower().strip()
    m = FRECUENCIAS_CAPITALIZACION.get(frecuencia, 12)
    r_anual_float = float(tasa_anual_percent) / 100.0
    r_mensual_float = (1.0 + r_anual_float / m) ** (m / 12.0) - 1.0
    r_mensual = Decimal(str(round(r_mensual_float, 10)))

    comision_entrada = _q(capital_inicial * (max(Decimal(0), comision_entrada_percent) / Decimal(100)))
    saldo = capital_inicial - comision_entrada
    total_aportado = capital_inicial + (aporte_mensual * Decimal(plazo_meses))

    series = []
    series.append({
        "mes": 0,
        "capital_aportado": _q(capital_inicial),
        "intereses_acumulados": Decimal("0.00"),
        "saldo": _q(saldo),
    })

    for mes in range(1, plazo_meses + 1):
        interes_mes = saldo * r_mensual
        saldo += interes_mes + aporte_mensual
        capital_aportado_mes = capital_inicial + (aporte_mensual * Decimal(mes))
        intereses_acum = max(Decimal(0), saldo - capital_aportado_mes + comision_entrada)
        series.append({
            "mes": mes,
            "capital_aportado": _q(capital_aportado_mes),
            "intereses_acumulados": _q(intereses_acum),
            "saldo": _q(saldo),
        })

    saldo_final_bruto = _q(saldo)
    comision_salida = _q(saldo_final_bruto * (max(Decimal(0), comision_salida_percent) / Decimal(100)))
    comisiones_totales = _q(comision_entrada + comision_salida)
    
    ganancia_bruta = max(Decimal(0), saldo_final_bruto - total_aportado)
    impuestos_totales = _q(ganancia_bruta * (max(Decimal(0), impuesto_ganancia_percent) / Decimal(100)))
    ganancia_neta = _q(saldo_final_bruto - total_aportado - comision_salida - impuestos_totales)
    saldo_final_neto = _q(total_aportado + ganancia_neta)
    roi_neto_percent = _q((ganancia_neta / total_aportado) * Decimal(100)) if total_aportado > 0 else Decimal(0)

    return {
        "capital_inicial": _q(capital_inicial),
        "aporte_mensual": _q(aporte_mensual),
        "plazo_meses": plazo_meses,
        "tasa_anual_percent": _q(tasa_anual_percent),
        "frecuencia_capitalizacion": frecuencia,
        "total_aportado": _q(total_aportado),
        "saldo_final_bruto": saldo_final_bruto,
        "comisiones_totales": comisiones_totales,
        "impuestos_totales": impuestos_totales,
        "ganancia_neta": ganancia_neta,
        "saldo_final_neto": saldo_final_neto,
        "roi_neto_percent": roi_neto_percent,
        "series": series,
    }

