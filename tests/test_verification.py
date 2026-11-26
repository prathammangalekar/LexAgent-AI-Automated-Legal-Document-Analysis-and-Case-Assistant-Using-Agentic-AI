"""Tests for Citation Verification, Temporal Law Transition, and Hallucination Detection."""

import pytest
from lexagent_ai.tools.citation_verifier import CitationVerifier
from lexagent_ai.models.schemas import CitationVerificationStatus


def test_authentic_citation_verification():
    """Tests verification of known landmark Supreme Court judgments."""
    verifier = CitationVerifier()

    # Percept D'Mark
    res1 = verifier.verify_case_citation("(2006) 4 SCC 227")
    assert res1["status"] == CitationVerificationStatus.VERIFIED
    assert "Percept" in res1["title"]

    # Kailash Nath Associates
    res2 = verifier.verify_case_citation("(2015) 4 SCC 136")
    assert res2["status"] == CitationVerificationStatus.VERIFIED
    assert "Kailash Nath" in res2["title"]

    # Arjun Panditrao Khotkar
    res3 = verifier.verify_case_citation("(2020) 7 SCC 1")
    assert res3["status"] == CitationVerificationStatus.VERIFIED
    assert "Arjun Panditrao" in res3["title"]


def test_hallucinated_citation_detection():
    """Tests that fictitious or non-existent citations are rejected."""
    verifier = CitationVerifier()
    res = verifier.verify_case_citation("Fake Case Citation Nonexistent 99999")

    assert res["status"] == CitationVerificationStatus.HALLUCINATED
    assert res["valid"] is False


def test_temporal_law_transition_detection():
    """Tests that criminal law changes taking effect on July 1, 2024 are strictly policed."""
    verifier = CitationVerifier()

    # Case occurring in August 2024 citing old IPC
    issues_post_reform = verifier.check_temporal_validity(
        text="The respondent committed fraud under Section 420 of the Indian Penal Code (IPC).",
        document_date="2024-08-15"
    )

    assert len(issues_post_reform) > 0
    assert any("BNS" in i.correction_guidance for i in issues_post_reform)

    # Case occurring in 2022 citing IPC (valid for that era)
    issues_pre_reform = verifier.check_temporal_validity(
        text="The complaint alleges criminal breach of trust under IPC 406.",
        document_date="2022-05-10"
    )
    assert len(issues_pre_reform) == 0


def test_full_agent_output_audit():
    """Tests comprehensive audit of text, citations, and ground sources."""
    verifier = CitationVerifier()
    report = verifier.evaluate_agent_outputs(
        analysis_text="The clause is void under Section 27 as established in Percept D'Mark v. Zaheer Khan.",
        research_citations=["(2006) 4 SCC 227"],
        grounding_sources=["Percept D'Mark", "Section 27"]
    )

    assert report.is_approved is True
    assert report.verified_citations_count == 1
    assert report.confidence_score >= 0.8
