"""Leerregel — a versioned learning rule (masterprompt agent J).

The agent may learn from corrections, but only with versioning and a source. Fiscal
rules are NEVER changed automatically without a source/review, so ``approved_by`` and
``source`` are required to apply a rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone


def _today() -> date:
    return datetime.now(timezone.utc).date()


@dataclass(slots=True)
class Leerregel:
    rule_id: str
    description: str
    source: str                     # gebruiker | boekhouder | officiele_bron | systeemobservatie
    domain: str                     # toepassingsgebied, e.g. "leverancier:Gamma" or "btw"
    valid_from: date = field(default_factory=_today)
    valid_to: date | None = None
    confidence: float = 0.5
    example: str = ""
    last_checked: date = field(default_factory=_today)
    approved_by: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_fiscal(self) -> bool:
        return self.domain.startswith("btw") or self.domain.startswith("fiscaal")

    @property
    def is_applicable(self) -> bool:
        """A fiscal rule may only apply when it has a real source and approval."""
        today = _today()
        if self.valid_to and today > self.valid_to:
            return False
        if today < self.valid_from:
            return False
        if self.is_fiscal:
            return bool(self.approved_by) and self.source in {"boekhouder", "officiele_bron"}
        return True
