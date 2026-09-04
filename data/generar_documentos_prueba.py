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
        "monthly_sales": [
            ("Enero", "95,000"), ("Febrero", "90,000"), ("Marzo", "85,000"),
            ("Abril", "82,000"), ("Mayo", "80,000"), ("Junio", "78,000"),
            ("Julio", "75,000"), ("Agosto", "76,000"), ("Septiembre", "74,000"),
            ("Octubre", "72,000"), ("Noviembre", "70,000"), ("Diciembre", "73,000"),
        ],
        "sales_story": "La serie evidencia una reduccion progresiva durante el ano, con una recuperacion menor en agosto y diciembre.",
        "notes": [
            "La caida de ventas se relaciona con la perdida de dos clientes corporativos.",
            "La linea de credito revolvente de S/ 200,000 se encuentra utilizada al 70%.",
            "No se reportan contingencias legales significativas al cierre de 2025.",
        ],
        "expectation": "Debe generar alertas de liquidez, prueba acida, endeudamiento, cobertura de intereses y caida de ventas.",
        "cash_parameters": [
            ("Efectivo inicial:", "120,000"),
            ("Efectivo restringido:", "30,000"),
            ("Efectivo no restringido inicial:", "90,000"),
            ("Reserva minima operativa:", "80,000"),
            ("Compromiso extraordinario (mes 2):", "20,000"),
        ],
        "cash_budget": [
            ("Mes 1", "70,000", "130,000", "0", "30,000"),
            ("Mes 2", "50,000", "110,000", "20,000", "-50,000"),
            ("Mes 3", "40,000", "90,000", "0", "-100,000"),
        ],
        "cash_result": "S/ 0",
        "cash_explanation": "El menor saldo proyectado es S/ -100,000. Frente a una reserva minima de S/ 80,000 existe una brecha de S/ 180,000; no hay excedente para invertir.",
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
        "monthly_sales": [
            ("Enero", "110,000"), ("Febrero", "115,000"), ("Marzo", "120,000"),
            ("Abril", "125,000"), ("Mayo", "128,000"), ("Junio", "130,000"),
            ("Julio", "135,000"), ("Agosto", "138,000"), ("Septiembre", "142,000"),
            ("Octubre", "145,000"), ("Noviembre", "150,000"), ("Diciembre", "162,000"),
        ],
        "sales_story": "La serie muestra crecimiento sostenido y un cierre anual mas fuerte en noviembre y diciembre.",
        "notes": [
            "La empresa incremento ventas mediante contratos recurrentes de servicios.",
            "Mantiene caja suficiente para cubrir obligaciones corrientes.",
            "No se reportan litigios, garantias otorgadas ni deudas vencidas.",
        ],
        "expectation": "No deberia generar alertas automaticas con los umbrales actuales.",
        "cash_parameters": [
            ("Efectivo inicial:", "350,000"),
            ("Efectivo restringido:", "20,000"),
            ("Efectivo no restringido inicial:", "330,000"),
            ("Reserva minima operativa:", "120,000"),
            ("Compromiso extraordinario (mes 2):", "40,000"),
        ],
        "cash_budget": [
            ("Mes 1", "180,000", "130,000", "0", "380,000"),
            ("Mes 2", "170,000", "140,000", "40,000", "370,000"),
            ("Mes 3", "150,000", "120,000", "0", "400,000"),
        ],
        "cash_result": "S/ 210,000",
        "cash_explanation": "El menor saldo del horizonte, incluyendo el saldo inicial no restringido, es S/ 330,000. Al conservar S/ 120,000 de reserva, el excedente estimado es S/ 210,000.",
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
        "monthly_sales": [
            ("Enero", "30,000"), ("Febrero", "31,000"), ("Marzo", "32,000"),
            ("Abril", "32,000"), ("Mayo", "33,000"), ("Junio", "33,000"),
            ("Julio", "34,000"), ("Agosto", "34,000"), ("Septiembre", "35,000"),
            ("Octubre", "35,000"), ("Noviembre", "35,000"), ("Diciembre", "36,000"),
        ],
        "sales_story": "El resumen mensual muestra estabilidad con crecimiento gradual, pero no completa las cifras del balance general.",
        "notes": [
            "Este extracto no incluye el balance general completo ni cifras comparativas.",
            "La gerencia presento solo un resumen de caja, inventarios, ventas y utilidad.",
            "La informacion debe completarse antes de realizar una evaluacion financiera.",
        ],
        "expectation": "Varios indicadores deben quedar sin dato; preguntas sobre cifras ausentes deben responder no encontrado.",
        "cash_parameters": [
            ("Efectivo inicial:", "90,000"),
            ("Efectivo restringido:", "No informado"),
            ("Efectivo no restringido inicial:", "No calculable"),
            ("Reserva minima operativa:", "No informado"),
            ("Compromiso extraordinario (mes 2):", "15,000"),
        ],
        "cash_budget": [
            ("Mes 1", "50,000", "No informado", "0", "No calculable"),
            ("Mes 2", "40,000", "No informado", "15,000", "No calculable"),
            ("Mes 3", "30,000", "No informado", "0", "No calculable"),
        ],
        "cash_result": "No calculable",
        "cash_explanation": "Faltan efectivo restringido, pagos proyectados y reserva minima. El sistema no debe inferir ni inventar un excedente.",
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


