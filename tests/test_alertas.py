"""
Pruebas unitarias de deteccion de alertas financieras.
"""
from backend.agent.alertas import detectar_alertas


def test_alerta_liquidez_baja():
    indicadores = {"liquidez_corriente": 0.8}
    alertas = detectar_alertas(indicadores, {})
    codigos = [a["codigo"] for a in alertas]
    assert "LIQUIDEZ_BAJA" in codigos


def test_alerta_endeudamiento_alto():
    indicadores = {"endeudamiento_total": 0.75}
    alertas = detectar_alertas(indicadores, {})
    codigos = [a["codigo"] for a in alertas]
    assert "ENDEUDAMIENTO_ALTO" in codigos


def test_alerta_perdidas_netas():
    indicadores = {"margen_neto": -0.05}
    alertas = detectar_alertas(indicadores, {})
    codigos = [a["codigo"] for a in alertas]
    assert "PERDIDAS_NETAS" in codigos


def test_sin_alertas_cuando_todo_esta_sano():
    indicadores = {
        "liquidez_corriente": 2.0,
        "prueba_acida": 1.5,
        "endeudamiento_total": 0.3,
        "cobertura_intereses": 4.0,
        "margen_neto": 0.15,
        "variacion_ventas_pct": 5.0,
    }
    alertas = detectar_alertas(indicadores, {})
    assert alertas == []


def test_caida_de_ventas_genera_alerta():
    indicadores = {"variacion_ventas_pct": -25.0}
    alertas = detectar_alertas(indicadores, {})
    codigos = [a["codigo"] for a in alertas]
    assert "CAIDA_INGRESOS" in codigos
