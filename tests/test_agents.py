"""Unit tests for all 8 specialized agents of LexAgent AI."""

import pytest
from pathlib import Path
from lexagent_ai.agents.document_agent import DocumentIntelligenceAgent
from lexagent_ai.agents.legal_analysis_agent import LegalAnalysisAgent
from lexagent_ai.agents.research_agent import LegalResearchAgent
from lexagent_ai.agents.case_comparison_agent import CaseComparisonAgent
from lexagent_ai.agents.reasoning_agent import CaseReasoningAgent
from lexagent_ai.agents.drafting_agent import LegalDraftingAgent
from lexagent_ai.agents.verification_agent import VerificationAgent
from lexagent_ai.agents.report_agent import ReportGenerationAgent
from lexagent_ai.models.schemas import DocumentCategory, ClauseRiskLevel, DraftType

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"


def test_agent_1_document_intelligence():
    """Tests Agent 1 ingestion, clause parsing, and entity extraction."""
    agent = DocumentIntelligenceAgent()
    sample_file = DOCS_DIR / "sample_employment_agreement.txt"
    assert sample_file.exists()

    doc = agent.process_file(sample_file)
    assert doc.category == DocumentCategory.EMPLOYMENT_AGREEMENT
    assert len(doc.parties) >= 2
    assert any("technova" in p.name.lower() for p in doc.parties)
    assert any("arjun menon" in p.name.lower() for p in doc.parties)
    assert len(doc.clauses) >= 4
    assert any("8" in c.clause_id for c in doc.clauses)
    assert len(doc.chunks) > 0


def test_agent_2_legal_analysis():
    """Tests Agent 2 clause risk classification and doctrinal analysis."""
    doc_agent = DocumentIntelligenceAgent()
    analysis_agent = LegalAnalysisAgent()
    sample_file = DOCS_DIR / "sample_employment_agreement.txt"

    doc = doc_agent.process_file(sample_file)
    analysis = analysis_agent.analyze_document(doc)

    assert analysis.overall_risk_score > 0.5
    assert len(analysis.high_risk_clauses) >= 2
    # Check Section 27 non-compete detection
    non_compete = next((c for c in analysis.high_risk_clauses if "Clause 8" in c.clause_id), None)
    assert non_compete is not None
    assert non_compete.risk_level == ClauseRiskLevel.CRITICAL
    assert "Section 27" in non_compete.applicable_statute

    # Check that factual assertions and interpretations are distinguished
    assert len(analysis.factual_assertions) > 0
    assert len(analysis.interpretative_inferences) > 0


def test_agent_3_legal_research():
    """Tests Agent 3 research formulation and authentic citation retrieval."""
    agent = LegalResearchAgent()
    query = "Whether post-employment non-compete clauses are valid under Indian Contract Act Section 27"

    research = agent.conduct_research(query)
    assert len(research.legal_topics) > 0
    assert len(research.landmark_judgments) > 0
    assert any("Percept D'Mark" in j.case_or_statute_title for j in research.landmark_judgments)
    assert "(2006) 4 SCC 227" in [j.standardized_citation for j in research.landmark_judgments]
    assert "July 1, 2024" in research.temporal_framework_analysis


def test_agent_4_case_comparison():
    """Tests Agent 4 precedent comparison, convergences, and distinctions."""
    agent = CaseComparisonAgent()
    brief = "Dispute regarding unilateral deduction of liquidated damages under milestone agreement without proving loss."

    comparison = agent.compare_cases(brief, primary_title="Milestone Dispute")
    assert len(comparison.comparator_cases) > 0
    assert len(comparison.factual_convergences) > 0
    assert len(comparison.strategic_litigation_insights) > 0


def test_agent_5_case_reasoning():
    """Tests Agent 5 IRAC legal reasoning and lawyer question generation."""
    agent = CaseReasoningAgent()
    brief = (
        "Employer seeks to enforce Clause 8 pan-India non-compete for 3 years against software architect, "
        "and withhold INR 25,00,000 as liquidated damages under Clause 11."
    )

    reasoning = agent.reason_case("Technova Dispute", brief)
    assert len(reasoning.framed_issues) >= 2
    # Verify IRAC issue 1
    issue1 = reasoning.framed_issues[0]
    assert len(issue1.governing_rules) > 0
    assert len(issue1.claimant_arguments) > 0
    assert len(issue1.respondent_arguments) > 0
    assert "APPLICATION:" in issue1.irac_synthesis
    assert len(reasoning.questions_for_counsel) > 0


def test_agent_6_legal_drafting():
    """Tests Agent 6 legal notice and reply drafting in Indian legal format."""
    agent = LegalDraftingAgent()
    draft = agent.generate_draft(
        draft_type=DraftType.LEGAL_NOTICE,
        case_title="Menon v. Technova",
        facts_summary="Unlawful withholding of dues and assertion of void non-compete restriction.",
        claimant_name="Arjun Menon",
        respondent_name="Technova Solutions Pvt. Ltd."
    )

    assert draft.draft_type == DraftType.LEGAL_NOTICE
    assert "WITHOUT PREJUDICE" in draft.formal_body
    assert "Arjun Menon" in draft.formal_body
    assert "Technova Solutions" in draft.formal_body
    assert "Section 27" in draft.formal_body
    assert len(draft.placeholders) > 0
    assert "ADVOCA" in draft.mandatory_disclaimer


def test_agent_7_verification():
    """Tests Agent 7 citation checking and hallucination rejection."""
    agent = VerificationAgent()

    # Legitimate verified citations
    report_valid = agent.audit_agent_outputs(
        document_date="2023-01-01"
    )
    assert report_valid.is_approved is True

    # Check that fabricated citation triggers failure
    from lexagent_ai.models.schemas import LegalResearchResult, VerifiedCitation, CitationVerificationStatus
    fake_research = LegalResearchResult(
        research_query="Test Fake",
        legal_topics=["Contract Law"],
        landmark_judgments=[
            VerifiedCitation(
                citation_raw="Bogus Citation 2099 Unknown Reporter 999",
                standardized_citation="Bogus Citation 2099 Unknown Reporter 999",
                case_or_statute_title="Nonexistent Fabricated Case v. Ghost",
                source_type="Supreme Court",
                status=CitationVerificationStatus.HALLUCINATED,
                ratio_or_rule="Fake rule",
                relevant_excerpt="Fake excerpt"
            )
        ],
        synthesis="Fake text without grounding.",
        temporal_framework_analysis=""
    )

    report_fake = agent.audit_agent_outputs(research_result=fake_research)
    assert report_fake.is_approved is False
    assert len(report_fake.hallucinated_citations) > 0


def test_agent_8_report_generation():
    """Tests Agent 8 report compilation, PDF and DOCX file output."""
    agent = ReportGenerationAgent()
    doc_agent = DocumentIntelligenceAgent()
    sample_file = DOCS_DIR / "sample_employment_agreement.txt"
    doc = doc_agent.process_file(sample_file)

    report = agent.compile_report(
        report_title="Technova Solutions Analysis",
        workflow_name="document_analysis",
        document=doc
    )

    assert report.report_id.startswith("LEX_")
    assert report.pdf_path is not None
    assert Path(report.pdf_path).exists()
    assert report.docx_path is not None
    assert Path(report.docx_path).exists()
