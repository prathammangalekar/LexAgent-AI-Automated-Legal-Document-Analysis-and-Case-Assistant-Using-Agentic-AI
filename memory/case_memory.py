"""Case Memory Management for LexAgent AI.

Maintains multi-turn context, previous legal research, extracted documents,
and agent observations isolated per case and client.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lexagent_ai.models.schemas import ExtractedDocument, LegalResearchResult, DocumentAnalysisResult


class CaseContextEntry(BaseModel):
    """An individual event, query, or finding recorded in case history."""
    timestamp: float = Field(default_factory=time.time)
    source_agent: str
    entry_type: str = Field(..., description="USER_QUERY, EXTRACTED_DOC, RESEARCH_FINDING, REASONING, DRAFT, CLARIFICATION")
    content: Dict[str, Any]


class CaseMemoryStore:
    """Isolates and manages state and memories across distinct legal cases."""

    def __init__(self):
        # Case ID -> list of context entries
        self._cases: Dict[str, List[CaseContextEntry]] = {}
        # Case ID -> Extracted documents
        self._case_documents: Dict[str, Dict[str, ExtractedDocument]] = {}
        # Case ID -> Saved research results
        self._case_research: Dict[str, List[LegalResearchResult]] = {}
        # Case ID -> Key verified facts
        self._case_facts: Dict[str, List[str]] = {}

    def get_or_create_case(self, case_id: str) -> str:
        """Initializes storage for a new case if not present."""
        if case_id not in self._cases:
            self._cases[case_id] = []
            self._case_documents[case_id] = {}
            self._case_research[case_id] = []
            self._case_facts[case_id] = []
        return case_id

    def record_entry(self, case_id: str, source_agent: str, entry_type: str, content: Dict[str, Any]) -> None:
        """Appends an event to the case audit trail."""
        self.get_or_create_case(case_id)
        entry = CaseContextEntry(source_agent=source_agent, entry_type=entry_type, content=content)
        self._cases[case_id].append(entry)

    def store_document(self, case_id: str, document: ExtractedDocument) -> None:
        """Stores an extracted document within the case context."""
        self.get_or_create_case(case_id)
        self._case_documents[case_id][document.document_id] = document
        self.record_entry(
            case_id,
            source_agent="DocumentIntelligenceAgent",
            entry_type="EXTRACTED_DOC",
            content={"document_id": document.document_id, "title": document.title, "pages": document.total_pages}
        )

    def get_document(self, case_id: str, document_id: str) -> Optional[ExtractedDocument]:
        """Retrieves an extracted document for a specific case."""
        return self._case_documents.get(case_id, {}).get(document_id)

    def store_research(self, case_id: str, research: LegalResearchResult) -> None:
        """Persists research results for subsequent query deduplication and retrieval."""
        self.get_or_create_case(case_id)
        self._case_research[case_id].append(research)
        self.record_entry(
            case_id,
            source_agent="AutonomousResearchAgent",
            entry_type="RESEARCH_FINDING",
            content={"query": research.research_query, "topics": research.legal_topics}
        )

    def get_all_research(self, case_id: str) -> List[LegalResearchResult]:
        """Gets all previous legal research conducted under this case."""
        return self._case_research.get(case_id, [])

    def add_facts(self, case_id: str, facts: List[str]) -> None:
        """Records ascertained facts."""
        self.get_or_create_case(case_id)
        self._case_facts[case_id].extend(facts)

    def get_facts(self, case_id: str) -> List[str]:
        """Retrieves all ascertained facts for the case."""
        return self._case_facts.get(case_id, [])

    def get_timeline(self, case_id: str) -> List[CaseContextEntry]:
        """Retrieves chronological audit trail for the case."""
        return self._cases.get(case_id, [])

    def clear_case(self, case_id: str) -> None:
        """Wipes context for a case to guarantee privacy/isolation."""
        self._cases.pop(case_id, None)
        self._case_documents.pop(case_id, None)
        self._case_research.pop(case_id, None)
        self._case_facts.pop(case_id, None)


# Global singleton case memory
global_case_memory = CaseMemoryStore()
