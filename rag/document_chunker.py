"""Legal Document Chunker.

Divides legal documents into coherent chunks respecting clause boundaries,
section titles, articles, and paragraph structures while preserving source metadata.
Includes strict prompt-injection shielding.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from lexagent_ai.models.schemas import DocumentChunk


class LegalDocumentChunker:
    """Specialized chunker for contracts, statutes, and court briefs."""

    CLAUSE_REGEX = re.compile(
        r'(?:^|\n\n)(?P<heading>(?:(?:Clause|Section|Article|Point)\s+[\dA-Za-z\.]+|[\dA-Za-z]+\.[\dA-Za-z\.]*|[A-Z\s]{4,}))[:\.\s]',
        re.MULTILINE
    )

    INJECTION_PATTERNS = [
        re.compile(r'ignore (?:all )?previous instructions', re.IGNORECASE),
        re.compile(r'system prompt override', re.IGNORECASE),
        re.compile(r'you are now in developer mode', re.IGNORECASE),
        re.compile(r'disregard earlier legal rules', re.IGNORECASE)
    ]

    def __init__(self, target_chunk_size: int = 600, overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def sanitize_text(self, text: str) -> str:
        """Shields the agent against prompt injection in untrusted documents."""
        sanitized = text
        for pat in self.INJECTION_PATTERNS:
            if pat.search(sanitized):
                sanitized = pat.sub("[SAFETY: UNTRUSTED PROMPT OVERRIDE ATTEMPT FILTERED]", sanitized)
        return sanitized

    def chunk_document(
        self,
        document_id: str,
        document_title: str,
        text: str,
        page_number: Optional[int] = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Splits text into legal chunks preserving clause headings and page numbers."""
        clean_text = self.sanitize_text(text)
        metadata = metadata or {}
        chunks: List[DocumentChunk] = []

        # Split along double linebreaks / paragraphs first
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

        current_heading = "Preamble / Recitals"
        current_buffer: List[str] = []
        current_len = 0
        chunk_idx = 1

        for p in paragraphs:
            # Check if this paragraph starts with a clause or section heading
            first_line = p.split("\n")[0].strip()
            is_heading = bool(re.match(r'^(?:Clause|Section|Article|Point|\d+\.|\d+\b)', first_line, re.IGNORECASE)) or (len(first_line) < 60 and first_line.isupper() and len(first_line) > 3)

            if is_heading:
                new_heading = first_line[:80]
                # If buffer already holds content, flush it as a complete clause chunk
                if current_buffer and (current_len >= self.target_chunk_size // 3 or len(current_buffer) >= 1):
                    chunk_text = "\n\n".join(current_buffer)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{document_id}_chunk_{chunk_idx}",
                            document_id=document_id,
                            document_title=document_title,
                            section_heading=current_heading,
                            text=chunk_text,
                            page_number=page_number,
                            metadata={**metadata, "word_count": len(chunk_text.split())}
                        )
                    )
                    chunk_idx += 1
                    current_buffer = []
                    current_len = 0
                current_heading = new_heading

            current_buffer.append(p)
            current_len += len(p)

            # Flush if exceeded chunk size
            if current_len >= self.target_chunk_size:
                chunk_text = "\n\n".join(current_buffer)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}_chunk_{chunk_idx}",
                        document_id=document_id,
                        document_title=document_title,
                        section_heading=current_heading,
                        text=chunk_text,
                        page_number=page_number,
                        metadata={**metadata, "word_count": len(chunk_text.split())}
                    )
                )
                chunk_idx += 1
                current_buffer = []
                current_len = 0

        # Flush final remainder
        if current_buffer:
            chunk_text = "\n\n".join(current_buffer)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{chunk_idx}",
                    document_id=document_id,
                    document_title=document_title,
                    section_heading=current_heading,
                    text=chunk_text,
                    page_number=page_number,
                    metadata={**metadata, "word_count": len(chunk_text.split())}
                )
            )

        return chunks
