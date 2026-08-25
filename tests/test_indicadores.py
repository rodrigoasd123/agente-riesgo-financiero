"""
Pruebas unitarias de calculo de indicadores financieros.
No dependen de LangGraph, Gemini ni de red: son logica pura.
"""
from backend.agent.indicadores import calcular_indicadores


def test_liquidez_corriente():
    cifras = {"activo_corriente": 480000, "pasivo_corriente": 510000}
    resultado = calcular_indicadores(cifras)
    assert resultado["liquidez_corriente"] == round(480000 / 510000, 4)


def test_endeudamiento_total():
    cifras = {"pasivo_total": 770000, "activo_total": 1100000}
    resultado = calcular_indicadores(cifras)
    assert resultado["endeudamiento_total"] == round(770000 / 1100000, 4)


def test_variacion_ventas():
    cifras = {"ventas": 950000, "ventas_periodo_anterior": 1150000}
    resultado = calcular_indicadores(cifras)
    esperado = round(((950000 - 1150000) / 1150000) * 100, 2)
    assert resultado["variacion_ventas_pct"] == esperado


def test_datos_faltantes_no_rompe():
    resultado = calcular_indicadores({})
    assert resultado["liquidez_corriente"] is None
    assert resultado["roe"] is None


def test_division_por_cero_segura():
    cifras = {"activo_corriente": 100, "pasivo_corriente": 0}
    resultado = calcular_indicadores(cifras)
    assert resultado["liquidez_corriente"] is None


def test_capital_trabajo():
    resultado = calcular_indicadores({"activo_corriente": 480, "pasivo_corriente": 510})
    assert resultado["capital_trabajo"] == -30
