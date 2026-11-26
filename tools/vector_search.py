"""Vector Search Tool for autonomous agents to query legal knowledge base."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from lexagent_ai.rag.retriever import LegalRetriever
from lexagent_ai.rag.knowledge_base import LegalKnowledgeBase


class VectorSearchTool:
    """Tool allowing agents to perform semantic search on legal knowledge base."""

    def __init__(self, knowledge_base: Optional[LegalKnowledgeBase] = None):
        self.retriever = LegalRetriever(knowledge_base)

    def search(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries the vector index for grounded statutes, precedents, or document chunks."""
        return self.retriever.retrieve(query=query, top_k=top_k, filter_doc_id=document_id)
