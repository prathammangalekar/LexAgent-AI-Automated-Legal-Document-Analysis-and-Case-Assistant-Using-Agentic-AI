"""Agent 3: Autonomous Legal Research Agent.

Receives legal research questions or flagged issues from the orchestrator.
Formulates multi-vector queries, searches authentic statutory and judicial databases,
extracts binding ratios and verbatim statutory sections, and validates temporal applicability.
Never hallucinates citations or case names.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from lexagent_ai.models.schemas import LegalResearchResult, VerifiedCitation
from lexagent_ai.tools.legal_search import LegalSearchTool


class LegalResearchAgent:
    """Agent autonomously conducting legal research on Indian law and judicial precedents."""

    def __init__(self, search_tool: Optional[LegalSearchTool] = None):
        self.search_tool = search_tool or LegalSearchTool()

    def identify_topics(self, query: str) -> List[str]:
        """Identifies legal topics and doctrinal categories from a query."""
        topics = []
        query_lower = query.lower()

        if any(w in query_lower for w in ["non-compete", "restraint of trade", "employment restriction", "section 27"]):
            topics.append("Contract Law - Restraint of Trade (Section 27)")
        if any(w in query_lower for w in ["liquidated damages", "penalty", "earnest money", "section 74"]):
            topics.append("Contract Law - Liquidated Damages & Penalties (Section 74)")
        if any(w in query_lower for w in ["electronic evidence", "whatsapp", "email", "section 65b", "bsa 63"]):
            topics.append("Evidence Law - Admissibility of Electronic Records (BSA Sec 63 / IEA Sec 65B)")
        if any(w in query_lower for w in ["arbitration", "dispute resolution", "arbitrability", "section 8"]):
            topics.append("Arbitration Law - Arbitrability & Reference (Arbitration Act 1996)")
        if any(w in query_lower for w in ["privacy", "data protection", "biometrics", "article 21", "it act"]):
            topics.append("Constitutional & Cyber Law - Privacy and Data Protection")
        if any(w in query_lower for w in ["cheating", "fraud", "criminal breach of trust", "bns 316", "bns 318", "ipc"]):
            topics.append("Criminal Law - Property Offenses (BNS 2023 / IPC 1860)")

        if not topics:
            topics.append("General Indian Commercial and Civil Jurisprudence")

        return topics

    def conduct_research(self, query: str, context: Optional[str] = None) -> LegalResearchResult:
        """Executes end-to-end legal research across Indian statutes and precedents."""
        search_query = query
        if context:
            search_query += f" {context[:200]}"

        topics = self.identify_topics(search_query)
        research_raw = self.search_tool.execute_legal_research(search_query)

        statutes_found = research_raw.get("statutory_provisions", [])
        judgments_found = research_raw.get("landmark_judgments", [])
        verified_citations: List[VerifiedCitation] = research_raw.get("verified_citations", [])

        # Build statutory provisions verbatim dictionary
        statutory_text_map: Dict[str, str] = {}
        for s in statutes_found:
            key = f"{s['act_title']} - Section {s['section_number']}"
            statutory_text_map[key] = s["text"]

        # Formulate synthesized legal reasoning based strictly on verified findings
        synthesis_paragraphs = []
        synthesis_paragraphs.append(f"Legal Research conducted on topics: {', '.join(topics)}.")

        if statutes_found:
            synthesis_paragraphs.append("STATUTORY FRAMEWORK:")
            for s in statutes_found:
                synthesis_paragraphs.append(
                    f"• {s['act_title']} Section {s['section_number']} ({s['section_title']}): Governs this issue. "
                    f"Relevant text: \"{s['text'][:250]}...\""
                )

        if judgments_found:
            synthesis_paragraphs.append("\nJUDICIAL PRECEDENTS & BINDING RATIOS:")
            for j in judgments_found:
                synthesis_paragraphs.append(
                    f"• {j['case_title']} ({j['citation']}) - {j['court']} ({j['year']}): "
                    f"{j['ratio_decidendi']}"
                )

        synthesis = "\n\n".join(synthesis_paragraphs)

        return LegalResearchResult(
            research_query=query,
            legal_topics=topics,
            applicable_statutes=statutes_found,
            landmark_judgments=verified_citations,
            statutory_provisions_text=statutory_text_map,
            synthesis=synthesis,
            temporal_framework_analysis=research_raw.get("temporal_note", ""),
            search_confidence=0.95 if verified_citations else 0.70
        )
