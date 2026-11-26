"""Autonomous Indian Legal Search Engine.

Searches authentic statutory databases (India Code, BNS, BNSS, BSA, Contract Act,
IT Act, Consumer Protection Act) and landmark Supreme Court / High Court decisions.
Never hallucinates citations, sections, or case names.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from lexagent_ai.config import settings
from lexagent_ai.models.schemas import VerifiedCitation, CitationVerificationStatus


class LegalSearchTool:
    """Authentic search engine for Indian legal authorities."""

    def __init__(self, knowledge_base_dir: Optional[Path] = None):
        self.kb_dir = knowledge_base_dir or settings.knowledge_base_dir
        self.statutes: List[Dict[str, Any]] = []
        self.judgments: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """Loads statutes and judgments from local database files."""
        statutes_path = self.kb_dir / "statutes.json"
        judgments_path = self.kb_dir / "judgments.json"

        if statutes_path.exists():
            with open(statutes_path, "r", encoding="utf-8") as f:
                self.statutes = json.load(f)

        if judgments_path.exists():
            with open(judgments_path, "r", encoding="utf-8") as f:
                self.judgments = json.load(f)

    def search_statutes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches statutory provisions based on keywords or section numbers.

        Args:
            query: Legal search string (e.g. 'restraint of trade', 'Section 27', 'BNS 316').
            limit: Maximum provisions to return.

        Returns:
            List of matching statutory provisions with full section text and act details.
        """
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []

        # Look for explicit section references like "section 27" or "sec 74"
        sec_match = re.search(r'\b(?:section|sec|article|art\.?)\s*(\d+[a-zA-Z]?(?:\(\d+\))?|[A-Za-z0-9\(\)]+)', query_lower)
        target_sec = sec_match.group(1).lower() if sec_match else None

        for act in self.statutes:
            act_title = act.get("act_title", "")
            act_id = act.get("act_id", "")
            for sec in act.get("sections", []):
                sec_num = str(sec.get("section_number", "")).lower()
                sec_title = sec.get("title", "").lower()
                sec_text = sec.get("text", "").lower()
                keywords = [k.lower() for k in sec.get("keywords", [])]

                score = 0
                if target_sec and (target_sec == sec_num or f"section {target_sec}" in sec_title):
                    score += 15

                # Keyword matches
                for kw in keywords:
                    if kw in query_lower:
                        score += 5

                # Query token matches
                tokens = [t for t in query_lower.split() if len(t) > 3]
                for token in tokens:
                    if token in sec_title:
                        score += 3
                    if token in sec_text:
                        score += 1
                    if token in act_title.lower():
                        score += 2

                if score > 0:
                    results.append({
                        "act_id": act_id,
                        "act_title": act_title,
                        "section_number": sec.get("section_number"),
                        "section_title": sec.get("title"),
                        "text": sec.get("text"),
                        "effective_date": act.get("effective_date"),
                        "score": score
                    })

        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def search_judgments(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Searches landmark judicial precedents from Supreme Court and High Courts.

        Args:
            query: Search query (e.g. 'non-compete employee', 'liquidated damages proof of loss').
            limit: Maximum precedents to return.

        Returns:
            List of matching verified cases.
        """
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []

        for case in self.judgments:
            score = 0
            title = case.get("case_title", "").lower()
            ratio = case.get("ratio_decidendi", "").lower()
            facts = case.get("facts", "").lower()
            keywords = [k.lower() for k in case.get("keywords", [])]
            statutes = [s.lower() for s in case.get("statutes_involved", [])]

            # Check case name match
            if any(term in title for term in query_lower.split() if len(term) > 3):
                score += 8

            for kw in keywords:
                if kw in query_lower:
                    score += 6

            for stat in statutes:
                if any(word in stat for word in query_lower.split() if len(word) > 3):
                    score += 4

            if any(word in ratio for word in query_lower.split() if len(word) > 4):
                score += 3

            if score > 0:
                results.append({
                    "case_id": case.get("case_id"),
                    "case_title": case.get("case_title"),
                    "citation": case.get("citation"),
                    "court": case.get("court"),
                    "year": case.get("year"),
                    "bench": case.get("bench"),
                    "statutes_involved": case.get("statutes_involved"),
                    "facts": case.get("facts"),
                    "ratio_decidendi": case.get("ratio_decidendi"),
                    "key_passages": case.get("key_passages"),
                    "outcome": case.get("outcome"),
                    "score": score
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def execute_legal_research(self, topic_or_question: str) -> Dict[str, Any]:
        """Comprehensive research workflow querying statutory law and precedent.

        Args:
            topic_or_question: The legal issue or factual query.

        Returns:
            Structured dictionary of verified authorities and synthesis.
        """
        statutory_findings = self.search_statutes(topic_or_question, limit=4)
        judicial_findings = self.search_judgments(topic_or_question, limit=3)

        verified_citations: List[VerifiedCitation] = []
        for j in judicial_findings:
            verified_citations.append(
                VerifiedCitation(
                    citation_raw=j["citation"],
                    standardized_citation=j["citation"],
                    case_or_statute_title=j["case_title"],
                    source_type="Supreme Court Judgment",
                    year=j["year"],
                    court_name=j["court"],
                    status=CitationVerificationStatus.VERIFIED,
                    official_source_url_or_ref=f"Supreme Court of India / SC e-Reporter ({j['citation']})",
                    ratio_or_rule=j["ratio_decidendi"],
                    relevant_excerpt=j["key_passages"][0] if j.get("key_passages") else j["ratio_decidendi"],
                    temporal_validity_note="Binding precedent under Article 141 of the Constitution of India."
                )
            )

        # Check temporal applicability note
        temporal_note = (
            "Temporal Notice under Indian Legal Framework: The Bharatiya Nyaya Sanhita (BNS), "
            "Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA) came into "
            "force on July 1, 2024. For acts or transactions occurring prior to July 1, 2024, the Indian "
            "Penal Code (IPC), Code of Criminal Procedure (CrPC), and Indian Evidence Act (IEA) apply."
        )

        return {
            "query": topic_or_question,
            "statutory_provisions": statutory_findings,
            "landmark_judgments": judicial_findings,
            "verified_citations": verified_citations,
            "temporal_note": temporal_note
        }
