"""Legal Knowledge Base indexing statutes, landmark judgments, and uploaded documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from lexagent_ai.config import settings
from lexagent_ai.models.schemas import DocumentChunk
from lexagent_ai.rag.embeddings import LegalEmbeddingModel


class LegalKnowledgeBase:
    """In-memory vector and metadata index for Indian legal authorities."""

    def __init__(self, kb_dir: Optional[Path] = None):
        self.kb_dir = kb_dir or settings.knowledge_base_dir
        self.embedder = LegalEmbeddingModel()
        self.chunks: List[DocumentChunk] = []
        self.vectors: List[List[float]] = []
        self.initialize_index()

    def initialize_index(self) -> None:
        """Loads statutory texts and landmark judgments into vector index."""
        statutes_path = self.kb_dir / "statutes.json"
        judgments_path = self.kb_dir / "judgments.json"

        # Index Statutes
        if statutes_path.exists():
            with open(statutes_path, "r", encoding="utf-8") as f:
                acts = json.load(f)
                for act in acts:
                    act_title = act.get("act_title", "")
                    act_id = act.get("act_id", "")
                    for sec in act.get("sections", []):
                        sec_num = sec.get("section_number")
                        sec_title = sec.get("title")
                        content = f"{act_title} - Section {sec_num}: {sec_title}\n\n{sec.get('text')}"
                        chunk = DocumentChunk(
                            chunk_id=f"{act_id}_sec_{sec_num}",
                            document_id=act_id,
                            document_title=act_title,
                            section_heading=f"Section {sec_num} ({sec_title})",
                            text=content,
                            page_number=1,
                            metadata={
                                "type": "statute",
                                "act_id": act_id,
                                "section": sec_num,
                                "keywords": sec.get("keywords", [])
                            }
                        )
                        self.add_chunk(chunk)

        # Index Landmark Judgments
        if judgments_path.exists():
            with open(judgments_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
                for c in cases:
                    case_id = c.get("case_id")
                    title = c.get("case_title")
                    citation = c.get("citation")
                    ratio = c.get("ratio_decidendi")
                    content = (
                        f"Landmark Judgment: {title} ({citation})\n"
                        f"Court: {c.get('court')} | Year: {c.get('year')}\n"
                        f"Statutes Involved: {', '.join(c.get('statutes_involved', []))}\n"
                        f"Ratio Decidendi: {ratio}\n"
                        f"Key Precedent Passages: {' '.join(c.get('key_passages', []))}"
                    )
                    chunk = DocumentChunk(
                        chunk_id=f"case_{case_id}",
                        document_id=case_id,
                        document_title=title,
                        section_heading=f"Judgment: {title}",
                        text=content,
                        page_number=1,
                        metadata={
                            "type": "judgment",
                            "citation": citation,
                            "court": c.get("court"),
                            "year": c.get("year"),
                            "keywords": c.get("keywords", [])
                        }
                    )
                    self.add_chunk(chunk)

    def add_chunk(self, chunk: DocumentChunk) -> None:
        """Adds a chunk and its normalized vector embedding to index."""
        self.chunks.append(chunk)
        vector = self.embedder.embed_text(chunk.text + " " + chunk.section_heading)
        self.vectors.append(vector)

    def add_document_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Indexes dynamic chunks from an uploaded user document."""
        for c in chunks:
            self.add_chunk(c)
