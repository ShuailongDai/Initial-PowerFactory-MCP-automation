from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "outputs" / "n_minus_1_short_circuit_bus_5.csv"
PDF_PATH = ROOT / "outputs" / "Innovation_Project_Idea_PowerFactory_MCP.pdf"


def load_results() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: str, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}"


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, "Innovation project idea - PowerFactory MCP automation")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = load_results()
    worst = min(rows, key=lambda r: float(r["short_circuit_power_mva"]))
    best = max(rows, key=lambda r: float(r["short_circuit_power_mva"]))

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyText2",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#111111"),
            backColor=colors.HexColor("#F1F3F5"),
            borderPadding=8,
            spaceBefore=8,
            spaceAfter=10,
        )
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="PowerFactory MCP Automation Innovation Project Idea",
    )

    story = []
    story.append(Paragraph("PowerFactory MCP Automation", styles["TitleCenter"]))
    story.append(
        Paragraph(
            "Innovation project idea for natural-language grid simulation, N-1 contingency testing, and short-circuit capacity assessment",
            styles["BodyText2"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "Executive summary",
            styles["Section"],
        )
    )
    story.append(
        Paragraph(
            "This proposal demonstrates a practical automation layer that connects natural-language requests to DIgSILENT PowerFactory through an MCP-based control workflow. The prototype executes simulation tasks, extracts engineering results, and converts them into structured evidence without requiring repetitive manual interaction.",
            styles["BodyText2"],
        )
    )
    story.append(
        Paragraph(
            f"In the proof of concept, the system ran a line N-1 short-circuit study at Bus 5 across {len(rows)} transmission-line outages. The most constraining contingency was {worst['outaged_line']}, with Skss = {fmt(worst['short_circuit_power_mva'])} MVA and Ikss = {fmt(worst['short_circuit_current_ka'], 4)} kA.",
            styles["Callout"],
        )
    )

    story.append(Paragraph("Problem and opportunity", styles["Section"]))
    for text in [
        "Power-system studies often require repeated operational steps: change network status, run a calculation, export results, restore the model, and document evidence.",
        "These workflows are high-value but repetitive. Manual execution increases cycle time and makes it harder to maintain a consistent audit trail across scenarios.",
        "A natural-language automation layer can let engineers specify the intent while the system performs the deterministic PowerFactory operations and records the outputs.",
    ]:
        story.append(Paragraph(text, styles["BodyText2"]))

    story.append(Paragraph("Proposed method", styles["Section"]))
    method_data = [
        ["Layer", "Role"],
        ["Natural-language interface", "Engineer requests tasks such as run load flow, list buses, or run N-1 short-circuit study."],
        ["MCP server", "Converts the request into controlled tool calls and waits for structured responses."],
        ["PowerFactory in-app agent", "Runs inside PowerFactory and executes API operations on the active project."],
        ["Result layer", "Exports tables, CSV files, and proposal-ready evidence."],
    ]
    table = Table(method_data, colWidths=[4.4 * cm, 11 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8BCC4")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)

    story.append(PageBreak())
    story.append(Paragraph("Proof-of-concept workflow", styles["Section"]))
    workflow = [
        "1. Start PowerFactory and run the MCP_Agent Python script inside the active project.",
        "2. Send natural-language instructions through the MCP bridge.",
        "3. Run base calculations and validate communication with the active project.",
        "4. Execute line N-1 logic: open one line, run three-phase short-circuit at Bus 5, capture Ikss and Skss, restore the line, and repeat.",
        "5. Export a CSV evidence file and summarize the limiting contingency.",
    ]
    for item in workflow:
        story.append(Paragraph(item, styles["BodyText2"]))

    story.append(Paragraph("Validation result - Bus 5 N-1 short-circuit study", styles["Section"]))
    result_table_data = [["Outaged line", "Ikss (kA)", "Skss (MVA)", "Status"]]
    for row in rows:
        result_table_data.append(
            [
                row["outaged_line"],
                fmt(row["short_circuit_current_ka"], 4),
                fmt(row["short_circuit_power_mva"], 2),
                "OK" if row["executed"] == "True" and row["return_code"] == "0" else "Check",
            ]
        )
    result_table = Table(result_table_data, colWidths=[4.6 * cm, 3.2 * cm, 3.4 * cm, 2.4 * cm])
    result_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (2, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8BCC4")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(result_table)
    story.append(
        Paragraph(
            f"The result identifies {worst['outaged_line']} as the limiting N-1 line outage for Bus 5 short-circuit capacity. The observed Skss range is {fmt(worst['short_circuit_power_mva'])} to {fmt(best['short_circuit_power_mva'])} MVA.",
            styles["BodyText2"],
        )
    )

    story.append(Paragraph("Innovation value", styles["Section"]))
    for text in [
        "Faster study cycles: repeatable scenario execution can reduce manual setup and export time.",
        "Better engineering traceability: each scenario is linked to a structured command, result row, and output file.",
        "Scalable study coverage: the same approach can extend from line N-1 to transformer outages, generator dispatch cases, protection studies, and batch reporting.",
        "Lower barrier for non-specialists: engineers can request studies in plain English while retaining deterministic PowerFactory execution.",
    ]:
        story.append(Paragraph(text, styles["BodyText2"]))

    story.append(Paragraph("Recommended next steps", styles["Section"]))
    next_steps = [
        ["Phase", "Deliverable"],
        ["Pilot hardening", "Add validation checks, error handling, and study-case snapshot/restore controls."],
        ["Use-case expansion", "Add transformer N-1, bus fault sweeps, load-flow violation checks, and standard report generation."],
        ["Governance", "Define approved command library, audit logging, and model change safeguards."],
        ["Deployment", "Package MCP configuration and PowerFactory agent for repeatable installation."],
    ]
    next_table = Table(next_steps, colWidths=[4.2 * cm, 11.2 * cm])
    next_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8BCC4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(next_table)

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build_pdf()
