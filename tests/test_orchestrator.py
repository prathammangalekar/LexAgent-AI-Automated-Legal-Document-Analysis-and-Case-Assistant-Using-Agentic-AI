"""End-to-end integration tests for LangGraph multi-agent orchestrator."""

import pytest
from pathlib import Path
from lexagent_ai.orchestrator.workflow import LexAgentWorkflowEngine
from lexagent_ai.memory.case_memory import global_case_memory

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"


def test_workflow_a_document_analysis():
    """Tests Workflow A end-to-end execution on sample employment agreement."""
    engine = LexAgentWorkflowEngine()
    sample_file = DOCS_DIR / "sample_employment_agreement.txt"

    report = engine.execute_workflow_a_document_analysis(sample_file)
    assert report is not None
    assert report.report_id.startswith("LEX_")
    assert report.legal_clause_analysis is not None
    assert len(report.legal_clause_analysis.high_risk_clauses) >= 2
    assert report.legal_research is not None
    assert report.case_reasoning is not None
    assert report.verification_audit.is_approved is True
    assert report.pdf_path is not None
    assert Path(report.pdf_path).exists()


def test_workflow_b_case_research():
    """Tests Workflow B on autonomous legal research query."""
    engine = LexAgentWorkflowEngine()
    query = "What is the legal standard for proving liquidated damages under Indian Contract Act Section 74?"

    report = engine.execute_workflow_b_case_research(query)
    assert report is not None
    assert report.legal_research is not None
    assert any("Kailash Nath" in j.case_or_statute_title for j in report.legal_research.landmark_judgments)
    assert report.verification_audit.is_approved is True


def test_workflow_c_case_comparison():
    """Tests Workflow C on case comparison brief."""
    engine = LexAgentWorkflowEngine()
    brief_file = DOCS_DIR / "sample_dispute_case_brief.txt"

    report = engine.execute_workflow_c_case_comparison(brief_file)
    assert report is not None
    assert report.case_comparison is not None
    assert len(report.case_comparison.comparator_cases) > 0
    assert len(report.case_comparison.factual_convergences) > 0


def test_workflow_d_legal_drafting():
    """Tests Workflow D for generating formal legal notice."""
    engine = LexAgentWorkflowEngine()
    instructions = "Draft a formal legal notice demanding payment of withheld milestone fees under Section 73 Indian Contract Act."

    report = engine.execute_workflow_d_legal_drafting(instructions)
    assert report is not None
    assert report.generated_draft is not None
    assert "WITHOUT PREJUDICE" in report.generated_draft.formal_body
    assert len(report.generated_draft.placeholders) > 0


def test_workflow_e_complex_investigation():
    """Tests Workflow E for full multi-agent investigation dossier."""
    engine = LexAgentWorkflowEngine()
    brief_file = DOCS_DIR / "sample_dispute_case_brief.txt"

    report = engine.execute_workflow_e_complex_investigation(brief_file)
    assert report is not None
    assert report.document_intelligence is not None
    assert report.legal_clause_analysis is not None
    assert report.legal_research is not None
    assert report.case_reasoning is not None
    assert report.case_comparison is not None
    assert report.verification_audit is not None
    assert Path(report.docx_path).exists()


def test_case_memory_isolation():
    """Tests that separate cases maintain isolated state in memory."""
    global_case_memory.clear_case("TEST_CASE_1")
    global_case_memory.clear_case("TEST_CASE_2")

    global_case_memory.add_facts("TEST_CASE_1", ["Fact A: Contract signed on 2024-01-15"])
    global_case_memory.add_facts("TEST_CASE_2", ["Fact B: Lease deed executed on 2023-08-10"])

    facts_1 = global_case_memory.get_facts("TEST_CASE_1")
    facts_2 = global_case_memory.get_facts("TEST_CASE_2")

    assert len(facts_1) == 1
    assert "Fact A" in facts_1[0]
    assert len(facts_2) == 1
    assert "Fact B" in facts_2[0]
    assert "Fact A" not in facts_2[0]
