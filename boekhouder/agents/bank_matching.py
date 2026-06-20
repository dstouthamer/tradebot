"""Bank Matching agent (masterprompt agent C).

Scores how well a receipt/invoice matches each bank transaction (exact amount, date
window, supplier name, IBAN) and returns the best candidate with a 0-100 confidence and
human-readable reasons. The confidence band decides the action via ``engine.rules``.
"""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.documents import BankTransaction, ExtractedDocument
from boekhouder.domain.enums import RiskZone
from boekhouder.engine import rules


@dataclass(slots=True)
class MatchCandidate:
    transaction: BankTransaction
    confidence: int
    reasons: list[str]


def _name_overlap(a: str, b: str) -> bool:
    a, b = a.lower(), b.lower()
    return bool(a) and (a in b or b in a or any(tok in b for tok in a.split() if len(tok) > 3))


def score(doc: ExtractedDocument, txn: BankTransaction) -> MatchCandidate:
    conf = 0
    reasons: list[str] = []

    if doc.total_incl is not None:
        # Compare against the absolute (outgoing) amount.
        if abs(txn.amount.cents) == doc.total_incl.cents:
            conf += 55
            reasons.append("Bedrag exact gelijk")
        elif abs(abs(txn.amount.cents) - doc.total_incl.cents) <= 2:
            conf += 45
            reasons.append("Bedrag vrijwel gelijk (afrondingsverschil)")

    if doc.doc_date is not None:
        delta = abs((txn.date - doc.doc_date).days)
        if delta == 0:
            conf += 20
            reasons.append("Zelfde datum")
        elif delta <= rules.MATCH_DATE_WINDOW_DAYS:
            conf += 15
            reasons.append(f"Datum binnen {delta} dag(en)")

    if doc.supplier and _name_overlap(doc.supplier, f"{txn.counterparty} {txn.description}"):
        conf += 20
        reasons.append("Leveranciersnaam komt terug in transactie")

    if doc.iban and txn.counterparty_iban and doc.iban == txn.counterparty_iban:
        conf += 15
        reasons.append("IBAN komt overeen")

    return MatchCandidate(txn, min(conf, 100), reasons)


class BankMatchingAgent(BaseAgent):
    name = "bank_matching"

    def best_match(self, doc: ExtractedDocument,
                   transactions: list[BankTransaction]) -> MatchCandidate | None:
        candidates = [score(doc, t) for t in transactions]
        candidates = [c for c in candidates if c.confidence > 0]
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.confidence)

    def run(self, doc: ExtractedDocument, transactions: list[BankTransaction]) -> AgentResult:
        best = self.best_match(doc, transactions)
        if best is None:
            return self.result(
                RiskZone.ROOD, 0.2,
                summary="Geen passende banktransactie gevonden.",
                actie_nodig="afwijzen",
                bewijs_nodig=["betaalbewijs of juiste bankafschrift"],
                payload=None,
            )
        zone = rules.match_zone(best.confidence)
        action = rules.match_action(best.confidence)
        return self.result(
            zone, best.confidence / 100,
            summary=f"Mogelijke match met banktransactie van {best.transaction.amount} "
                    f"({best.confidence}% zekerheid).",
            reasons=best.reasons,
            actie_nodig=action,
            payload=best,
        )
