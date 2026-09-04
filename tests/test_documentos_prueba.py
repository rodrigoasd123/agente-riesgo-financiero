from __future__ import annotations

import pdfplumber

from data.generar_documentos_prueba import SCENARIOS, generate_scenario


def test_escenarios_cubren_disponibilidad_positiva_cero_e_indeterminada():
    results = {scenario["filename"]: scenario["cash_result"] for scenario in SCENARIOS}

    assert results["01_estado_financiero_riesgo_alto.pdf"] == "S/ 0"
    assert results["02_estado_financiero_saludable.pdf"] == "S/ 210,000"
    assert results["03_estado_financiero_incompleto.pdf"] == "No calculable"


def test_documentos_generados_incluyen_presupuesto_formula_y_resultado(tmp_path):
    for scenario in SCENARIOS:
        path = generate_scenario(scenario, output_dir=tmp_path)
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        assert page_count == 3
        assert "Presupuesto de caja a 90 dias" in text
        assert "Efectivo restringido" in text
        assert "Reserva minima operativa" in text
        assert "excedente potencialmente invertible" in text.lower()
        assert scenario["cash_result"] in text
        assert "Ventas mensuales - enero a diciembre de 2025" in text
        assert all(f"{month} 2025:" in text for month, _ in scenario["monthly_sales"])
        monthly_total = sum(int(value.replace(",", "")) for _, value in scenario["monthly_sales"])
        annual_sales = next(
            int(value.replace(",", ""))
            for label, value in scenario["results"]
            if label.startswith("Ingresos por ventas (2025)")
        )
        assert monthly_total == annual_sales


def test_documento_incompleto_no_inventa_disponibilidad(tmp_path):
    scenario = next(item for item in SCENARIOS if item["cash_result"] == "No calculable")
    path = generate_scenario(scenario, output_dir=tmp_path)
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    assert "No informado" in text
    assert "No calculable" in text
    assert "no debe inferir ni inventar" in text
