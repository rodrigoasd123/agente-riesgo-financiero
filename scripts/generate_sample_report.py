"""Genera un reporte de muestra sintetico para validacion visual."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agent.financial_tools import calcular_escenario
from backend.reporting import generar_pdf


OUTPUT = ROOT / "output" / "pdf" / "reporte_financiero_muestra.pdf"


def main() -> None:
    analysis = {
        "filename": "estado_financiero_ejemplo.pdf",
        "created_at": "2026-08-24T16:00:00+00:00",
        "cifras_json": json.dumps({"activo_corriente": 480000, "pasivo_corriente": 510000, "activo_total": 1100000, "pasivo_total": 770000, "ventas": 950000, "utilidad_neta": 18500}),
        "indicadores_json": json.dumps({"liquidez_corriente": 0.9412, "capital_trabajo": -30000, "endeudamiento_total": 0.7, "margen_neto": 0.0195, "roa": 0.0168, "roe": 0.0561}),
        "alertas_json": json.dumps([{"codigo": "LIQUIDEZ_BAJA", "severidad": "alta", "mensaje": "La liquidez corriente es menor a 1.0."}, {"codigo": "ENDEUDAMIENTO_ALTO", "severidad": "alta", "mensaje": "El endeudamiento total supera el umbral de 60%."}]),
        "resumen": "La empresa presenta presion de liquidez y una proporcion elevada de activos financiados con deuda. La rentabilidad sobre activos es positiva pero reducida.",
    }
    projection = calcular_escenario(
        Decimal("100000"),
        [Decimal(value) for value in ("30000", "35000", "40000", "45000")],
        Decimal("10"),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(generar_pdf(analysis, projection))
    print(OUTPUT)


if __name__ == "__main__":
    main()
