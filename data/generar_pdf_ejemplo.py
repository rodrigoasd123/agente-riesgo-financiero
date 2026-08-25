"""
Genera un PDF sintetico de estado financiero (balance general + estado
de resultados) para pruebas del equipo. NO contiene datos reales de
ningun cliente, segun lo exigido por el enunciado del proyecto.

Ejecutar: python data/generar_pdf_ejemplo.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUTPUT_PATH = Path(__file__).parent / "estado_financiero_ejemplo.pdf"

LINEAS = [
    "EMPRESA FICTICIA S.A.C. (RUC 20999999999)",
    "Estados Financieros - Periodo 2025 (comparativo 2024)",
    "Cifras expresadas en Soles (S/)",
    "",
    "BALANCE GENERAL",
    "-----------------------------------------------------",
    "Activo corriente: 480,000",
    "  Efectivo y equivalentes: 120,000",
    "  Inventarios: 150,000",
    "Activo no corriente: 620,000",
    "Total de activos: 1,100,000",
    "",
    "Pasivo corriente: 510,000",
    "Pasivo no corriente: 260,000",
    "Total de pasivos: 770,000",
    "",
    "Patrimonio neto: 330,000",
    "",
    "ESTADO DE RESULTADOS",
    "-----------------------------------------------------",
    "Ingresos por ventas (2025): 950,000",
    "Ingresos por ventas (2024): 1,150,000",
    "Utilidad operativa: 62,000",
    "Gastos financieros: 48,000",
    "Utilidad neta del ejercicio: 18,500",
    "",
    "NOTAS A LOS ESTADOS FINANCIEROS",
    "-----------------------------------------------------",
    "Nota 1: La caida de ingresos respecto al periodo anterior se debe",
    "principalmente a la perdida de dos clientes corporativos clave.",
    "Nota 2: La empresa mantiene una linea de credito revolvente con un",
    "banco local por S/ 200,000, utilizada en un 70% al cierre del periodo.",
    "Nota 3: No existen contingencias legales significativas al cierre",
    "del ejercicio 2025.",
]


def generar_pdf():
    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=letter)
    width, height = letter
    y = height - 60
    c.setFont("Helvetica", 11)
    for linea in LINEAS:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60
        c.drawString(50, y, linea)
        y -= 18
    c.save()
    print(f"PDF de ejemplo generado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    generar_pdf()
