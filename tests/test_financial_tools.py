from decimal import Decimal

from backend.agent.financial_tools import calcular_escenario, calcular_tir


def test_escenario_calcula_van_tir_y_recuperacion():
    result = calcular_escenario(Decimal("100"), [Decimal("60"), Decimal("60")], Decimal("10"))
    assert result["van"] == Decimal("4.13")
    assert result["tir_percent"] == Decimal("13.07")
    assert result["periodo_recuperacion"] == Decimal("1.67")
    assert result["flujos"][-1]["flujo_acumulado"] == Decimal("20.00")


def test_tir_no_existe_sin_cambio_de_signo():
    assert calcular_tir([Decimal("-100"), Decimal("-5")]) is None

