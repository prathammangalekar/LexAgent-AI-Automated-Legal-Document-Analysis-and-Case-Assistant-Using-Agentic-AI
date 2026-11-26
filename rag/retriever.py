"""Hybrid Semantic & Lexical Legal Retriever.

Combines vector cosine similarity with BM25-style keyword boosting for section numbers
and statutory names, preserving source citations, page numbers, and chunk provenance.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from lexagent_ai.rag.knowledge_base import LegalKnowledgeBase
from lexagent_ai.models.schemas import DocumentChunk


class LegalRetriever:
    """Retrieves relevant legal chunks grounded in statutes, precedents, and documents."""

    def __init__(self, knowledge_base: Optional[LegalKnowledgeBase] = None):
        self.kb = knowledge_base or LegalKnowledgeBase()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_doc_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves top-k most relevant legal chunks for a query.

        Args:
            query: The legal issue or fact query.
            top_k: Number of chunks to return.
            filter_doc_id: Optional filter to restrict search to a specific document.

        Returns:
            List of matching chunks with similarity score and metadata.
        """
        if not self.kb.chunks:
            return []

        query_vector = self.kb.embedder.embed_text(query)
        query_lower = query.lower()
        scored_results: List[Dict[str, Any]] = []

        # Check for explicit section references in query
        sec_match = re.search(r'\b(?:section|sec|article|art\.?)\s*(\d+[a-zA-Z]?(?:\(\d+\))?|[A-Za-z0-9\(\)]+)', query_lower)
        target_sec = sec_match.group(1).lower() if sec_match else None

        for idx, chunk in enumerate(self.kb.chunks):
            if filter_doc_id and chunk.document_id != filter_doc_id:
                continue

            # Base vector cosine similarity
            vector_sim = self.kb.embedder.cosine_similarity(query_vector, self.kb.vectors[idx])

            # Lexical boosting
            boost = 0.0
            chunk_text_lower = chunk.text.lower()
            chunk_heading_lower = chunk.section_heading.lower()

            if target_sec and (f"section {target_sec}" in chunk_heading_lower or f"sec {target_sec}" in chunk_text_lower):
                boost += 0.35

            # Keyword matching from metadata
            keywords = chunk.metadata.get("keywords", [])
            for kw in keywords:
                if kw.lower() in query_lower:
                    boost += 0.15

            # Significant tokens in title or heading
            for token in query_lower.split():
                if len(token) > 4:
                    if token in chunk_heading_lower:
                        boost += 0.08
                    elif token in chunk_text_lower:
                        boost += 0.03

            combined_score = min(1.0, vector_sim * 0.7 + boost)

            if combined_score > 0.15:
                scored_results.append({
                    "chunk": chunk,
                    "score": round(combined_score, 4),
                    "document_title": chunk.document_title,
                    "section_heading": chunk.section_heading,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "metadata": chunk.metadata
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