def _cash_budget_table(rows, accent):
    headers = ["Periodo", "Cobros", "Pagos", "Compromisos", "Saldo"]
    data = [[Paragraph(value, STYLES["rf_budget_header"]) for value in headers]]
    data.extend([[Paragraph(value, STYLES["rf_budget_cell"]) for value in row] for row in rows])
    table = Table(data, colWidths=[27 * mm, 31 * mm, 36 * mm, 36 * mm, 30 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _monthly_sales_table(rows, accent):
    data = [[
        Paragraph("Mes 2025", STYLES["rf_budget_header"]),
        Paragraph("Ventas (S/)", STYLES["rf_budget_header"]),
        Paragraph("Variacion mensual", STYLES["rf_budget_header"]),
    ]]
    previous = None
    for month, raw_value in rows:
        value = int(raw_value.replace(",", ""))
        variation = "Base" if previous is None else f"{((value / previous) - 1) * 100:+.1f}%"
        data.append([
            Paragraph(f"{month} 2025:", STYLES["rf_budget_cell"]),
            Paragraph(raw_value, STYLES["rf_budget_cell"]),
            Paragraph(variation, STYLES["rf_budget_cell"]),
        ])
        previous = value
    table = Table(data, colWidths=[55 * mm, 55 * mm, 50 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def generate_scenario(scenario, output_dir=OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / scenario["filename"]
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
            PageBreak(),
            Paragraph("DISPONIBILIDAD DE EFECTIVO", STYLES["rf_eyebrow"]),
            Paragraph("Presupuesto de caja a 90 dias", STYLES["rf_title_small"]),
            Paragraph(
                "Escenario sintetico para estimar un excedente potencialmente invertible; no representa asesoria financiera.",
                STYLES["rf_subtitle"],
            ),
            Spacer(1, 6 * mm),
            Paragraph("Parametros de liquidez", STYLES["rf_section"]),
            Spacer(1, 2 * mm),
            _financial_table(scenario["cash_parameters"], scenario["accent"]),
            Spacer(1, 6 * mm),
            Paragraph("Proyeccion mensual antes de una nueva inversion", STYLES["rf_section"]),
            Spacer(1, 2 * mm),
            _cash_budget_table(scenario["cash_budget"], scenario["accent"]),
            Spacer(1, 5 * mm),
            Paragraph(
                "<b>Metodo:</b> excedente potencialmente invertible = maximo entre cero y el menor saldo proyectado del horizonte (incluido el saldo inicial no restringido) menos la reserva minima operativa.",
                STYLES["rf_note"],
            ),
            Spacer(1, 4 * mm),
            Table(
                [
                    [Paragraph("Excedente potencialmente invertible", STYLES["rf_expected_title"])],
                    [Paragraph(scenario["cash_result"], STYLES["rf_cash_result"])],
                    [Paragraph(scenario["cash_explanation"], STYLES["rf_expected_body"])],
                ],
                colWidths=[160 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
                        ("BOX", (0, 0), (-1, -1), 0.8, scenario["accent"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            ),
            PageBreak(),
            Paragraph("EVOLUCION DE VENTAS", STYLES["rf_eyebrow"]),
            Paragraph("Ventas mensuales - enero a diciembre de 2025", STYLES["rf_title_small"]),
            Paragraph(
                "Serie sintetica para evaluar tendencia y variacion mensual. Los doce meses concilian con las ventas anuales del estado de resultados.",
                STYLES["rf_subtitle"],
            ),
            Spacer(1, 6 * mm),
            _monthly_sales_table(scenario["monthly_sales"], scenario["accent"]),
            Spacer(1, 5 * mm),
            Table(
                [
                    [Paragraph("Lectura esperada", STYLES["rf_expected_title"])],
                    [Paragraph(scenario["sales_story"], STYLES["rf_expected_body"])],
                ],
                colWidths=[160 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
                        ("BOX", (0, 0), (-1, -1), 0.8, scenario["accent"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
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
STYLES.add(ParagraphStyle("rf_title_small", parent=STYLES["rf_title"], fontSize=19, leading=23))
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
STYLES.add(ParagraphStyle("rf_budget_header", parent=STYLES["rf_body"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white, alignment=TA_CENTER))
STYLES.add(ParagraphStyle("rf_budget_cell", parent=STYLES["rf_body"], fontSize=8, leading=10, alignment=TA_CENTER))
STYLES.add(ParagraphStyle("rf_cash_result", parent=STYLES["rf_amount"], fontSize=18, leading=22, textColor=colors.HexColor("#101828"), alignment=TA_LEFT))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        print(generate_scenario(scenario))


if __name__ == "__main__":
    main()
