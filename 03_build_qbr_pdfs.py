"""
03_build_qbr_pdfs.py

Generates one polished PDF QBR document per account -- the kind of
document a CSM would actually walk into a customer meeting with, or
attach to an internal renewal review.

Run: python3 03_build_qbr_pdfs.py
Output: qbr_reports/<account_name>_QBR.pdf  (one per account)
"""

import json
import os
import re

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, HRFlowable)

with open("qbr_accounts_with_narrative.json") as f:
    accounts = json.load(f)

os.makedirs("qbr_reports", exist_ok=True)
os.makedirs("_chart_tmp", exist_ok=True)

BAND_COLORS = {
    "Healthy": colors.HexColor("#3E8E5A"),
    "Neutral": colors.HexColor("#8FA6C2"),
    "At Risk": colors.HexColor("#E8A33D"),
    "Critical": colors.HexColor("#D64545"),
}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontSize=22, leading=26,
                           fontName="Helvetica-Bold", spaceAfter=4))
styles.add(ParagraphStyle(name="SubTitle", fontSize=11, textColor=colors.grey,
                           spaceAfter=14))
styles.add(ParagraphStyle(name="SectionHeader", fontSize=14, fontName="Helvetica-Bold",
                           spaceBefore=16, spaceAfter=8, textColor=colors.HexColor("#1F2937")))
styles.add(ParagraphStyle(name="Body", fontSize=10.5, leading=15))
styles.add(ParagraphStyle(name="BulletWin", fontSize=10.5, leading=15,
                           textColor=colors.HexColor("#2A6B41"), leftIndent=12))
styles.add(ParagraphStyle(name="BulletRisk", fontSize=10.5, leading=15,
                           textColor=colors.HexColor("#A83232"), leftIndent=12))


def make_trend_chart(acct, filepath):
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    q = acct["quarters"]
    ax.plot(q, acct["health_score_by_quarter"], marker="o", linewidth=2.5,
            color="#2E5A9C", label="Health Score")
    ax.plot(q, acct["usage_score_by_quarter"], marker="o", linewidth=2, linestyle="--",
            color="#8FA6C2", label="Usage Score")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Score (0-100)")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close(fig)


def safe_filename(name):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name)


def build_pdf(acct):
    fname = f"qbr_reports/{safe_filename(acct['name'])}_QBR.pdf"
    chart_path = f"_chart_tmp/{safe_filename(acct['name'])}_trend.png"
    make_trend_chart(acct, chart_path)

    doc = SimpleDocTemplate(fname, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                             leftMargin=0.7 * inch, rightMargin=0.7 * inch)
    story = []

    # --- Header ---
    story.append(Paragraph(f"{acct['name']}", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Quarterly Business Review &nbsp;|&nbsp; {acct['quarters'][-1]} &nbsp;|&nbsp; "
        f"CSM: {acct['csm']}", styles["SubTitle"]))

    # --- Key metrics table ---
    band_color = BAND_COLORS[acct["current_health_band"]]
    metrics_data = [
        ["ARR", "Segment", "Health Score", "Health Band", "Renewal In"],
        [f"${acct['arr']:,}", acct["segment"], f"{acct['current_health_score']:.0f} / 100",
         acct["current_health_band"], f"{acct['renewal_in_days']} days"],
    ]
    t = Table(metrics_data, colWidths=[1.15 * inch] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("BACKGROUND", (3, 1), (3, 1), band_color),
        ("TEXTCOLOR", (3, 1), (3, 1), colors.white),
        ("FONTNAME", (3, 1), (3, 1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # --- Executive summary ---
    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
    story.append(Paragraph(acct["narrative"]["executive_summary"], styles["Body"]))
    story.append(Spacer(1, 6))

    # --- Trend chart ---
    story.append(Paragraph("Health & Usage Trend (Trailing 4 Quarters)", styles["SectionHeader"]))
    story.append(Image(chart_path, width=6.2 * inch, height=2.6 * inch))

    # --- Wins & Risks ---
    story.append(Paragraph("Wins", styles["SectionHeader"]))
    if acct["wins"]:
        for w in acct["wins"]:
            story.append(Paragraph(f"\u2713 {w}", styles["BulletWin"]))
    else:
        story.append(Paragraph("No notable wins logged this quarter.", styles["Body"]))

    story.append(Paragraph("Risks", styles["SectionHeader"]))
    if acct["risks"]:
        for r in acct["risks"]:
            story.append(Paragraph(f"\u26a0 {r}", styles["BulletRisk"]))
    else:
        story.append(Paragraph("No active risk factors identified.", styles["Body"]))

    # --- Recommendation ---
    story.append(Paragraph("Recommended Next Step", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D1D5DB")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(acct["narrative"]["recommendation"], styles["Body"]))

    doc.build(story)
    return fname


generated = [build_pdf(a) for a in accounts]
print(f"Generated {len(generated)} QBR reports in qbr_reports/:")
for g in generated:
    print(f"  {g}")
