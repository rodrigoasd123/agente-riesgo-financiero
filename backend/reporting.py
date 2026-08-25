"""Exportaciones auditables en CSV y PDF, generadas completamente en memoria."""

from __future__ import annotations

import csv
import io
import json
import re
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def safe_stem(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")
    return (cleaned or "analisis_financiero")[:80]


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def generar_csv(analysis: dict, projection: dict | None = None) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["seccion", "concepto", "valor", "detalle"])
    writer.writerow(["metadatos", "archivo", _csv_cell(analysis["filename"]), ""])
    writer.writerow(["metadatos", "fecha_analisis", _csv_cell(analysis["created_at"]), ""])
    for key, value in json.loads(analysis["cifras_json"]).items():
        writer.writerow(["cifras", _csv_cell(key), _csv_cell(value), ""])
    for key, value in json.loads(analysis["indicadores_json"]).items():
        writer.writerow(["indicadores", _csv_cell(key), _csv_cell(value), ""])
    for alert in json.loads(analysis["alertas_json"]):
        writer.writerow(["alertas", _csv_cell(alert.get("codigo")), _csv_cell(alert.get("severidad")), _csv_cell(alert.get("mensaje"))])
    writer.writerow(["resumen", "resumen_ejecutivo", _csv_cell(analysis["resumen"]), ""])
    if projection:
        writer.writerow(["proyeccion", "VAN", _csv_cell(projection["van"]), ""])
        writer.writerow(["proyeccion", "TIR_porcentaje", _csv_cell(projection["tir_percent"]), ""])
        writer.writerow(["proyeccion", "periodo_recuperacion", _csv_cell(projection["periodo_recuperacion"]), ""])
        for row in projection["flujos"]:
            writer.writerow(["flujo_caja", f"periodo_{row['periodo']}", _csv_cell(row["flujo"]), f"acumulado={_csv_cell(row['flujo_acumulado'])}"])
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def _table(rows: list[list[object]], widths: list[float]) -> Table:
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["BodyText"],
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    safe_rows = [
        [
            Paragraph(
                escape("—" if value is None else str(value)),
                header_style if row_index == 0 else styles["BodyText"],
            )
            for value in row
        ]
        for row_index, row in enumerate(rows)
    ]
    table = Table(safe_rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#153448")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4CC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F8")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def generar_pdf(analysis: dict, projection: dict | None = None) -> bytes:
    stream = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#153448")))
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=17 * mm, title="Reporte de riesgo financiero")
    story = [
        Paragraph("Reporte de análisis de riesgo financiero", styles["TitleCenter"]),
        Spacer(1, 6 * mm),
        Paragraph(f"<b>Documento:</b> {escape(analysis['filename'])}", styles["BodyText"]),
        Paragraph(f"<b>Fecha UTC:</b> {escape(analysis['created_at'])}", styles["BodyText"]),
        Spacer(1, 5 * mm),
        Paragraph("Resumen ejecutivo", styles["Heading2"]),
        Paragraph(escape(analysis["resumen"]), styles["BodyText"]),
        Spacer(1, 4 * mm),
    ]
    cifras = json.loads(analysis["cifras_json"])
    indicators = json.loads(analysis["indicadores_json"])
    alerts = json.loads(analysis["alertas_json"])
    story += [Paragraph("Cifras extraídas", styles["Heading2"]), _table([["Concepto", "Valor"], *[[k, v] for k, v in cifras.items()]], [105 * mm, 50 * mm]), Spacer(1, 4 * mm)]
    story += [Paragraph("Indicadores calculados", styles["Heading2"]), _table([["Indicador", "Valor"], *[[k, v] for k, v in indicators.items()]], [105 * mm, 50 * mm]), Spacer(1, 4 * mm)]
    alert_rows = [["Código", "Severidad", "Detalle"], *[[a.get("codigo"), a.get("severidad"), a.get("mensaje")] for a in alerts]]
    if len(alert_rows) == 1:
        alert_rows.append(["Sin alertas", "—", "No se detectaron alertas con los umbrales configurados."])
    story += [Paragraph("Alertas", styles["Heading2"]), _table(alert_rows, [36 * mm, 28 * mm, 91 * mm])]
    if projection:
        story += [PageBreak(), Paragraph("Escenario de flujo de caja", styles["Heading2"]), Paragraph("Estos valores provienen de los flujos ingresados por el usuario; no se infieren del PDF.", styles["BodyText"])]
        story += [_table([
            ["Métrica", "Resultado"],
            ["VAN", projection["van"]],
            ["TIR (%)", projection["tir_percent"]],
            ["Periodo de recuperación", projection["periodo_recuperacion"]],
        ], [105 * mm, 50 * mm]), Spacer(1, 4 * mm)]
        story += [_table([["Periodo", "Flujo", "Acumulado"], *[[r["periodo"], r["flujo"], r["flujo_acumulado"]] for r in projection["flujos"]]], [45 * mm, 55 * mm, 55 * mm])]
    story += [Spacer(1, 7 * mm), Paragraph("Aviso: herramienta de apoyo académico. Verifique cifras, supuestos y conclusiones con un profesional antes de tomar decisiones financieras.", styles["Italic"])]

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#52646F"))
        canvas.drawCentredString(A4[0] / 2, 9 * mm, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()
