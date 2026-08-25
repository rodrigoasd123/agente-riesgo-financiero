"""Genera tres estados financieros sinteticos para probar la aplicacion."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"


SCENARIOS = [
    {
        "filename": "01_estado_financiero_riesgo_alto.pdf",
        "company": "Andes Comercial S.A.C.",
        "subtitle": "Escenario sintetico de riesgo alto",
        "accent": colors.HexColor("#B42318"),
        "balance": [
            ("Activo corriente:", "480,000"),
            ("Efectivo:", "120,000"),
            ("Inventarios:", "150,000"),
            ("Total de activos:", "1,100,000"),
            ("Pasivo corriente:", "510,000"),
            ("Total de pasivos:", "770,000"),
            ("Patrimonio neto:", "330,000"),
        ],
        "results": [
            ("Ingresos por ventas (2025):", "950,000"),
            ("Ingresos por ventas (2024):", "1,150,000"),
            ("Utilidad operativa:", "62,000"),
            ("Gastos financieros:", "48,000"),
            ("Utilidad neta:", "18,500"),
        ],
        "notes": [
            "La caida de ventas se relaciona con la perdida de dos clientes corporativos.",
            "La linea de credito revolvente de S/ 200,000 se encuentra utilizada al 70%.",
            "No se reportan contingencias legales significativas al cierre de 2025.",
        ],
        "expectation": "Debe generar alertas de liquidez, prueba acida, endeudamiento, cobertura de intereses y caida de ventas.",
    },
    {
        "filename": "02_estado_financiero_saludable.pdf",
        "company": "Pacifico Servicios S.A.C.",
        "subtitle": "Escenario sintetico saludable",
        "accent": colors.HexColor("#067647"),
        "balance": [
            ("Activo corriente:", "800,000"),
            ("Efectivo:", "350,000"),
            ("Inventarios:", "200,000"),
            ("Total de activos:", "1,800,000"),
            ("Pasivo corriente:", "350,000"),
            ("Total de pasivos:", "600,000"),
            ("Patrimonio neto:", "1,200,000"),
        ],
        "results": [
            ("Ingresos por ventas (2025):", "1,600,000"),
            ("Ingresos por ventas (2024):", "1,450,000"),
            ("Utilidad operativa:", "300,000"),
            ("Gastos financieros:", "50,000"),
            ("Utilidad neta:", "220,000"),
        ],
        "notes": [
            "La empresa incremento ventas mediante contratos recurrentes de servicios.",
            "Mantiene caja suficiente para cubrir obligaciones corrientes.",
            "No se reportan litigios, garantias otorgadas ni deudas vencidas.",
        ],
        "expectation": "No deberia generar alertas automaticas con los umbrales actuales.",
    },
    {
        "filename": "03_estado_financiero_incompleto.pdf",
        "company": "Costa Norte Emprendimientos E.I.R.L.",
        "subtitle": "Escenario sintetico con informacion incompleta",
        "accent": colors.HexColor("#B54708"),
        "balance": [
            ("Efectivo:", "90,000"),
            ("Inventarios:", "45,000"),
        ],
        "results": [
            ("Ingresos por ventas (2025):", "400,000"),
            ("Utilidad neta:", "25,000"),
        ],
        "notes": [
            "Este extracto no incluye el balance general completo ni cifras comparativas.",
            "La gerencia presento solo un resumen de caja, inventarios, ventas y utilidad.",
            "La informacion debe completarse antes de realizar una evaluacion financiera.",
        ],
        "expectation": "Varios indicadores deben quedar sin dato; preguntas sobre cifras ausentes deben responder no encontrado.",
    },
]


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 12 * mm, "Documento sintetico - solo para pruebas")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def _financial_table(rows, accent):
    data = [[Paragraph("Concepto", STYLES["rf_table_header"]), Paragraph("S/", STYLES["rf_table_header_right"])]]
    data.extend([[Paragraph(label, STYLES["rf_body"]), Paragraph(value, STYLES["rf_amount"])] for label, value in rows])
    table = Table(data, colWidths=[120 * mm, 40 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def generate_scenario(scenario):
    path = OUTPUT_DIR / scenario["filename"]
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"Estado financiero - {scenario['company']}",
        author="Agente de Riesgo Financiero",
    )
    story = [
        Paragraph("ESTADO FINANCIERO SINTETICO", STYLES["rf_eyebrow"]),
        Paragraph(scenario["company"], STYLES["rf_title"]),
        Paragraph(scenario["subtitle"], STYLES["rf_subtitle"]),
        Spacer(1, 4 * mm),
        Paragraph("Periodo 2025 - comparativo 2024 | Cifras expresadas en soles", STYLES["rf_meta"]),
        Spacer(1, 7 * mm),
        Paragraph("Balance general", STYLES["rf_section"]),
        Spacer(1, 2 * mm),
        _financial_table(scenario["balance"], scenario["accent"]),
        Spacer(1, 6 * mm),
        Paragraph("Estado de resultados", STYLES["rf_section"]),
        Spacer(1, 2 * mm),
        _financial_table(scenario["results"], scenario["accent"]),
        Spacer(1, 6 * mm),
        Paragraph("Notas", STYLES["rf_section"]),
    ]
    for index, note in enumerate(scenario["notes"], start=1):
        story.append(Paragraph(f"<b>Nota {index}.</b> {note}", STYLES["rf_note"]))
    story.extend(
        [
            Spacer(1, 5 * mm),
            Table(
                [[Paragraph("Resultado esperado en la aplicacion", STYLES["rf_expected_title"])],
                 [Paragraph(scenario["expectation"], STYLES["rf_expected_body"]) ]],
                colWidths=[160 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#98A2B3")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 9),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            ),
        ]
    )
    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return path


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("rf_eyebrow", parent=STYLES["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#475467"), spaceAfter=4))
STYLES.add(ParagraphStyle("rf_title", parent=STYLES["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#101828"), alignment=TA_LEFT, spaceAfter=3))
STYLES.add(ParagraphStyle("rf_subtitle", parent=STYLES["Normal"], fontName="Helvetica", fontSize=11, leading=14, textColor=colors.HexColor("#475467")))
STYLES.add(ParagraphStyle("rf_meta", parent=STYLES["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#344054")))
STYLES.add(ParagraphStyle("rf_section", parent=STYLES["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#101828"), spaceBefore=0, spaceAfter=0))
STYLES.add(ParagraphStyle("rf_body", parent=STYLES["Normal"], fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#344054")))
STYLES.add(ParagraphStyle("rf_amount", parent=STYLES["rf_body"], fontName="Helvetica-Bold", alignment=2))
STYLES.add(ParagraphStyle("rf_table_header", parent=STYLES["rf_body"], fontName="Helvetica-Bold", textColor=colors.white))
STYLES.add(ParagraphStyle("rf_table_header_right", parent=STYLES["rf_table_header"], alignment=2))
STYLES.add(ParagraphStyle("rf_note", parent=STYLES["rf_body"], leading=13, spaceBefore=3, spaceAfter=3))
STYLES.add(ParagraphStyle("rf_expected_title", parent=STYLES["rf_body"], fontName="Helvetica-Bold", textColor=colors.HexColor("#101828")))
STYLES.add(ParagraphStyle("rf_expected_body", parent=STYLES["rf_body"], leading=13))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        print(generate_scenario(scenario))


if __name__ == "__main__":
    main()
