"""Calculos puros de escenarios de flujo de caja."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext, localcontext


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


FRECUENCIAS_CAPITALIZACION = {
    "diaria": 365,
    "mensual": 12,
    "bimestral": 6,
    "trimestral": 4,
    "cuatrimestral": 3,
    "semestral": 2,
    "anual": 1,
}

MESES_POR_PERIODO = {
    "mensual": 1,
    "bimestral": 2,
    "trimestral": 3,
    "cuatrimestral": 4,
    "semestral": 6,
    "anual": 12,
}

RATE_QUANTUM = Decimal("0.000001")

ADVERTENCIA_INVERSION = (
    "Simulación educativa basada en supuestos del usuario; no representa una "
    "rentabilidad garantizada ni asesoría de inversión."
)


def _decimal_opcional(value) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def _q_rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)


def _convertir_tasa(
    tasa_percent: Decimal,
    tipo_tasa: str,
    frecuencia_capitalizacion: str,
    periodicidad_tasa: str,
    base_dias: int,
) -> tuple[Decimal, Decimal, str]:
    """Convierte una convención declarada a TEM y TEA equivalentes."""
    tipo = tipo_tasa.lower().strip()
    frecuencia = frecuencia_capitalizacion.lower().strip()
    periodicidad = periodicidad_tasa.lower().strip()
    if tipo not in {"tea", "tna", "efectiva_periodo"}:
        raise ValueError("Tipo de tasa no válido.")
    if frecuencia not in FRECUENCIAS_CAPITALIZACION:
        raise ValueError("Frecuencia de capitalización no válida.")
    if periodicidad not in MESES_POR_PERIODO:
        raise ValueError("Periodicidad de tasa no válida.")
    if base_dias not in {360, 365}:
        raise ValueError("La base diaria debe ser 360 o 365 días.")

    tasa = tasa_percent / Decimal(100)
    with localcontext() as context:
        context.prec = 40
        if tipo == "tea":
            if tasa <= Decimal(-1):
                raise ValueError("La TEA debe ser mayor que -100 %.")
            tea = tasa
            tem = (Decimal(1) + tea) ** (Decimal(1) / Decimal(12)) - Decimal(1)
            descripcion = "TEA convertida a tasa efectiva mensual equivalente."
        elif tipo == "tna":
            periodos_ano = Decimal(
                base_dias if frecuencia == "diaria" else FRECUENCIAS_CAPITALIZACION[frecuencia]
            )
            tasa_periodica = tasa / periodos_ano
            if Decimal(1) + tasa_periodica <= 0:
                raise ValueError("La TNA produce una base de capitalización no positiva.")
            tea = (Decimal(1) + tasa_periodica) ** periodos_ano - Decimal(1)
            tem = (Decimal(1) + tea) ** (Decimal(1) / Decimal(12)) - Decimal(1)
            sufijo = f" con base {base_dias}" if frecuencia == "diaria" else ""
            descripcion = f"TNA capitalizable {frecuencia}{sufijo}, convertida a TEM y TEA."
        else:
            if tasa <= Decimal(-1):
                raise ValueError("La tasa efectiva del período debe ser mayor que -100 %.")
            meses = Decimal(MESES_POR_PERIODO[periodicidad])
            tem = (Decimal(1) + tasa) ** (Decimal(1) / meses) - Decimal(1)
            tea = (Decimal(1) + tem) ** Decimal(12) - Decimal(1)
            descripcion = f"Tasa efectiva {periodicidad} convertida a TEM y TEA."
    return tem, tea, descripcion


def calcular_excedente_tesoreria(
    cifras: dict,
    factor_reserva_percent: Decimal = Decimal("20"),
    moneda: str = "PEN",
) -> dict:
    """Estima caja invertible sin convertir cifras ausentes en disponibilidad."""
    efectivo = _decimal_opcional(cifras.get("efectivo"))
    restringido_documento = _decimal_opcional(cifras.get("efectivo_restringido"))
    pasivo_corriente = _decimal_opcional(cifras.get("pasivo_corriente"))
    reserva_documento = _decimal_opcional(cifras.get("reserva_minima_operativa"))
    saldo_minimo = _decimal_opcional(cifras.get("saldo_minimo_proyectado"))
    moneda_documento = str(cifras.get("moneda") or moneda).strip().upper()
    if moneda_documento not in {"PEN", "USD", "EUR"}:
        moneda_documento = moneda

    base = {
        "calculable": False,
        "motivo": None,
        "moneda": moneda_documento,
        "efectivo_total": _q(efectivo) if efectivo is not None else None,
        "efectivo_restringido": (
            _q(restringido_documento) if restringido_documento is not None else None
        ),
        "efectivo_no_restringido": None,
        "saldo_minimo_proyectado": _q(saldo_minimo) if saldo_minimo is not None else None,
        "pasivo_corriente": _q(pasivo_corriente) if pasivo_corriente is not None else None,
        "factor_reserva_percent": _q(factor_reserva_percent),
        "reserva_operativa": None,
        "metodo_reserva": None,
        "excedente_invertible": None,
        "escenarios": {},
        "advertencia": ADVERTENCIA_INVERSION,
    }
    if efectivo is None:
        base["motivo"] = "El documento no contiene efectivo total verificable."
        return base

    restringido = max(Decimal(0), restringido_documento or Decimal(0))
    efectivo_libre = max(Decimal(0), efectivo - restringido)
    base["efectivo_no_restringido"] = _q(efectivo_libre)

    if reserva_documento is not None:
        reserva = max(Decimal(0), reserva_documento)
        metodo = "reserva_documental"
    elif pasivo_corriente is not None:
        factor = factor_reserva_percent / Decimal(100)
        reserva = max(Decimal(0), pasivo_corriente * factor)
        metodo = "porcentaje_pasivo_corriente"
    else:
        base["motivo"] = (
            "Falta la reserva mínima operativa y el pasivo corriente necesario "
            "para estimarla."
        )
        return base

    caja_referencia = min(efectivo_libre, saldo_minimo) if saldo_minimo is not None else efectivo_libre
    excedente = max(Decimal(0), caja_referencia - reserva)
    base.update(
        {
            "calculable": True,
            "motivo": None,
            "reserva_operativa": _q(reserva),
            "metodo_reserva": metodo,
            "excedente_invertible": _q(excedente),
            "escenarios": {
                "prudente_30": _q(excedente * Decimal("0.30")),
                "balanceado_60": _q(excedente * Decimal("0.60")),
                "amplio_90": _q(excedente * Decimal("0.90")),
            },
        }
    )
    return base


def simular_inversion(
    capital_inicial: Decimal,
    plazo_meses: int,
    tasa_anual_percent: Decimal,
    frecuencia_capitalizacion: str = "mensual",
    comision_entrada_percent: Decimal = Decimal(0),
    comision_salida_percent: Decimal = Decimal(0),
    impuesto_ganancia_percent: Decimal = Decimal(0),
    aporte_mensual: Decimal = Decimal(0),
    moneda: str = "PEN",
    tipo_tasa: str = "tna",
    periodicidad_tasa: str = "anual",
    base_dias: int = 365,
    momento_aporte: str = "fin_periodo",
    inflacion_anual_percent: Decimal = Decimal(0),
    costo_mantenimiento_mensual: Decimal = Decimal(0),
) -> dict:
    """Simula flujos nominales y reales con una convención de tasa explícita."""
    frecuencia = frecuencia_capitalizacion.lower().strip()
    tipo = tipo_tasa.lower().strip()
    periodicidad = periodicidad_tasa.lower().strip()
    momento = momento_aporte.lower().strip()
    if plazo_meses < 1 or plazo_meses > 600:
        raise ValueError("El plazo debe estar entre 1 y 600 meses.")
    if capital_inicial <= 0 or aporte_mensual < 0 or costo_mantenimiento_mensual < 0:
        raise ValueError("El capital debe ser positivo y los aportes no pueden ser negativos.")
    if momento not in {"inicio_periodo", "fin_periodo"}:
        raise ValueError("Momento de aporte no válido.")
    if not Decimal("-99.99") <= tasa_anual_percent <= Decimal("1000"):
        raise ValueError("La tasa debe estar entre -99.99 % y 1000 %.")
    if not Decimal("-99.99") <= inflacion_anual_percent <= Decimal("1000"):
        raise ValueError("La inflación anual debe estar entre -99.99 % y 1000 %.")
    for porcentaje in (
        comision_entrada_percent,
        comision_salida_percent,
        impuesto_ganancia_percent,
    ):
        if porcentaje < 0 or porcentaje > Decimal(100):
            raise ValueError("Comisiones e impuestos no pueden ser negativos.")

    tasa_mensual, tasa_efectiva_anual, descripcion_tasa = _convertir_tasa(
        tasa_anual_percent,
        tipo,
        frecuencia,
        periodicidad,
        base_dias,
    )
    inflacion_anual = inflacion_anual_percent / Decimal(100)
    with localcontext() as context:
        context.prec = 40
        inflacion_mensual = (Decimal(1) + inflacion_anual) ** (
            Decimal(1) / Decimal(12)
        ) - Decimal(1)

    comision_entrada = capital_inicial * comision_entrada_percent / Decimal(100)
    saldo = capital_inicial - comision_entrada
    total_aportado = capital_inicial + aporte_mensual * Decimal(plazo_meses)
    total_aportado_real = capital_inicial
    costos_mantenimiento = Decimal(0)
    series = [
        {
            "mes": 0,
            "capital_aportado": _q(capital_inicial),
            "ganancia_acumulada": _q(saldo - capital_inicial),
            "saldo": _q(saldo),
            "saldo_real": _q(saldo),
        }
    ]

    for mes in range(1, plazo_meses + 1):
        factor_inflacion_mes = (Decimal(1) + inflacion_mensual) ** Decimal(mes)
        if momento == "inicio_periodo":
            saldo += aporte_mensual
            factor_aporte = (Decimal(1) + inflacion_mensual) ** Decimal(mes - 1)
            total_aportado_real += aporte_mensual / factor_aporte
        saldo += saldo * tasa_mensual
        if momento == "fin_periodo":
            saldo += aporte_mensual
            total_aportado_real += aporte_mensual / factor_inflacion_mes
        costo_aplicado = min(saldo, costo_mantenimiento_mensual) if saldo > 0 else Decimal(0)
        saldo -= costo_aplicado
        costos_mantenimiento += costo_aplicado
        capital_mes = capital_inicial + aporte_mensual * Decimal(mes)
        series.append(
            {
                "mes": mes,
                "capital_aportado": _q(capital_mes),
                "ganancia_acumulada": _q(saldo - capital_mes),
                "saldo": _q(saldo),
                "saldo_real": _q(saldo / factor_inflacion_mes),
            }
        )

    saldo_final_bruto = saldo
    comision_salida = saldo_final_bruto * comision_salida_percent / Decimal(100)
    ganancia_gravable = max(
        Decimal(0), saldo_final_bruto - comision_salida - total_aportado
    )
    impuesto = ganancia_gravable * impuesto_ganancia_percent / Decimal(100)
    saldo_final_neto = saldo_final_bruto - comision_salida - impuesto
    ganancia_neta = saldo_final_neto - total_aportado
    roi = (
        ganancia_neta / total_aportado * Decimal(100)
        if total_aportado > 0
        else Decimal(0)
    )
    factor_inflacion_final = (Decimal(1) + inflacion_mensual) ** Decimal(plazo_meses)
    saldo_final_real = saldo_final_neto / factor_inflacion_final
    ganancia_real = saldo_final_real - total_aportado_real
    roi_real = (
        ganancia_real / total_aportado_real * Decimal(100)
        if total_aportado_real > 0
        else Decimal(0)
    )

    return {
        "moneda": moneda,
        "capital_inicial": _q(capital_inicial),
        "aporte_mensual": _q(aporte_mensual),
        "plazo_meses": plazo_meses,
        "tasa_anual_percent": _q(tasa_anual_percent),
        "tipo_tasa": tipo,
        "tasa_ingresada_percent": _q_rate(tasa_anual_percent),
        "periodicidad_tasa": periodicidad,
        "frecuencia_capitalizacion": frecuencia,
        "base_dias": base_dias,
        "tasa_efectiva_mensual_percent": _q_rate(tasa_mensual * Decimal(100)),
        "tasa_efectiva_anual_percent": _q_rate(tasa_efectiva_anual * Decimal(100)),
        "descripcion_tasa": descripcion_tasa,
        "momento_aporte": momento,
        "inflacion_anual_percent": _q_rate(inflacion_anual_percent),
        "costo_mantenimiento_mensual": _q(costo_mantenimiento_mensual),
        "total_aportado": _q(total_aportado),
        "total_aportado_valor_real": _q(total_aportado_real),
        "saldo_final_bruto": _q(saldo_final_bruto),
        "comision_entrada": _q(comision_entrada),
        "comision_salida": _q(comision_salida),
        "costos_mantenimiento": _q(costos_mantenimiento),
        "impuestos_totales": _q(impuesto),
        "costos_totales": _q(
            comision_entrada + comision_salida + costos_mantenimiento + impuesto
        ),
        "ganancia_neta": _q(ganancia_neta),
        "saldo_final_neto": _q(saldo_final_neto),
        "roi_neto_percent": _q(roi),
        "saldo_final_real": _q(saldo_final_real),
        "ganancia_real": _q(ganancia_real),
        "roi_real_percent": _q(roi_real),
        "series": series,
        "advertencia": ADVERTENCIA_INVERSION,
    }
