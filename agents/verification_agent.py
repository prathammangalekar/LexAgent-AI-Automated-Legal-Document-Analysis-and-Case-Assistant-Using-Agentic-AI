"""Agent 7: Verification and Hallucination Detection Agent.

Quality-control layer for LexAgent AI.
Audits citations against Indian law reporters, verifies evidence grounding,
detects outdated statutory provisions (IPC vs BNS), identifies internal contradictions,
and mandates retry/re-research when confidence is insufficient.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from lexagent_ai.models.schemas import (
    VerificationReport,
    VerificationIssue,
    DocumentAnalysisResult,
    LegalResearchResult,
    LegalReasoningResult,
    GeneratedDraft
)
from lexagent_ai.tools.citation_verifier import CitationVerifier


class VerificationAgent:
    """Agent acting as the rigorous quality-control and anti-hallucination sentinel."""

    def __init__(self, verifier_tool: Optional[CitationVerifier] = None):
        self.verifier = verifier_tool or CitationVerifier()

    def audit_agent_outputs(
        self,
        analysis_result: Optional[DocumentAnalysisResult] = None,
        research_result: Optional[LegalResearchResult] = None,
        reasoning_result: Optional[LegalReasoningResult] = None,
        draft: Optional[GeneratedDraft] = None,
        document_date: Optional[str] = None
    ) -> VerificationReport:
        """Comprehensive verification of all generated legal materials."""
        citations_to_check: List[str] = []
        grounding_corpus: List[str] = []
        text_corpus: List[str] = []

        # Collect citations from research
        if research_result:
            for j in research_result.landmark_judgments:
                citations_to_check.append(j.standardized_citation)
                citations_to_check.append(j.case_or_statute_title)
                grounding_corpus.append(j.case_or_statute_title)
            for s in research_result.applicable_statutes:
                grounding_corpus.append(s["act_title"])
            text_corpus.append(research_result.synthesis)

        # Collect citations and text from reasoning
        if reasoning_result:
            for issue in reasoning_result.framed_issues:
                for rule in issue.governing_rules:
                    citations_to_check.append(rule)
                    grounding_corpus.append(rule)
                text_corpus.append(issue.irac_synthesis)

        # Collect citations and text from draft
        if draft:
            citations_to_check.extend(draft.statutory_grounds_cited)
            citations_to_check.extend(draft.precedents_referenced)
            text_corpus.append(draft.formal_body)

        # Collect analysis text
        if analysis_result:
            text_corpus.append(analysis_result.executive_summary)
            for c in analysis_result.analyzed_clauses:
                text_corpus.append(c.legal_interpretation)
                if c.applicable_statute:
                    grounding_corpus.append(c.applicable_statute)

        combined_text = "\n\n".join(text_corpus)
        unique_citations = list(set(citations_to_check))

        # Run verification engine
        report = self.verifier.evaluate_agent_outputs(
            analysis_text=combined_text,
            research_citations=unique_citations,
            grounding_sources=grounding_corpus,
            document_date=document_date
        )

        return report
