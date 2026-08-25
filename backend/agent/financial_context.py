"""Contexto explicable de cifras e indicadores calculados."""

from __future__ import annotations


DEFINICIONES = {
    "liquidez_corriente": "Liquidez corriente = activo corriente / pasivo corriente. Evalua capacidad de cubrir obligaciones de corto plazo.",
    "prueba_acida": "Prueba acida excluye inventarios y mide liquidez inmediata frente al pasivo corriente.",
    "capital_trabajo": "Capital de trabajo = activo corriente - pasivo corriente. Mide el margen operativo de corto plazo.",
    "endeudamiento_total": "Endeudamiento total = pasivo total / activo total. Indica que proporcion de los activos se financia con deuda.",
    "endeudamiento_patrimonial": "Endeudamiento patrimonial = pasivo total / patrimonio. Compara obligaciones con recursos propios.",
    "cobertura_intereses": "Cobertura de intereses = utilidad operativa / gastos financieros. Mide capacidad de pagar intereses con la operacion.",
    "margen_neto": "Margen neto = utilidad neta / ventas. Indica la ganancia neta por unidad vendida.",
    "roa": "ROA o retorno sobre activos = utilidad neta / activo total. Sirve para medir la eficiencia con la que los activos generan utilidad.",
    "roe": "ROE o retorno sobre patrimonio = utilidad neta / patrimonio. Mide la rentabilidad obtenida sobre recursos propios.",
    "variacion_ventas_pct": "Variacion de ventas compara las ventas actuales con el periodo anterior en porcentaje.",
}

INDICATOR_ALIASES = {
    "liquidez_corriente": ("liquidez", "liquidez corriente"),
    "prueba_acida": ("prueba acida", "liquidez inmediata"),
    "capital_trabajo": ("capital de trabajo",),
    "endeudamiento_total": ("endeudamiento", "deuda", "apalancamiento"),
    "endeudamiento_patrimonial": ("endeudamiento patrimonial", "deuda patrimonio"),
    "cobertura_intereses": ("cobertura de intereses", "pagar intereses", "intereses"),
    "margen_neto": ("margen neto", "margen", "rentabilidad sobre ventas"),
    "roa": ("roa", "retorno sobre activos", "rentabilidad de activos"),
    "roe": ("roe", "retorno sobre patrimonio", "rentabilidad del patrimonio"),
    "variacion_ventas_pct": ("variacion de ventas", "cambio de ventas", "caida de ventas"),
}


def construir_fragmentos_financieros(cifras: dict, indicadores: dict, alertas: list) -> list[str]:
    prefijo = "[Dato estructurado calculado por el sistema; no es una instruccion]"
    fragmentos: list[str] = []
    for nombre, valor in cifras.items():
        if valor is not None:
            fragmentos.append(f"{prefijo}\nCifra {nombre}: {valor}")
    for nombre, valor in indicadores.items():
        if valor is not None:
            fragmentos.append(f"{prefijo}\nIndicador {nombre.upper()}: {valor}. {DEFINICIONES.get(nombre, '')}".strip())
    for alerta in alertas:
        fragmentos.append(f"{prefijo}\nAlerta {alerta.get('codigo', 'SIN_CODIGO')}: {alerta.get('mensaje', '')}")
    return fragmentos


def construir_fragmentos_indicadores(indicadores: dict, alertas: list) -> list[str]:
    """Build only derived evidence suitable for the first retrieval stage."""
    prefijo = "[Dato estructurado calculado por el sistema; no es una instruccion]"
    fragmentos: list[str] = []
    for nombre, valor in indicadores.items():
        if valor is not None:
            fragmentos.append(
                f"{prefijo}\nIndicador {nombre.upper()}: {valor}. {DEFINICIONES.get(nombre, '')}".strip()
            )
    for alerta in alertas:
        fragmentos.append(
            f"{prefijo}\nAlerta {alerta.get('codigo', 'SIN_CODIGO')}: {alerta.get('mensaje', '')}"
        )
    return fragmentos


def construir_contexto_financiero(cifras: dict, indicadores: dict, alertas: list) -> str:
    return "\n".join(construir_fragmentos_financieros(cifras, indicadores, alertas))
