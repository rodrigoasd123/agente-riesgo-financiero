"""
Deteccion de senales de alerta a partir de los indicadores calculados.
Cada alerta incluye: codigo, severidad, mensaje explicativo y el valor
que la origino, para que la UI y el resumen ejecutivo puedan usarla.
"""
from backend.config import (
    UMBRAL_LIQUIDEZ_CORRIENTE,
    UMBRAL_PRUEBA_ACIDA,
    UMBRAL_ENDEUDAMIENTO_TOTAL,
    UMBRAL_COBERTURA_INTERESES,
    UMBRAL_CAIDA_VENTAS_PORCENTUAL,
)


def _alerta(codigo: str, severidad: str, mensaje: str, valor) -> dict:
    return {"codigo": codigo, "severidad": severidad, "mensaje": mensaje, "valor": valor}


def detectar_alertas(indicadores: dict, cifras: dict) -> list:
    alertas = []

    liquidez = indicadores.get("liquidez_corriente")
    if liquidez is not None and liquidez < UMBRAL_LIQUIDEZ_CORRIENTE:
        alertas.append(_alerta(
            "LIQUIDEZ_BAJA", "alta",
            f"La liquidez corriente ({liquidez}) esta por debajo de {UMBRAL_LIQUIDEZ_CORRIENTE}. "
            "La empresa podria tener dificultades para cubrir sus obligaciones de corto plazo.",
            liquidez,
        ))

    prueba_acida = indicadores.get("prueba_acida")
    if prueba_acida is not None and prueba_acida < UMBRAL_PRUEBA_ACIDA:
        alertas.append(_alerta(
            "PRUEBA_ACIDA_BAJA", "media",
            f"La prueba acida ({prueba_acida}) es menor a {UMBRAL_PRUEBA_ACIDA}, "
            "lo que sugiere alta dependencia del inventario para cubrir pasivos corrientes.",
            prueba_acida,
        ))

    endeudamiento = indicadores.get("endeudamiento_total")
    if endeudamiento is not None and endeudamiento > UMBRAL_ENDEUDAMIENTO_TOTAL:
        alertas.append(_alerta(
            "ENDEUDAMIENTO_ALTO", "alta",
            f"El endeudamiento total ({endeudamiento}) supera el umbral de {UMBRAL_ENDEUDAMIENTO_TOTAL}. "
            "Una parte importante de los activos esta financiada con deuda.",
            endeudamiento,
        ))

    cobertura = indicadores.get("cobertura_intereses")
    if cobertura is not None and cobertura < UMBRAL_COBERTURA_INTERESES:
        alertas.append(_alerta(
            "COBERTURA_INTERESES_BAJA", "alta",
            f"La cobertura de intereses ({cobertura}) es menor a {UMBRAL_COBERTURA_INTERESES}. "
            "La utilidad operativa podria no ser suficiente para cubrir los gastos financieros.",
            cobertura,
        ))

    margen_neto = indicadores.get("margen_neto")
    if margen_neto is not None and margen_neto < 0:
        alertas.append(_alerta(
            "PERDIDAS_NETAS", "alta",
            f"La empresa registra un margen neto negativo ({margen_neto}), es decir, perdidas netas en el periodo.",
            margen_neto,
        ))

    variacion_ventas = indicadores.get("variacion_ventas_pct")
    if variacion_ventas is not None and variacion_ventas < UMBRAL_CAIDA_VENTAS_PORCENTUAL:
        alertas.append(_alerta(
            "CAIDA_INGRESOS", "media",
            f"Las ventas cayeron {variacion_ventas}% respecto al periodo anterior, "
            f"superando el umbral de alerta de {UMBRAL_CAIDA_VENTAS_PORCENTUAL}%.",
            variacion_ventas,
        ))

    return alertas
