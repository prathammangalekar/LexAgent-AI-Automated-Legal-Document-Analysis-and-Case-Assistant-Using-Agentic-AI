"""Report Generator producing formatted PDF, DOCX, and Markdown legal reports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from lexagent_ai.config import settings
from lexagent_ai.models.schemas import ComprehensiveLegalReport


class LegalReportGenerator:
    """Exports comprehensive multi-agent legal analyses to PDF and DOCX formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_pdf(self, report: ComprehensiveLegalReport, filename: Optional[str] = None) -> str:
        """Generates a professional PDF legal report using ReportLab."""
        fname = filename or f"{report.report_id}.pdf"
        pdf_path = self.output_dir / fname

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom professional typography styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1A365D'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#4A5568')
        )
        section_style = ParagraphStyle(
            'SecHead',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#2B6CB0'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#2D3748')
        )
        bold_body = ParagraphStyle(
            'BoldBody',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        alert_style = ParagraphStyle(
            'Alert',
            parent=body_style,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#9B2C2C')
        )
        table_cell = ParagraphStyle(
            'Cell',
            parent=body_style,
            fontSize=8,
            leading=10
        )

        story = []

        # Header Banner
        header_data = [
            [
                Paragraph("<b>LEXAGENT AI - AUTONOMOUS LEGAL INTELLIGENCE SYSTEM</b>", title_style),
                Paragraph(f"<b>Report ID:</b> {report.report_id}<br/><b>Date:</b> {report.generated_at}", subtitle_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[380, 150])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_header)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A365D'), spaceAfter=10))

        # Document / Workflow Title
        story.append(Paragraph(f"<b>Title:</b> {report.report_title}", title_style))
        story.append(Paragraph(f"<b>Workflow Executed:</b> {report.workflow_executed}", subtitle_style))
        story.append(Spacer(1, 10))

        # Executive Summary
        story.append(Paragraph("1. EXECUTIVE SUMMARY", section_style))
        story.append(Paragraph(report.executive_summary, body_style))
        story.append(Spacer(1, 10))

        # Clause Risk Analysis (if present)
        if report.legal_clause_analysis and report.legal_clause_analysis.analyzed_clauses:
            story.append(Paragraph("2. LEGAL CLAUSE & RISK ANALYSIS", section_style))
            clause_rows = [["Clause ID", "Heading", "Risk Level", "Legal Assessment / Impact"]]
            for c in report.legal_clause_analysis.analyzed_clauses:
                risk_color = "#C53030" if c.risk_level in ["high", "critical"] else "#DD6B20" if c.risk_level == "medium" else "#2F855A"
                risk_p = Paragraph(f"<font color='{risk_color}'><b>{c.risk_level.upper()}</b></font>", table_cell)
                desc = Paragraph(f"<b>{c.plain_english_summary}</b><br/>{c.recommendation}", table_cell)
                clause_rows.append([
                    Paragraph(c.clause_id, table_cell),
                    Paragraph(c.clause_title, table_cell),
                    risk_p,
                    desc
                ])

            t_clauses = Table(clause_rows, colWidths=[65, 110, 65, 290])
            t_clauses.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1A202C')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_clauses)
            story.append(Spacer(1, 10))

        # Legal Research & Verified Authorities (if present)
        if report.legal_research and report.legal_research.landmark_judgments:
            story.append(Paragraph("3. VERIFIED JUDICIAL PRECEDENTS & STATUTORY AUTHORITIES", section_style))
            for j in report.legal_research.landmark_judgments:
                prec_box = [
                    [Paragraph(f"<b>{j.case_or_statute_title}</b> | <b>Citation:</b> {j.standardized_citation}", bold_body)],
                    [Paragraph(f"<b>Court:</b> {j.court_name} ({j.year}) | <b>Status:</b> {j.status.value.upper()}", subtitle_style)],
                    [Paragraph(f"<b>Binding Principle (Ratio):</b> {j.ratio_or_rule}", body_style)],
                    [Paragraph(f"<b>Relevant Excerpt:</b> <i>\"{j.relevant_excerpt}\"</i>", subtitle_style)]
                ]
                t_prec = Table(prec_box, colWidths=[530])
                t_prec.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7FAFC')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
                    ('LINELEFT', (0, 0), (0, -1), 3.0, colors.HexColor('#2B6CB0')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(t_prec)
                story.append(Spacer(1, 6))

        # Legal Reasoning & IRAC Breakdown (if present)
        if report.case_reasoning and report.case_reasoning.framed_issues:
            story.append(Paragraph("4. STRUCTURED LEGAL REASONING (IRAC ANALYSIS)", section_style))
            for issue in report.case_reasoning.framed_issues:
                story.append(Paragraph(f"<b>Issue {issue.issue_id}:</b> {issue.framed_question}", bold_body))
                story.append(Paragraph(f"<b>Governing Rules:</b> {', '.join(issue.governing_rules)}", body_style))
                story.append(Paragraph(f"<b>Petitioner / Claimant Arguments:</b>", bold_body))
                for arg in issue.claimant_arguments:
                    story.append(Paragraph(f"• {arg}", body_style))
                story.append(Paragraph(f"<b>Respondent Defense Arguments:</b>", bold_body))
                for arg in issue.respondent_arguments:
                    story.append(Paragraph(f"• {arg}", body_style))
                story.append(Paragraph(f"<b>Evidentiary Analysis:</b> {issue.evidence_appraisal}", body_style))
                story.append(Paragraph(f"<b>IRAC Synthesis & Outcome Assessment:</b> {issue.irac_synthesis}", body_style))
                story.append(Spacer(1, 8))

        # Verification & Hallucination Audit
        story.append(Paragraph("5. VERIFICATION & ANTI-HALLUCINATION AUDIT", section_style))
        audit = report.verification_audit
        audit_status_color = "#2F855A" if audit.is_approved else "#C53030"
        status_text = "APPROVED - ALL CITATIONS GROUNDED" if audit.is_approved else "ACTION REQUIRED - ISSUES DETECTED"
        story.append(Paragraph(
            f"<b>Audit Result:</b> <font color='{audit_status_color}'><b>{status_text}</b></font> | "
            f"<b>Confidence:</b> {audit.confidence_score * 100:.1f}% | "
            f"<b>Verified Citations:</b> {audit.verified_citations_count}/{audit.total_citations_evaluated}",
            body_style
        ))
        if audit.issues:
            for iss in audit.issues:
                story.append(Paragraph(f"• [{iss.issue_type}] {iss.flawed_text}: {iss.reason}", alert_style))
        story.append(Spacer(1, 10))

        # Generated Draft (if present)
        if report.generated_draft:
            story.append(Paragraph("6. GENERATED LEGAL INSTRUMENT DRAFT", section_style))
            story.append(Paragraph(f"<b>Draft Type:</b> {report.generated_draft.draft_type.value.upper()}", bold_body))
            story.append(Paragraph(f"<b>Subject / Caption:</b> {report.generated_draft.caption_or_subject}", subtitle_style))
            story.append(Spacer(1, 4))

            draft_box = [[Paragraph(report.generated_draft.formal_body.replace("\n", "<br/>"), body_style)]]
            t_draft = Table(draft_box, colWidths=[530])
            t_draft.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#4A5568')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t_draft)
            story.append(Spacer(1, 10))

        # Lawyer Clarification Checklist & Recommendations
        if report.lawyer_clarification_checklist:
            story.append(Paragraph("7. ADVOCATE ACTION & CLARIFICATION CHECKLIST", section_style))
            for item in report.lawyer_clarification_checklist:
                story.append(Paragraph(f"[ ] {item}", body_style))
            story.append(Spacer(1, 8))

        # Mandatory Regulatory Disclaimer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=10, spaceAfter=8))
        story.append(Paragraph(f"<b>MANDATORY LEGAL DISCLAIMER:</b> {report.disclaimer}", alert_style))

        doc.build(story)
        report.pdf_path = str(pdf_path)
        return str(pdf_path)

    def generate_docx(self, report: ComprehensiveLegalReport, filename: Optional[str] = None) -> str:
        """Generates a structured Word (.docx) document report."""
        fname = filename or f"{report.report_id}.docx"
        docx_path = self.output_dir / fname

        doc = Document()
        # Title
        doc.add_heading(report.report_title, level=0)
        p_sub = doc.add_paragraph()
        p_sub.add_run(f"Report ID: {report.report_id} | Date: {report.generated_at}\n")
        p_sub.add_run(f"Workflow: {report.workflow_executed}")

        # Executive Summary
        doc.add_heading("1. Executive Summary", level=1)
        doc.add_paragraph(report.executive_summary)

        # Clause Risk Analysis
        if report.legal_clause_analysis and report.legal_clause_analysis.analyzed_clauses:
            doc.add_heading("2. Legal Clause & Risk Analysis", level=1)
            table = doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Clause ID"
            hdr_cells[1].text = "Heading"
            hdr_cells[2].text = "Risk Level"
            hdr_cells[3].text = "Analysis & Recommendation"

            for c in report.legal_clause_analysis.analyzed_clauses:
                row_cells = table.add_row().cells
                row_cells[0].text = c.clause_id
                row_cells[1].text = c.clause_title
                row_cells[2].text = c.risk_level.upper()
                row_cells[3].text = f"{c.plain_english_summary}\n\nRecommendation: {c.recommendation}"

        # Legal Research & Precedents
        if report.legal_research and report.legal_research.landmark_judgments:
            doc.add_heading("3. Verified Precedents & Legal Authorities", level=1)
            for j in report.legal_research.landmark_judgments:
                p = doc.add_paragraph()
                p.add_run(f"{j.case_or_statute_title} ({j.standardized_citation})\n").bold = True
                p.add_run(f"Court: {j.court_name} ({j.year}) | Status: {j.status.value.upper()}\n")
                p.add_run(f"Binding Ratio: {j.ratio_or_rule}\n")
                p.add_run(f"Excerpt: \"{j.relevant_excerpt}\"")

        # Legal Reasoning (IRAC)
        if report.case_reasoning and report.case_reasoning.framed_issues:
            doc.add_heading("4. Structured Legal Reasoning (IRAC)", level=1)
            for issue in report.case_reasoning.framed_issues:
                doc.add_heading(f"Issue {issue.issue_id}: {issue.framed_question}", level=2)
                doc.add_paragraph(f"Governing Provisions: {', '.join(issue.governing_rules)}")
                doc.add_paragraph("Claimant Arguments: " + " | ".join(issue.claimant_arguments))
                doc.add_paragraph("Respondent Arguments: " + " | ".join(issue.respondent_arguments))
                doc.add_paragraph(f"Evidentiary Appraisal: {issue.evidence_appraisal}")
                doc.add_paragraph(f"Synthesis & Risk: {issue.irac_synthesis}")

        # Verification Audit
        doc.add_heading("5. Verification and Anti-Hallucination Audit", level=1)
        audit = report.verification_audit
        p_audit = doc.add_paragraph()
        p_audit.add_run(f"Verification Approved: {audit.is_approved}\n").bold = True
        p_audit.add_run(f"Confidence Score: {audit.confidence_score * 100:.1f}%\n")
        p_audit.add_run(f"Citations Evaluated: {audit.verified_citations_count}/{audit.total_citations_evaluated}\n")
        if audit.issues:
            for iss in audit.issues:
                p_iss = doc.add_paragraph(f"[{iss.issue_type}] {iss.flawed_text}: {iss.reason}")
                p_iss.paragraph_format.left_indent = Inches(0.25)

        # Generated Draft
        if report.generated_draft:
            doc.add_heading("6. Generated Legal Draft", level=1)
            doc.add_paragraph(f"Subject: {report.generated_draft.caption_or_subject}").bold = True
            doc.add_paragraph(report.generated_draft.formal_body)

        # Checklist
        if report.lawyer_clarification_checklist:
            doc.add_heading("7. Advocate Checklist", level=1)
            for item in report.lawyer_clarification_checklist:
                doc.add_paragraph(f"[ ] {item}")

        # Disclaimer
        doc.add_heading("Disclaimer", level=1)
        doc.add_paragraph(report.disclaimer)

        doc.save(str(docx_path))
        report.docx_path = str(docx_path)
        return str(docx_path)
