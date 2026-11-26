"""Workflow execution controllers for LexAgent AI.

Provides specialized entry points for the 5 Autonomous Workflows:
- Workflow A: Legal Document Analysis
- Workflow B: Case Research
- Workflow C: Case Comparison
- Workflow D: Legal Draft Generation
- Workflow E: Complex Case Investigation
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from lexagent_ai.orchestrator.graph import lexagent_orchestrator
from lexagent_ai.orchestrator.state import AgentState
from lexagent_ai.models.schemas import ComprehensiveLegalReport


class LexAgentWorkflowEngine:
    """Executes multi-agent legal workflows via the central LangGraph orchestrator."""

    def __init__(self):
        self.orchestrator = lexagent_orchestrator

    def execute_workflow_a_document_analysis(self, file_path: str | Path) -> ComprehensiveLegalReport:
        """Workflow A: Legal Document Analysis.

        1. Upload document.
        2. Extract clauses, parties, entities.
        3. Analyze risks and ambiguities.
        4. Research statutory provisions and judicial precedents.
        5. Reason through IRAC issues.
        6. Verify all citations and temporal validity.
        7. Compile and export Comprehensive Legal Report (PDF/DOCX).
        """
        initial_state: AgentState = {
            "case_id": f"CASE_DOC_{uuid.uuid4().hex[:6].upper()}",
            "user_request": "Analyze this legal agreement, evaluate risk provisions under Indian law, and compile a formal analysis.",
            "workflow_type": "document_analysis",
            "input_file_path": str(file_path),
            "iteration_count": 0,
            "max_iterations": 2,
            "execution_history": [],
            "errors": []
        }

        final_state = self.orchestrator.invoke(initial_state)
        return final_state["comprehensive_report"]

    def execute_workflow_b_case_research(self, legal_question: str) -> ComprehensiveLegalReport:
        """Workflow B: Autonomous Case Research.

        1. Accept legal question.
        2. Formulate targeted research queries.
        3. Retrieve applicable Indian legislation & Supreme Court judgments.
        4. Extract relevant judgment paragraphs and statutory sections.
        5. Verify citations against official reporter registers.
        6. Produce structured research report.
        """
        initial_state: AgentState = {
            "case_id": f"CASE_RES_{uuid.uuid4().hex[:6].upper()}",
            "user_request": legal_question,
            "workflow_type": "case_research",
            "input_file_path": None,
            "iteration_count": 0,
            "max_iterations": 2,
            "execution_history": [],
            "errors": []
        }

        final_state = self.orchestrator.invoke(initial_state)
        return final_state["comprehensive_report"]

    def execute_workflow_c_case_comparison(
        self,
        case_file_1: str | Path,
        case_file_2: Optional[str | Path] = None
    ) -> ComprehensiveLegalReport:
        """Workflow C: Case Comparison.

        1. Accept case documents / dispute brief.
        2. Extract core facts and issues.
        3. Compare with benchmark precedents and comparator cases.
        4. Contrast judicial reasoning and statutory concurrence.
        5. Generate structured comparison report.
        """
        initial_state: AgentState = {
            "case_id": f"CASE_CMP_{uuid.uuid4().hex[:6].upper()}",
            "user_request": "Compare the dispute against applicable Indian landmark precedents and evaluate factual convergences.",
            "workflow_type": "case_comparison",
            "input_file_path": str(case_file_1),
            "secondary_file_path": str(case_file_2) if case_file_2 else None,
            "iteration_count": 0,
            "max_iterations": 2,
            "execution_history": [],
            "errors": []
        }

        final_state = self.orchestrator.invoke(initial_state)
        return final_state["comprehensive_report"]

    def execute_workflow_d_legal_drafting(
        self,
        draft_instructions: str,
        supporting_file: Optional[str | Path] = None
    ) -> ComprehensiveLegalReport:
        """Workflow D: Legal Draft Generation.

        1. Collect user-provided facts and drafting intent.
        2. Research required legal provisions and grounds.
        3. Generate formal Indian legal notice or reply.
        4. Verify citations and statutory validity.
        5. Pass through human review checkpoint.
        6. Export draft in PDF and DOCX formats.
        """
        initial_state: AgentState = {
            "case_id": f"CASE_DFT_{uuid.uuid4().hex[:6].upper()}",
            "user_request": draft_instructions,
            "workflow_type": "legal_drafting",
            "input_file_path": str(supporting_file) if supporting_file else None,
            "iteration_count": 0,
            "max_iterations": 2,
            "execution_history": [],
            "errors": []
        }

        final_state = self.orchestrator.invoke(initial_state)
        return final_state["comprehensive_report"]

    def execute_workflow_e_complex_investigation(self, file_path: str | Path) -> ComprehensiveLegalReport:
        """Workflow E: Complex Case Investigation.

        1. Ingest complex case brief.
        2. Dissect into sub-issues across document intelligence, analysis, and research.
        3. Perform IRAC reasoning and evidentiary gap appraisal.
        4. Execute comparative precedent mapping.
        5. Formulate advocate action checklist and litigation strategy.
        6. Run verification audit and export final dossier.
        """
        initial_state: AgentState = {
            "case_id": f"CASE_INV_{uuid.uuid4().hex[:6].upper()}",
            "user_request": "Execute a full multi-agent case investigation, identifying evidentiary vulnerabilities and statutory arguments.",
            "workflow_type": "complex_investigation",
            "input_file_path": str(file_path),
            "iteration_count": 0,
            "max_iterations": 2,
            "execution_history": [],
            "errors": []
        }

        final_state = self.orchestrator.invoke(initial_state)
        return final_state["comprehensive_report"]
