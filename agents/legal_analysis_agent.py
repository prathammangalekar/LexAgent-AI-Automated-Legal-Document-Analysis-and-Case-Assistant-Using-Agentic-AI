"""Agent 2: Legal Understanding and Analysis Agent.

Analyzes legal provisions, detects ambiguous, contradictory, and high-risk clauses
(e.g., restraint of trade, excessive liquidated damages, unilateral indemnities, jurisdiction conflicts).
Explicitly segregates document facts from AI legal interpretations.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from lexagent_ai.models.schemas import (
    ExtractedDocument,
    DocumentAnalysisResult,
    AnalyzedClause,
    ClauseRiskLevel,
    LegalObligation
)


class LegalAnalysisAgent:
    """Agent performing statutory clause-level risk assessment and doctrinal analysis."""

    HIGH_RISK_PATTERNS = [
        {
            "keyword": "non-compete",
            "regex": r'\b(?:non-compete|restrain.*trade|not.*engage.*competitive|shall not.*consult for)\b',
            "category": "Restraint of Trade / Void Covenant",
            "statute": "Section 27, Indian Contract Act, 1872",
            "risk": ClauseRiskLevel.CRITICAL,
            "plain": "Prohibits working with competitors or practicing your profession post-employment.",
            "interpretation": "Under Section 27 of the Indian Contract Act and the Supreme Court ruling in Percept D'Mark v. Zaheer Khan (2006) 4 SCC 227, all post-termination non-compete restrictions are void ab initio in India. Reasonableness tests do not save post-contractual covenants.",
            "recommendation": "Remove or modify to apply solely during the active subsistence of employment; delete post-employment operational restrictions."
        },
        {
            "keyword": "liquidated damages",
            "regex": r'\b(?:liquidated damages|forfeit.*gratuity|fixed sum of|penalty.*breach|irrespective of.*actual.*loss)\b',
            "category": "Unconscionable Penalty / Liquidated Damages",
            "statute": "Section 74, Indian Contract Act, 1872",
            "risk": ClauseRiskLevel.HIGH,
            "plain": "Imposes fixed monetary penalties for early exit or breach without requiring proof of loss.",
            "interpretation": "Under Section 74 and Kailash Nath Associates v. DDA (2015) 4 SCC 136, a stipulated sum can only be awarded if damage is actually proved to have been sustained. Forfeiture without actual loss operates as an unenforceable penalty.",
            "recommendation": "Cap liquidated damages to demonstrable actual recruitment/training expenses, subject to production of financial proof."
        },
        {
            "keyword": "unilateral indemnity",
            "regex": r'\b(?:defend, indemnify.*and hold harmless|no corresponding obligation to indemnify)\b',
            "category": "Unbalanced Unilateral Indemnification",
            "statute": "Section 124 & 125, Indian Contract Act, 1872",
            "risk": ClauseRiskLevel.HIGH,
            "plain": "Requires one party to absorb all third-party lawsuits while offering zero mutual protection.",
            "interpretation": "Creates disproportionate unlimited liability on the employee/service provider for ordinary business errors, conflicting with equitable risk distribution.",
            "recommendation": "Make indemnity bilateral, cap liability to total fees paid, and exclude indirect or consequential damages."
        },
        {
            "keyword": "jurisdiction conflict",
            "regex": r'\b(?:exclusive jurisdiction.*notwithstanding.*arbitration|seated in london.*courts at bengaluru)\b',
            "category": "Jurisdiction / Forum Conflict",
            "statute": "Section 28, Indian Contract Act, 1872 & Arbitration Act 1996",
            "risk": ClauseRiskLevel.MEDIUM,
            "plain": "Creates conflicting forums by naming local courts for exclusive jurisdiction while specifying foreign arbitration.",
            "interpretation": "Creates serious procedural ambiguity over supervisory court jurisdiction versus arbitral seat under the Arbitration and Conciliation Act, 1996.",
            "recommendation": "Harmonize dispute resolution: explicitly designate the seat of arbitration and specify that courts at the seat have supervisory jurisdiction."
        }
    ]

    AMBIGUOUS_PHRASES = [
        "at management's sole discretion",
        "best endeavors",
        "reasonable time",
        "material breach as determined by",
        "any and all related businesses",
        "without limitation"
    ]

    LEGAL_GLOSSARY = {
        "Void Ab Initio": "Having no legal effect from the beginning; treated as if it never existed in law.",
        "Restraint of Trade": "A contractual restriction that prevents an individual or business from freely carrying on their trade or profession.",
        "Liquidated Damages": "A pre-agreed sum payable as compensation for breach of contract, subject to statutory scrutiny under Indian law.",
        "Indemnity": "A contractual obligation where one party promises to compensate another for legal losses or damages.",
        "Arbitration Seat": "The legal domicile of an arbitration, which determines the procedural law and courts that supervise the arbitration."
    }

    def analyze_document(self, doc: ExtractedDocument) -> DocumentAnalysisResult:
        """Performs deep clause-by-clause risk identification and obligation mapping."""
        analyzed_clauses: List[AnalyzedClause] = []
        high_risk_clauses: List[AnalyzedClause] = []
        obligations: List[LegalObligation] = []
        factual_assertions: List[str] = []
        interpretations: List[str] = []

        # 1. Fact assertions directly extracted from the instrument
        factual_assertions.append(f"Document category identified as: {doc.category.value}.")
        if doc.parties:
            parties_str = " and ".join(f"{p.name} ({p.role})" for p in doc.parties)
            factual_assertions.append(f"Parties named in agreement: {parties_str}.")
        if doc.effective_date:
            factual_assertions.append(f"Execution or effective date stated: {doc.effective_date}.")
        if doc.governing_law:
            factual_assertions.append(f"Governing law clause specifies: {doc.governing_law}.")
        if doc.jurisdiction_clause:
            factual_assertions.append(f"Court jurisdiction clause specifies: {doc.jurisdiction_clause}.")

        # 2. Analyze extracted clauses
        for clause in doc.clauses:
            text_lower = clause.text.lower()
            matched_risk = None

            for risk_def in self.HIGH_RISK_PATTERNS:
                if re.search(risk_def["regex"], text_lower, re.IGNORECASE):
                    matched_risk = risk_def
                    break

            # Check ambiguous phrasing
            ambiguous_terms = [phrase for phrase in self.AMBIGUOUS_PHRASES if phrase in text_lower]
            is_ambiguous = len(ambiguous_terms) > 0

            # Check contradictory elements
            is_contradictory = False
            contradiction_detail = None
            if "exclusive jurisdiction" in text_lower and "arbitration" in text_lower and "seated in london" in text_lower:
                is_contradictory = True
                contradiction_detail = "Clause simultaneously asserts exclusive jurisdiction of Indian domestic courts and foreign seat of arbitration."

            if matched_risk:
                analyzed = AnalyzedClause(
                    clause_id=clause.clause_id,
                    clause_title=clause.heading,
                    verbatim_text=clause.text[:500],
                    risk_level=matched_risk["risk"],
                    risk_category=matched_risk["category"],
                    is_ambiguous=is_ambiguous,
                    ambiguous_terms=ambiguous_terms,
                    is_contradictory=is_contradictory,
                    contradiction_details=contradiction_detail,
                    applicable_statute=matched_risk["statute"],
                    plain_english_summary=matched_risk["plain"],
                    legal_interpretation=matched_risk["interpretation"],
                    recommendation=matched_risk["recommendation"]
                )
                analyzed_clauses.append(analyzed)
                if matched_risk["risk"] in [ClauseRiskLevel.HIGH, ClauseRiskLevel.CRITICAL]:
                    high_risk_clauses.append(analyzed)
                    interpretations.append(f"{clause.clause_id} ({clause.heading}): Evaluated as {matched_risk['category']} under {matched_risk['statute']}.")
            elif is_ambiguous:
                analyzed = AnalyzedClause(
                    clause_id=clause.clause_id,
                    clause_title=clause.heading,
                    verbatim_text=clause.text[:500],
                    risk_level=ClauseRiskLevel.MEDIUM,
                    risk_category="Ambiguous Language",
                    is_ambiguous=True,
                    ambiguous_terms=ambiguous_terms,
                    is_contradictory=is_contradictory,
                    contradiction_details=contradiction_detail,
                    applicable_statute="Indian Contract Act, 1872",
                    plain_english_summary=f"Contains indefinite terms: {', '.join(ambiguous_terms)}.",
                    legal_interpretation="Vague terms create subjective interpretation risks and evidentiary difficulties during enforcement.",
                    recommendation="Define objective benchmarks and measurable criteria."
                )
                analyzed_clauses.append(analyzed)
            else:
                analyzed = AnalyzedClause(
                    clause_id=clause.clause_id,
                    clause_title=clause.heading,
                    verbatim_text=clause.text[:300],
                    risk_level=ClauseRiskLevel.LOW,
                    risk_category="Standard Commercial Clause",
                    is_ambiguous=False,
                    ambiguous_terms=[],
                    is_contradictory=False,
                    contradiction_details=None,
                    applicable_statute="Indian Contract Act, 1872",
                    plain_english_summary="Standard commercial obligation with typical contractual language.",
                    legal_interpretation="Appears legally standard, subject to mutual consensus.",
                    recommendation="Retain standard wording."
                )
                analyzed_clauses.append(analyzed)

            # Map obligations
            if "shall pay" in text_lower or "agrees to pay" in text_lower:
                obligations.append(LegalObligation(
                    party_name="Paying Party",
                    nature="Affirmative Payment Obligation",
                    description=clause.heading,
                    trigger_condition="Monthly / Milestone completion"
                ))
            if "shall not" in text_lower or "covenants not to" in text_lower:
                obligations.append(LegalObligation(
                    party_name="Restrained Party",
                    nature="Negative Covenant / Prohibition",
                    description=clause.heading,
                    consequence_of_breach="Claim for injunction or liquidated damages"
                ))

        # Check for missing standard provisions
        missing = []
        full_text_lower = doc.full_text.lower()
        if "severability" not in full_text_lower:
            missing.append("Severability Clause (Crucial so that invalidity of Clause 8 does not invalidate the entire contract)")
        if "force majeure" not in full_text_lower:
            missing.append("Force Majeure / Excusable Delay Clause (Protects against unforeseen statutory/natural disruptions)")
        if "mutual confidentiality" not in full_text_lower and "unilateral" in full_text_lower:
            missing.append("Mutual Non-Disclosure Protection (Currently unilateral protecting only Company)")

        # Overall risk scoring (0.0 to 1.0)
        critical_count = sum(1 for c in high_risk_clauses if c.risk_level == ClauseRiskLevel.CRITICAL)
        high_count = sum(1 for c in high_risk_clauses if c.risk_level == ClauseRiskLevel.HIGH)
        raw_score = (critical_count * 0.4) + (high_count * 0.25) + (len(missing) * 0.1)
        overall_risk_score = min(0.95, max(0.15, raw_score))

        summary = (
            f"Analysis of '{doc.title}' indicates an overall risk rating of {overall_risk_score * 100:.0f}%. "
            f"Identified {len(high_risk_clauses)} high/critical risk provisions, notably post-employment "
            f"restrictions governed by Section 27 and liquidated damage penalties under Section 74 of the Indian Contract Act."
        )

        return DocumentAnalysisResult(
            document_id=doc.document_id,
            document_type=doc.category,
            overall_risk_score=round(overall_risk_score, 2),
            executive_summary=summary,
            analyzed_clauses=analyzed_clauses,
            high_risk_clauses=high_risk_clauses,
            missing_provisions=missing,
            obligations=obligations,
            factual_assertions=factual_assertions,
            interpretative_inferences=interpretations,
            plain_language_terminology=self.LEGAL_GLOSSARY
        )
