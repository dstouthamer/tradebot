"""Boekhoud agent (masterprompt agent D).

Builds a concept ``Boeking`` from an extracted document and an optional bank match.
Assigns a risk zone (groen/oranje/rood) from evidence quality, match confidence and
category certainty. Never produces a definitive booking — confirmation happens later.
"""
from __future__ import annotations

from boekhouder.agents.bank_matching import MatchCandidate
from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.agents.optimization import OptimizationAgent
from boekhouder.domain import grootboek
from boekhouder.domain.documents import Boeking, ExtractedDocument
from boekhouder.domain.enums import BtwTarief, EvidenceQuality, RiskZone
from boekhouder.domain.money import Money, btw_from_incl


class BookkeepingAgent(BaseAgent):
    name = "bookkeeping"

    def build(self, doc: ExtractedDocument, match: MatchCandidate | None = None) -> Boeking:
        tarief = doc.btw_tarief or BtwTarief.HOOG
        total = doc.total_incl or Money(0)
        split = btw_from_incl(total, tarief)
        excl = doc.total_excl or split.excl
        zone, note = self._risk(doc, match)

        # Kies automatisch de juiste grootboekrekening (investering -> activa, anders kosten).
        text = f"{doc.supplier or ''} {doc.description or ''} {doc.category or ''}"
        is_inv, energy, _ = OptimizationAgent.detect_investment(text, float(excl.amount))
        gb = grootboek.classify(text, is_investment=is_inv, energy=energy)

        return Boeking(
            supplier=doc.supplier or "onbekend",
            doc_date=doc.doc_date,
            total_incl=total,
            btw=doc.btw_amount or split.btw,
            total_excl=excl,
            btw_tarief=tarief,
            category=doc.category or gb.naam,
            grootboek=gb.nummer,
            grootboek_naam=gb.naam,
            project=doc.project,
            payment_status="betaald" if match else "onbekend",
            bank_match_id=(match.transaction.txn_id or None) if match else None,
            match_confidence=match.confidence if match else 0,
            risk_zone=zone,
            note=note,
        )

    @staticmethod
    def _risk(doc: ExtractedDocument, match: MatchCandidate | None) -> tuple[RiskZone, str | None]:
        if doc.evidence_quality == EvidenceQuality.LAAG or doc.total_incl is None:
            return RiskZone.ROOD, "Onvoldoende bewijs om zakelijk te boeken."
        if doc.category is None or (match and match.confidence < 80):
            return RiskZone.ORANJE, "Categorie of bankmatch nog te bevestigen."
        if not match:
            return RiskZone.ORANJE, "Nog geen betaalbewijs gekoppeld."
        return RiskZone.GROEN, None

    def run(self, doc: ExtractedDocument, match: MatchCandidate | None = None) -> AgentResult:
        boeking = self.build(doc, match)
        reasons = [f"Categorie: {boeking.category}"]
        if match:
            reasons.append(f"Bankmatch {boeking.match_confidence}%")
        action = "boeken" if boeking.risk_zone == RiskZone.GROEN else "controleren"
        return self.result(
            boeking.risk_zone,
            0.9 if boeking.risk_zone == RiskZone.GROEN else 0.6,
            summary=f"Conceptboeking {boeking.supplier} {boeking.total_incl}.",
            reasons=reasons,
            advies=boeking.note or "Klaar om te boeken na bevestiging.",
            actie_nodig=action,
            boekhouder_check=boeking.risk_zone == RiskZone.ORANJE,
            payload=boeking,
        )
