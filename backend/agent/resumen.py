"""Resumen ejecutivo con Gemini y fallback sin detalles internos."""

from backend.agent.gemini_client import generate_text


_SYSTEM = (
    "Eres un analista financiero senior. Usa exclusivamente los indicadores y alertas "
    "proporcionados, no inventes cifras y no presentes el resultado como aprobacion crediticia."
)
_PROMPT = """
Redacta en espanol un resumen ejecutivo de maximo 180 palabras con:
1. Situacion general
2. Puntos fuertes
3. Riesgos o alertas
4. Recomendacion de revision humana

Indicadores: {indicadores}
Alertas: {alertas}
""".strip()


def generar_resumen(indicadores: dict, alertas: list) -> str:
    try:
        return generate_text(
            _PROMPT.format(indicadores=indicadores, alertas=alertas),
            system_instruction=_SYSTEM,
        )
    except Exception:
        n_alertas = len(alertas)
        estado = "con senales de alerta" if n_alertas else "sin alertas automaticas"
        return (
            f"Analisis offline completado {estado}. Se calcularon {len(indicadores)} "
            f"indicadores y se detectaron {n_alertas} alertas. Revise las cifras y fuentes "
            "antes de tomar una decision financiera."
        )
