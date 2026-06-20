"""Compliance & Controle agent (masterprompt agent F / sections 6 & 12).

The guardrail. It inspects a request and blocks anything fraudulent — booking a private
expense as business without basis, fabricating/altering receipts, backdating, hiding
turnover, double booking, reclaiming btw without basis, fake suppliers/sham
constructions. When it blocks, it always returns a *legal alternative* and the evidence
that would be needed. It can only ever downgrade risk to ROOD, never upgrade to GROEN.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import RiskZone


@dataclass(slots=True)
class ComplianceRule:
    name: str
    pattern: re.Pattern
    reason: str
    alternative: str


# Patterns are intentionally broad: when in doubt we block and offer a legal path.
_RULES: list[ComplianceRule] = [
    ComplianceRule(
        "prive_als_zakelijk",
        re.compile(r"\b(prive|privé)\b.*\b(zakelijk|boek|aftrek)|"
                   r"\b(boek|zet).*\bprive\b.*\bzakelijk\b", re.IGNORECASE),
        "Privé-uitgave volledig zakelijk boeken zonder zakelijke onderbouwing.",
        "We kunnen wel een aantoonbaar zakelijk deel verdedigbaar boeken. "
        "Daarvoor heb ik nodig: zakelijke aanleiding, gebruik en een verdeelsleutel.",
    ),
    ComplianceRule(
        "backdaten",
        re.compile(r"\b(backdat|antidateer|terugdateer|datum\s+(aanpass|wijzig|verander)|"
                   r"vorig jaar.*datum|zet.*datum.*vorig)\w*", re.IGNORECASE),
        "Factuur/bon backdaten of de datum aanpassen.",
        "We gebruiken de werkelijke datum. Wel kan ik kijken naar legale timing van "
        "een toekomstige factuur of investering vóór jaarafsluiting.",
    ),
    ComplianceRule(
        "verzin_bon",
        re.compile(r"\b(verzin|verzonnen|fake|nep|valse?)\b.{0,20}\b(bon|bonnetje|factuur|kosten|leverancier)|"
                   r"\bmaak\b.{0,20}\b(nep|fake|valse?)\b.{0,20}\b(bon|factuur)|"
                   r"\bbon\b.{0,20}\bverzin", re.IGNORECASE),
        "Bon/kosten/leverancier verzinnen of vervalsen.",
        "Kosten kunnen alleen met een echt bewijsstuk. Stuur een geldige bon of factuur.",
    ),
    ComplianceRule(
        "omzet_verbergen",
        re.compile(r"\b(omzet|inkomsten|cash|contant).*(buiten de boek|verberg|niet (aangeven|boeken)|"
                   r"zwart)|\bzwart\b.*\b(omzet|geld)", re.IGNORECASE),
        "Omzet buiten de boeken houden of inkomsten verbergen.",
        "Alle omzet hoort in de administratie. Ik verlaag wel je belasting legaal: vraag "
        "'bespaar belasting' voor een optimalisatie-scan (aftrekposten, timing, EIA/MIA, pensioen).",
    ),
    ComplianceRule(
        "omzet_drukken",
        re.compile(r"(minder|niet alle|deel van de)\s+omzet\s*(op|aan)?gev|"
                   r"\bomzet\b\s+(niet|minder|lager)\s+(op|aan)?gev|"
                   r"\bomzet\b\s+(drukken|verlagen)\b.*\bbelasting|"
                   r"\bwinst\b\s+(wegsluiz|verberg|verdoezel)|"
                   r"\bfactu(ur|ren)\b.*\bniet\b.*(op|aan)?gev", re.IGNORECASE),
        "Minder/niet alle omzet opgeven om belasting te drukken.",
        "Omzet verlagen of weglaten mag niet — dat is fraude. Wel verlagen we je belasting "
        "legaal: alle aftrekposten, kosten/investeringen timen, EIA/MIA voor verduurzaming, "
        "pensioen/lijfrente en evt. BV-omslag. Vraag: 'bespaar belasting'.",
    ),
    ComplianceRule(
        "dubbel_boeken",
        re.compile(r"\b(dubbel|twee keer|2x)\s+(boek|aftrek|declareer)", re.IGNORECASE),
        "Dezelfde kosten dubbel boeken.",
        "Een kostenpost mag één keer. Ik controleer juist op dubbele boekingen.",
    ),
    ComplianceRule(
        "btw_zonder_basis",
        re.compile(r"\bbtw\b.*(terugvraag|terugvragen|claim).*(zonder|geen)\s+(bon|factuur|basis|bewijs)",
                   re.IGNORECASE),
        "Btw terugvragen zonder geldige basis.",
        "Btw-aftrek kan alleen met een correcte factuur op naam van het bedrijf.",
    ),
]


class ComplianceAgent(BaseAgent):
    name = "compliance"

    def check(self, text: str) -> ComplianceRule | None:
        for rule in _RULES:
            if rule.pattern.search(text):
                return rule
        return None

    def run(self, text: str) -> AgentResult:
        hit = self.check(text)
        if hit is None:
            return self.result(
                RiskZone.GROEN, 1.0,
                summary="Geen compliance-bezwaar gevonden.",
                blocked=False,
                requires_confirmation=False,
            )
        return self.result(
            RiskZone.ROOD, 1.0,
            summary="Dit kan ik niet zo verwerken.",
            reasons=[hit.reason],
            advies=hit.alternative,
            bewijs_nodig=["geldig, controleerbaar bewijsstuk"],
            actie_nodig="afwijzen",
            boekhouder_check=True,
            blocked=True,
        )

    def gate(self, result: AgentResult, text: str) -> AgentResult:
        """Apply the guardrail to another agent's result; blocks override everything."""
        hit = self.check(text)
        if hit is None:
            return result
        result.risk_zone = RiskZone.ROOD
        result.blocked = True
        result.actie_nodig = "afwijzen"
        result.boekhouder_check = True
        result.summary = "Dit kan ik niet zo verwerken."
        result.reasons = [hit.reason] + result.reasons
        result.advies = hit.alternative
        return result
