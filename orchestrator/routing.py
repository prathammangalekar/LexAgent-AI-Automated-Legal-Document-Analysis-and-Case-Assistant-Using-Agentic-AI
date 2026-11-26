"""Conditional routing and dynamic decision paths for LangGraph multi-agent flow."""

from __future__ import annotations

import re
from typing import Literal
from lexagent_ai.orchestrator.state import AgentState


def determine_workflow_type(request: str, file_path: str | None = None) -> str:
    """Classifies user intent into one of five core autonomous legal workflows."""
    req_lower = request.lower()

    if any(k in req_lower for k in ["compare", "contrast", "distinction between", "precedent comparison"]):
        return "case_comparison"
    elif any(k in req_lower for k in ["draft", "notice", "reply", "prepare agreement", "memorandum", "complaint"]):
        return "legal_drafting"
    elif any(k in req_lower for k in ["research", "what does the law say", "applicable sections", "find judgments", "statutory position"]):
        return "case_research"
    elif any(k in req_lower for k in ["investigate", "complex case", "in-depth investigation", "full case assessment"]):
        return "complex_investigation"
    elif file_path or any(k in req_lower for k in ["analyze", "review", "risk", "clause", "agreement", "contract"]):
        return "document_analysis"

    return "document_analysis"


def route_initial_step(state: AgentState) -> Literal["document_intelligence", "autonomous_research", "case_comparison", "legal_drafting"]:
    """Routes from task planning to the initial agent based on selected workflow."""
    wf = state.get("workflow_type", "document_analysis")

    if wf == "case_research":
        return "autonomous_research"
    elif wf == "case_comparison":
        return "case_comparison"
    elif wf == "legal_drafting" and not state.get("input_file_path"):
        return "legal_drafting"
    else:
        # Document Analysis or Complex Investigation start with Document Intelligence
        return "document_intelligence"


def route_verification_gate(state: AgentState) -> Literal["report_generation", "autonomous_research"]:
    """Quality control gate: Checks verification report.

    If verification fails with severe hallucination or outdated laws and
    iteration count < max_iterations, routes back to research agent with
    remediation guidance (reflection and self-correction loop).
    Otherwise proceeds to report generation.
    """
    v_report = state.get("verification_report")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    if v_report and not v_report.is_approved and iteration < max_iter:
        state["requires_re_research"] = True
        state["remediation_guidance"] = v_report.remediation_required or "Ground all conclusions in verified authorities."
        return "autonomous_research"

    return "report_generation"
