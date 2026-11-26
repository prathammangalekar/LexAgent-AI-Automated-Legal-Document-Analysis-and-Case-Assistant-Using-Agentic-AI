"""Generates realistic sample PDF and DOCX files for testing and evaluation."""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document

DOCS_DIR = Path(__file__).resolve().parent / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_pdf():
    pdf_path = DOCS_DIR / "sample_employment_agreement.pdf"
    txt_path = DOCS_DIR / "sample_employment_agreement.txt"
    if not txt_path.exists():
        return
    text = txt_path.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=13)

    story = [
        Paragraph("<b>EMPLOYMENT AND NON-DISCLOSURE AGREEMENT</b>", title_style),
        Spacer(1, 14),
    ]

    for paragraph in text.split("\n\n"):
        clean_p = paragraph.strip().replace("\n", " ")
        if clean_p:
            story.append(Paragraph(clean_p, body_style))
            story.append(Spacer(1, 8))

    doc.build(story)
    print(f"Generated PDF: {pdf_path}")


def create_sample_docx():
    docx_path = DOCS_DIR / "sample_dispute_case_brief.docx"
    txt_path = DOCS_DIR / "sample_dispute_case_brief.txt"
    if not txt_path.exists():
        return
    text = txt_path.read_text(encoding="utf-8")

    doc = Document()
    doc.add_heading("MASTER SERVICES AGREEMENT AND DISPUTE BRIEF", 0)
    for p in text.split("\n\n"):
        clean_p = p.strip().replace("\n", " ")
        if clean_p:
            doc.add_paragraph(clean_p)

    doc.save(str(docx_path))
    print(f"Generated DOCX: {docx_path}")


if __name__ == "__main__":
    create_sample_pdf()
    create_sample_docx()
