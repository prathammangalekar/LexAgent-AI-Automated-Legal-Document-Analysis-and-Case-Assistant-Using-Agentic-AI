"""Central Orchestration State for LexAgent AI using LangGraph.

Maintains multi-agent shared state, structured outputs, iteration counters,
and execution audit trails across agent transitions.
"""

from __future__ import annotations

import time
from typing import TypedDict, List, Dict, Any, Optional
from lexagent_ai.models.schemas import (
    ExtractedDocument,
    DocumentAnalysisResult,
    LegalResearchResult,
    CaseComparisonReport,
    LegalReasoningResult,
    GeneratedDraft,
    VerificationReport,
    ComprehensiveLegalReport
)


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across LangGraph nodes."""

    # Task and Request Context
    case_id: str
    user_request: str
    workflow_type: str  # document_analysis, case_research, case_comparison, legal_drafting, complex_investigation
    input_file_path: Optional[str]
    secondary_file_path: Optional[str]

    # Agent Outputs
    extracted_document: Optional[ExtractedDocument]
    analysis_result: Optional[DocumentAnalysisResult]
    research_result: Optional[LegalResearchResult]
    reasoning_result: Optional[LegalReasoningResult]
    comparison_result: Optional[CaseComparisonReport]
    generated_draft: Optional[GeneratedDraft]
    verification_report: Optional[VerificationReport]
    comprehensive_report: Optional[ComprehensiveLegalReport]

    # Execution Management & Reflection Controls
    current_step: str
    iteration_count: int
    max_iterations: int
    requires_re_research: bool
    remediation_guidance: Optional[str]

    # Human-In-The-Loop Checkpoint
    human_approval_required: bool
    human_approved: bool

    # Execution History & Errors
    execution_history: List[Dict[str, Any]]
    errors: List[str]
