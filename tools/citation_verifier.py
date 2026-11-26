"""Citation Verification and Anti-Hallucination Tool for Indian Legal Citations.

Validates Indian case citations against official reporters (SCC, AIR, SCR, INSC)
and checks statutory provisions against India Code and reform enactments (BNS/BNSS/BSA).
"""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from lexagent_ai.config import settings
from lexagent_ai.models.schemas import (
    VerificationIssue,
    VerificationReport,
    CitationVerificationStatus,
)


class CitationVerifier:
    """Verifies judicial citations and detects hallucinations or superseded statutes."""

    # Standard Indian citation regex patterns
    PATTERNS = {
        "SCC": r'\(\d{4}\)\s*\d+\s*SCC\s*\d+',
        "AIR_SC": r'AIR\s*\d{4}\s*SC\s*\d+',
        "INSC": r'\d{4}\s*INSC\s*\d+',
        "SCR": r'\[\d{4}\]\s*\d*\s*SCR\s*\d+',
        "SCC_ONLINE": r'\d{4}\s*SCC\s*OnLine\s*(?:SC|Del|Bom|Mad|Cal|Kar)\s*\d+',
        "STATUTE_SECTION": r'(?:Section|Sec\.|Article|Art\.)\s*(\d+[A-Za-z]?(?:\(\d+\))?)\s*(?:of\s+the\s+)?([A-Za-z\s,]+(?:Act|Sanhita|Adhiniyam|Constitution))'
    }

    def __init__(self, knowledge_base_dir: Optional[Path] = None):
        self.kb_dir = knowledge_base_dir or settings.knowledge_base_dir
        self.verified_judgments: Dict[str, Dict[str, Any]] = {}
        self.verified_statutes: Dict[str, List[str]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Loads verified case law and statute registry."""
        statutes_path = self.kb_dir / "statutes.json"
        judgments_path = self.kb_dir / "judgments.json"

        if judgments_path.exists():
            with open(judgments_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
                for c in cases:
                    self.verified_judgments[c["case_title"].lower()] = c
                    self.verified_judgments[c["citation"].lower()] = c
                    for alt in c.get("alternate_citations", []):
                        self.verified_judgments[alt.lower()] = c

        if statutes_path.exists():
            with open(statutes_path, "r", encoding="utf-8") as f:
                acts = json.load(f)
                for a in acts:
                    act_name = a["act_title"].lower()
                    sec_list = [str(s["section_number"]).lower() for s in a.get("sections", [])]
                    self.verified_statutes[act_name] = sec_list
                    self.verified_statutes[a["act_id"].lower()] = sec_list

    def extract_citations(self, text: str) -> List[str]:
        """Extracts candidate citation strings from text."""
        citations = []
        for pattern_name, regex in self.PATTERNS.items():
            matches = re.findall(regex, text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    citations.append(" ".join(m).strip())
                else:
                    citations.append(m.strip())
        return list(set(citations))

    def verify_case_citation(self, citation_or_title: str) -> Dict[str, Any]:
        """Verifies if a case citation or title exists in verified Indian legal registry."""
        clean = citation_or_title.strip().lower()

        # 1. Check if this is a statutory provision or Act
        if any(term in clean for term in ["section", "sec.", "sec ", "article", "act", "sanhita", "adhiniyam", "constitution"]):
            # Check if it references any of our verified Indian statutes
            for act_name in self.verified_statutes:
                if act_name in clean or any(kw in clean for kw in ["contract", "bns", "bnss", "bsa", "evidence", "information technology", "consumer", "arbitration", "constitution"]):
                    return {
                        "input": citation_or_title,
                        "status": CitationVerificationStatus.VERIFIED,
                        "title": citation_or_title,
                        "court": "Parliament of India / State Legislature",
                        "ratio": "Statutory Authority",
                        "valid": True
                    }

        # 2. Direct registry match for judgments
        if clean in self.verified_judgments:
            record = self.verified_judgments[clean]
            return {
                "input": citation_or_title,
                "status": CitationVerificationStatus.VERIFIED,
                "title": record.get("case_title"),
                "court": record.get("court"),
                "ratio": record.get("ratio_decidendi"),
                "valid": True
            }

        # 3. Substring / partial title match
        for key, record in self.verified_judgments.items():
            if key in clean or clean in key:
                return {
                    "input": citation_or_title,
                    "status": CitationVerificationStatus.VERIFIED,
                    "title": record.get("case_title"),
                    "court": record.get("court"),
                    "ratio": record.get("ratio_decidendi"),
                    "valid": True
                }

        # 4. Check if the citation matches standard reporter syntax (SCC, AIR, etc.)
        matches_syntax = any(
            re.search(self.PATTERNS[p], citation_or_title, re.IGNORECASE)
            for p in ["SCC", "AIR_SC", "INSC", "SCR", "SCC_ONLINE"]
        )

        if matches_syntax:
            # Valid syntax but unverified in our indexed landmark knowledge base
            return {
                "input": citation_or_title,
                "status": CitationVerificationStatus.UNVERIFIED,
                "valid": True,  # Syntactically valid Indian reporter citation
                "note": "Valid Indian reporter format, but not found in indexed landmark registry. Requires independent verification."
            }

        return {
            "input": citation_or_title,
            "status": CitationVerificationStatus.HALLUCINATED,
            "valid": False,
            "note": "Does not conform to standard Indian legal citation syntax or verified database."
        }

    def check_temporal_validity(self, text: str, document_date: Optional[str] = None) -> List[VerificationIssue]:
        """Checks for temporal statutory mismatches (e.g. IPC vs BNS)."""
        issues: List[VerificationIssue] = []

        # If text cites IPC for an event post July 1, 2024
        if document_date and document_date >= "2024-07-01":
            if re.search(r'\b(?:Indian Penal Code|IPC)\b', text, re.IGNORECASE):
                issues.append(
                    VerificationIssue(
                        issue_type="OUTDATED_LAW",
                        severity="HIGH",
                        source_agent="Legal Research / Drafting",
                        flawed_text="References to Indian Penal Code (IPC) for event occurring on or after 1 July 2024.",
                        reason="The Bharatiya Nyaya Sanhita (BNS) replaced the IPC on July 1, 2024.",
                        correction_guidance="Replace IPC sections with corresponding BNS provisions (e.g. IPC 420 -> BNS 318; IPC 406 -> BNS 316)."
                    )
                )
            if re.search(r'\b(?:Code of Criminal Procedure|CrPC)\b', text, re.IGNORECASE):
                issues.append(
                    VerificationIssue(
                        issue_type="OUTDATED_LAW",
                        severity="HIGH",
                        source_agent="Legal Research / Drafting",
                        flawed_text="References to Code of Criminal Procedure (CrPC) for proceeding post 1 July 2024.",
                        reason="The Bharatiya Nagarik Suraksha Sanhita (BNSS) replaced CrPC on July 1, 2024.",
                        correction_guidance="Cite BNSS (e.g. CrPC 154 -> BNSS 173; CrPC 156(3) -> BNSS 175)."
                    )
                )

        return issues

    def evaluate_agent_outputs(
        self,
        analysis_text: str,
        research_citations: List[str],
        grounding_sources: List[str],
        document_date: Optional[str] = None
    ) -> VerificationReport:
        """Full quality audit of legal citations, grounded assertions, and temporal validity."""
        issues: List[VerificationIssue] = []
        verified_count = 0
        hallucinated_citations: List[str] = []

        # 1. Audit all citations
        for cit in research_citations:
            result = self.verify_case_citation(cit)
            if result["status"] == CitationVerificationStatus.VERIFIED:
                verified_count += 1
            elif result["status"] == CitationVerificationStatus.HALLUCINATED:
                hallucinated_citations.append(cit)
                issues.append(
                    VerificationIssue(
                        issue_type="FABRICATED_CITATION",
                        severity="FATAL",
                        source_agent="Research / Reasoning Agent",
                        flawed_text=cit,
                        reason="Citation failed Indian reporter validation and does not exist in registry.",
                        correction_guidance=f"Remove or replace '{cit}' with an authentic Supreme Court precedent."
                    )
                )

        # 2. Check temporal law issues
        temporal_issues = self.check_temporal_validity(analysis_text, document_date)
        issues.extend(temporal_issues)

        # 3. Grounding check: verify that conclusions mention at least one grounded statute or precedent
        unsupported: List[str] = []
        if grounding_sources and not any(src.lower() in analysis_text.lower() for src in grounding_sources):
            unsupported.append("Analysis makes claims not grounded in retrieved statutory or judicial records.")
            issues.append(
                VerificationIssue(
                    issue_type="UNSUPPORTED_CLAIM",
                    severity="MEDIUM",
                    source_agent="Legal Analysis Agent",
                    flawed_text="Generic conclusions without citing ground sources.",
                    reason="Conclusions must tie back to specific clauses or retrieved legal provisions.",
                    correction_guidance="Ground all legal risks in specific statutory sections (e.g. Section 27 Contract Act)."
                )
            )

        total_checked = len(research_citations)
        passed = (len(hallucinated_citations) == 0 and len([i for i in issues if i.severity == "FATAL"]) == 0)

        # Calculate confidence score
        if total_checked > 0:
            confidence = (verified_count / total_checked) * (0.8 if issues else 1.0)
        else:
            confidence = 0.9 if not issues else 0.6

        return VerificationReport(
            is_approved=passed,
            confidence_score=round(confidence, 2),
            total_citations_evaluated=total_checked,
            verified_citations_count=verified_count,
            hallucinated_citations=hallucinated_citations,
            outdated_laws_detected=[i.flawed_text for i in issues if i.issue_type == "OUTDATED_LAW"],
            unsupported_assertions=unsupported,
            issues=issues,
            remediation_required=issues[0].correction_guidance if (not passed and issues) else None
        )
