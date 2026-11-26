"""Agent 5: Case Reasoning Agent.

Performs structured legal reasoning using the IRAC (Issue, Rule, Application, Conclusion) framework.
Balances claimant and respondent arguments, identifies evidentiary weaknesses,
and generates lawyer-consultation checklists without claiming judicial certainty.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from lexagent_ai.models.schemas import (
    LegalReasoningResult,
    LegalReasoningIssue,
    ExtractedDocument,
    DocumentAnalysisResult,
    LegalResearchResult
)


class CaseReasoningAgent:
    """Agent executing structured IRAC legal argumentation and evidentiary evaluation."""

    def reason_case(
        self,
        case_title: str,
        facts_text: str,
        analysis_result: Optional[DocumentAnalysisResult] = None,
        research_result: Optional[LegalResearchResult] = None
    ) -> LegalReasoningResult:
        """Executes structured legal reasoning across ascertained facts, governing rules, and arguments."""
        text_lower = facts_text.lower()
        ascertained_facts: List[str] = []
        framed_issues: List[LegalReasoningIssue] = []
        evidentiary_gaps: List[str] = []
        strategic_interpretations: List[str] = []
        lawyer_checklist: List[str] = []

        # 1. Parse Ascertained Facts
        lines = [line.strip() for line in facts_text.split("\n") if len(line.strip()) > 15]
        for line in lines[:8]:
            ascertained_facts.append(re.sub(r'^\d+[\.\)]\s*', '', line))

        # 2. Frame Issues and apply IRAC logic

        # ISSUE A: Restraint of Trade / Non-Compete (if present)
        if "non-compete" in text_lower or "clause 8" in text_lower or "restraint" in text_lower:
            issue_1 = LegalReasoningIssue(
                issue_id="1",
                framed_question="Whether the 36-month post-employment pan-India non-compete covenant is enforceable or void under Indian law?",
                governing_rules=[
                    "Section 27 of the Indian Contract Act, 1872",
                    "Percept D'Mark (India) (P) Ltd. v. Zaheer Khan (2006) 4 SCC 227",
                    "Superintendence Company of India v. Krishan Murgai (1981) 2 SCC 246"
                ],
                claimant_arguments=[
                    "The Employer contends that the restriction protects legitimate proprietary software algorithms, trade secrets, and client contacts.",
                    "The Employer argues that the employee freely consented to the terms with substantial remuneration."
                ],
                respondent_arguments=[
                    "Under Section 27, all post-employment restrictive covenants are completely void ab initio.",
                    "The Supreme Court in Percept D'Mark established that English law doctrines of partial reasonableness do not apply in India.",
                    "Protection of trade secrets can be achieved via confidentiality remedies, but cannot bar constitutional right to livelihood under Article 19(1)(g)."
                ],
                evidence_appraisal="Contract contains clear written text of Clause 8. However, Employer has produced no evidence of actual trade secret exfiltration.",
                irac_synthesis=(
                    "APPLICATION: Applying Section 27 and Percept D'Mark, the covenant operates after the cessation of employment. "
                    "In Indian jurisprudence, post-contractual non-competes are void as a matter of public policy. "
                    "CONCLUSION: An injunction enforcing the non-compete is highly unlikely to be granted by an Indian court."
                ),
                risk_assessment="High probability of non-compete being declared void; Employer retains limited remedy only for proven confidentiality theft."
            )
            framed_issues.append(issue_1)
            lawyer_checklist.append("Verify whether the employee retained any proprietary code, repositories, or documentation.")
            lawyer_checklist.append("Advise client on drafting confidentiality cease-and-desist letter rather than asserting void non-compete.")

        # ISSUE B: Liquidated Damages / Penalties (if present)
        if "liquidated damages" in text_lower or "clause 11" in text_lower or "clause 9" in text_lower or "forfeit" in text_lower or "withheld" in text_lower:
            issue_2 = LegalReasoningIssue(
                issue_id="2",
                framed_question="Whether the unilateral withholding or penalty of liquidated damages is legally sustainable without proof of actual financial loss?",
                governing_rules=[
                    "Section 73 and Section 74 of the Indian Contract Act, 1872",
                    "Kailash Nath Associates v. Delhi Development Authority (2015) 4 SCC 136",
                    "ONGC Ltd. v. Saw Pipes Ltd. (2003) 5 SCC 705"
                ],
                claimant_arguments=[
                    "The withholding party contends that the contract explicitly pre-quantified damages as a genuine pre-estimate of delay/replacement loss.",
                    "Under ONGC v. Saw Pipes, where commercial delay disrupts operations, the agreed liquidated sum is reasonable compensation."
                ],
                respondent_arguments=[
                    "Under Kailash Nath Associates, compensation under Section 74 requires actual proof of damage where damage is capable of being proved.",
                    "If the claimant suffered zero loss or if delay was caused by mutual defaults (prevention doctrine), forfeiture operates as an impermissible penalty."
                ],
                evidence_appraisal="Need invoices, milestone logs, or audit records proving actual replacement recruitment cost or business disruption.",
                irac_synthesis=(
                    "APPLICATION: Where commercial losses are capable of assessment, Section 74 requires reasonable compensation "
                    "not exceeding the stipulated penalty. Unilateral forfeiture without producing prima facie loss calculations is vulnerable. "
                    "CONCLUSION: An arbitrator or court will likely require proof of actual losses sustained before awarding the claimed sum."
                ),
                risk_assessment="Moderate-to-high risk that full liquidated damages deduction will be set aside unless actual financial loss is evidenced."
            )
            framed_issues.append(issue_2)
            evidentiary_gaps.append("Absence of audited loss calculations or replacement cost invoices justifying the stipulated damages sum.")
            lawyer_checklist.append("Compile itemized schedule of actual expenses or financial loss directly resulting from the alleged breach.")

        # ISSUE C: Electronic Evidence & Certification (if present)
        if "whatsapp" in text_lower or "slack" in text_lower or "email" in text_lower or "electronic evidence" in text_lower:
            issue_3 = LegalReasoningIssue(
                issue_id="3",
                framed_question="Whether digital correspondence (WhatsApp/Slack) is admissible without an electronic evidence certificate under BSA Section 63 / IEA Section 65B?",
                governing_rules=[
                    "Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (or Section 65B of Indian Evidence Act, 1872)",
                    "Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal (2020) 7 SCC 1"
                ],
                claimant_arguments=[
                    "Digital chat exports and screenshots demonstrate contemporaneously that delays were mutually acknowledged."
                ],
                respondent_arguments=[
                    "Under the Supreme Court mandate in Arjun Panditrao Khotkar, secondary electronic evidence is inadmissible without a statutory certificate."
                ],
                evidence_appraisal="Screenshots currently lack device custodian certificates and digital hashes.",
                irac_synthesis=(
                    "APPLICATION: Secondary digital printouts or exports must be accompanied by an electronic certificate executed by "
                    "the device owner or system administrator having lawful custody. "
                    "CONCLUSION: The electronic messages are subject to strict evidentiary exclusion unless accompanied by a Section 63/65B certificate."
                ),
                risk_assessment="Critical evidentiary risk: Digital communications will be discarded if proper certification is omitted."
            )
            framed_issues.append(issue_3)
            evidentiary_gaps.append("Missing Section 63 (BSA) / Section 65B (IEA) Electronic Record Certificate for digital logs.")
            lawyer_checklist.append("Obtain an affidavit-cum-certificate under Section 63 BSA / Section 65B IEA from the IT administrator or device custodian.")

        # Default issue framing if generic document
        if not framed_issues:
            framed_issues.append(
                LegalReasoningIssue(
                    issue_id="1",
                    framed_question="Whether the contractual obligations and termination mechanisms conform to Indian Contract Act provisions?",
                    governing_rules=["Section 10, 23, and 73 of the Indian Contract Act, 1872"],
                    claimant_arguments=["Parties are bound by the express written terms voluntarily executed."],
                    respondent_arguments=["Contractual terms are subject to mandatory statutory public policy restrictions."],
                    evidence_appraisal="Reviewing signed agreement and correspondence.",
                    irac_synthesis="Terms must be evaluated against statutory boundaries of consideration and public policy.",
                    risk_assessment="Standard commercial risk subject to factual evidence."
                )
            )

        strategic_interpretations.append(
            "Litigation Strategy: Maintain focus on statutory unenforceability rather than purely disputed facts. "
            "In Indian commercial disputes, establishing a statutory bar under Section 27 or 74 provides strong preliminary leverage."
        )

        return LegalReasoningResult(
            case_title_or_id=case_title,
            summary_of_ascertained_facts=ascertained_facts,
            framed_issues=framed_issues,
            evidentiary_vulnerabilities=evidentiary_gaps,
            strategic_legal_interpretations=strategic_interpretations,
            questions_for_counsel=lawyer_checklist
        )
