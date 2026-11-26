"""Agent 1: Legal Document Intelligence Agent.

Accepts PDF, DOCX, and TXT legal documents.
Extracts text, metadata, parties, dates, amounts, governing law, and clauses.
Executes OCR if a scanned document is detected.
Partitions text into structured semantic chunks for RAG indexing.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from lexagent_ai.models.schemas import (
    DocumentCategory,
    ExtractedParty,
    ExtractedClause,
    ExtractedEntity,
    ExtractedDocument,
    DocumentChunk
)
from lexagent_ai.tools.pdf_reader import PDFReader
from lexagent_ai.tools.docx_reader import DocxReader
from lexagent_ai.tools.ocr_tool import OCRTool
from lexagent_ai.rag.document_chunker import LegalDocumentChunker


class DocumentIntelligenceAgent:
    """Agent responsible for understanding and ingesting raw legal instruments."""

    CATEGORY_INDICATORS = {
        DocumentCategory.EMPLOYMENT_AGREEMENT: ["employment agreement", "contract of employment", "service agreement", "appointment letter"],
        DocumentCategory.NON_DISCLOSURE_AGREEMENT: ["non-disclosure", "confidentiality agreement", "nda"],
        DocumentCategory.LEASE_LICENSE_DEED: ["lease deed", "leave and license", "tenancy agreement", "lessor", "lessee"],
        DocumentCategory.COURT_ORDER_JUDGMENT: ["in the supreme court", "in the high court", "writ petition", "appeal civil", "judgment", "coram:"],
        DocumentCategory.LEGAL_NOTICE: ["legal notice", "statutory notice", "under instructions from my client", "demand notice", "without prejudice"],
        DocumentCategory.NOTICE_REPLY: ["reply to legal notice", "rejoinder", "response to demand"],
        DocumentCategory.WRIT_PETITION_PLAINT: ["plaint under order", "writ petition under article", "petition under section", "petitioner", "respondent"],
        DocumentCategory.CONTRACT_AGREEMENT: ["master services agreement", "agreement", "memorandum of understanding", "mou", "terms of service"]
    }

    def __init__(self):
        self.chunker = LegalDocumentChunker()

    def detect_category(self, text: str) -> DocumentCategory:
        """Classifies document into a standardized legal category."""
        text_lower = text[:2500].lower()
        for cat, indicators in self.CATEGORY_INDICATORS.items():
            if any(ind in text_lower for ind in indicators):
                return cat
        return DocumentCategory.CONTRACT_AGREEMENT if "agreement" in text_lower else DocumentCategory.UNKNOWN

    def extract_parties(self, text: str) -> List[ExtractedParty]:
        """Extracts contracting or litigating parties from text."""
        parties: List[ExtractedParty] = []

        # 1. Check for standard agreement party recitals: lines following "between:" or "by and between:"
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines[:30]):
            if "between" in line.lower():
                # Traverse following lines for party corporate or individual names
                for next_line in lines[i+1:i+10]:
                    if next_line.upper().startswith("AND") or next_line.lower().startswith("whereas"):
                        continue
                    clean_name = re.split(r'\,|\(hereinafter|\-|\(the', next_line, flags=re.IGNORECASE)[0].strip()
                    if len(clean_name) > 3 and not any(clean_name.lower().startswith(w) for w in ["now", "therefore", "in witness", "whereas"]):
                        role = "Employer / First Party" if len(parties) == 0 else "Employee / Second Party"
                        parties.append(ExtractedParty(name=clean_name, role=role))
                        if len(parties) == 2:
                            break
                break

        # 2. Fallback for litigation documents: "Petitioner: X ... Respondent: Y" or "v." / "vs"
        if not parties:
            pet_match = re.search(r'(?:Petitioner|Appellant|Plaintiff)[:\s]+([A-Za-z0-9\s\.\,\(\)\-]+?)(?:\n|vs|\.\.\.)', text, re.IGNORECASE)
            resp_match = re.search(r'(?:Respondent|Defendant)[:\s]+([A-Za-z0-9\s\.\,\(\)\-]+?)(?:\n|\.\.\.)', text, re.IGNORECASE)
            if pet_match:
                parties.append(ExtractedParty(name=pet_match.group(1).strip(), role="Petitioner / Appellant"))
            if resp_match:
                parties.append(ExtractedParty(name=resp_match.group(1).strip(), role="Respondent / Defendant"))

        # 3. Check for "CASE REFERENCE: X v. Y"
        if not parties:
            case_ref_match = re.search(r'(?:CASE REFERENCE|REFERENCE)[:\s]+([A-Za-z0-9\s\.\,\(\)\-]+?)\s+(?:v\.|vs)\s+([A-Za-z0-9\s\.\,\(\)\-]+?)(?:\n|$)', text, re.IGNORECASE)
            if case_ref_match:
                parties.append(ExtractedParty(name=case_ref_match.group(1).strip(), role="Claimant / First Party"))
                parties.append(ExtractedParty(name=case_ref_match.group(2).strip(), role="Respondent / Second Party"))

        return parties

    def extract_clauses(self, text: str) -> List[ExtractedClause]:
        """Extracts individual clauses, articles, and numbered provisions."""
        clauses: List[ExtractedClause] = []

        # Regex matching patterns like "1. APPOINTMENT", "Clause 8. NON-COMPETE", "8.1 ...", "Section 9"
        clause_pattern = re.compile(
            r'(?:^|\n\n)(?P<num>(?:Clause\s+)?\d+(?:\.\d+)*)\.?\s+(?P<heading>[A-Z0-9\s\-_/,\(\)]+)\n(?P<body>(?:(?!\n\n(?:\d+\.|\bClause\b)).)+)',
            re.MULTILINE | re.DOTALL
        )

        matches = list(clause_pattern.finditer(text))
        for m in matches:
            num = m.group("num").strip()
            heading = m.group("heading").strip()
            body = m.group("body").strip()
            if len(body) > 20 and len(heading) < 80:
                clauses.append(
                    ExtractedClause(
                        clause_id=f"Clause {num}",
                        heading=heading,
                        text=f"{num}. {heading}\n{body}",
                        character_span=(m.start(), m.end())
                    )
                )

        # Fallback if strict clause structure is absent: partition by standard paragraph blocks
        if not clauses:
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
            for i, p in enumerate(paragraphs[:15]):
                first_line = p.split("\n")[0][:50]
                clauses.append(
                    ExtractedClause(
                        clause_id=f"Section {i+1}",
                        heading=first_line,
                        text=p
                    )
                )

        return clauses

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extracts monetary amounts, dates, and statutory references."""
        entities: List[ExtractedEntity] = []

        # Monetary amounts (INR, Rs, Lakhs, Crores)
        amt_matches = re.finditer(r'(?:INR|Rs\.?|Rupees)\s*[\d,]+(?:\s*(?:Lakhs?|Crores?))?(?:\s*\([A-Za-z\s\-]+\))?', text, re.IGNORECASE)
        for m in amt_matches:
            entities.append(ExtractedEntity(entity_type="AMOUNT", text=m.group(0).strip()))

        # Dates (e.g. 15th January 2024, 2024-07-01, 10/08/2023)
        date_matches = re.finditer(r'\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}-\d{2}-\d{2})\b', text, re.IGNORECASE)
        for m in date_matches:
            entities.append(ExtractedEntity(entity_type="DATE", text=m.group(0).strip()))

        # Statutes & Section references
        statute_matches = re.finditer(r'(?:Section|Sec\.|Article)\s*\d+[A-Za-z\(\)]*(?:\s+of\s+[A-Za-z\s]+(?:Act|Sanhita|Adhiniyam|Constitution))?', text, re.IGNORECASE)
        for m in statute_matches:
            entities.append(ExtractedEntity(entity_type="STATUTE", text=m.group(0).strip()))

        return entities

    def process_file(self, file_path: str | Path) -> ExtractedDocument:
        """Processes raw file (PDF, DOCX, TXT) into an ExtractedDocument."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Legal document not found: {file_path}")

        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        file_name = path.name
        suffix = path.suffix.lower()
        warnings: List[str] = []

        raw_text = ""
        total_pages = 1
        metadata = {}

        if suffix == ".pdf":
            pdf_data = PDFReader.extract_text_with_metadata(path)
            raw_text = pdf_data["full_text"]
            total_pages = pdf_data["total_pages"]
            metadata = pdf_data["metadata"]

            if pdf_data["ocr_required"] or len(raw_text.strip()) < 100:
                warnings.append("Document appears to be scanned; triggering OCR.")
                ocr_result = OCRTool.extract_from_image_or_pdf(path)
                if ocr_result.get("text"):
                    raw_text = ocr_result["text"]

        elif suffix in [".docx", ".doc"]:
            docx_data = DocxReader.extract_text_with_metadata(path)
            raw_text = docx_data["full_text"]
            metadata = docx_data["metadata"]

        else:
            # Plain text or other text encodings
            raw_text = path.read_text(encoding="utf-8", errors="replace")

        # Determine category & title
        category = self.detect_category(raw_text)
        first_line = raw_text.strip().split("\n")[0][:80]
        title = first_line if len(first_line) > 5 else f"Legal Document ({file_name})"

        # Extract structured elements
        parties = self.extract_parties(raw_text)
        clauses = self.extract_clauses(raw_text)
        entities = self.extract_entities(raw_text)

        # Extract governing law and jurisdiction
        gov_match = re.search(r'governed by (?:and construed in accordance with )?(?:the )?laws of ([A-Za-z\s]+)', raw_text, re.IGNORECASE)
        governing_law = gov_match.group(1).strip() if gov_match else "Laws of India (Presumed)"

        juris_match = re.search(r'courts (?:at|in)\s+([A-Za-z\s\,]+?)\s+shall have (?:exclusive )?jurisdiction', raw_text, re.IGNORECASE)
        jurisdiction = juris_match.group(1).strip() if juris_match else None

        arb_match = re.search(r'(?:arbitration|arbitral)\s+(?:seated in|held at|administered by)\s+([A-Za-z0-9\s\,\(\)]+)', raw_text, re.IGNORECASE)
        dispute_res = arb_match.group(0).strip() if arb_match else ("Arbitration" if "arbitrat" in raw_text.lower() else "Court Litigation")

        # Create semantic chunks
        chunks = self.chunker.chunk_document(
            document_id=doc_id,
            document_title=title,
            text=raw_text,
            metadata={"category": category.value, "file_name": file_name}
        )

        return ExtractedDocument(
            document_id=doc_id,
            file_name=file_name,
            category=category,
            title=title,
            parties=parties,
            effective_date=entities[0].text if entities and entities[0].entity_type == "DATE" else None,
            governing_law=governing_law,
            jurisdiction_clause=jurisdiction,
            dispute_resolution=dispute_res,
            clauses=clauses,
            key_entities=entities,
            total_pages=total_pages,
            word_count=len(raw_text.split()),
            full_text=raw_text,
            chunks=chunks,
            extraction_warnings=warnings
        )
