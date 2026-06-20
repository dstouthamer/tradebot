"""Learning agent (masterprompt agent J).

Stores corrections as versioned ``Leerregel`` records — always with a source, validity
window and confidence. Fiscal rules are never auto-applied without an accountant/official
source and approval (enforced by ``Leerregel.is_applicable``).
"""
from __future__ import annotations

import uuid

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.learning import Leerregel
from boekhouder.store import Store, get_store


class LearningAgent(BaseAgent):
    name = "learning"

    def __init__(self, store: Store | None = None) -> None:
        super().__init__()
        self.store = store or get_store()

    def remember(self, description: str, *, source: str, domain: str,
                 confidence: float = 0.6, example: str = "",
                 approved_by: str | None = None) -> Leerregel:
        rule = Leerregel(
            rule_id=f"R-{uuid.uuid4().hex[:8]}",
            description=description, source=source, domain=domain,
            confidence=confidence, example=example, approved_by=approved_by,
        )
        self.store.save_rule(rule)
        return rule

    def applicable_rules(self, domain_prefix: str = "") -> list[Leerregel]:
        return [r for r in self.store.get_rules()
                if r.is_applicable and r.domain.startswith(domain_prefix)]

    def run(self, description: str, *, source: str, domain: str,
            approved_by: str | None = None) -> AgentResult:
        rule = self.remember(description, source=source, domain=domain, approved_by=approved_by)
        applied = rule.is_applicable
        zone = RiskZone.GROEN if applied else RiskZone.ORANJE
        note = ("Regel opgeslagen en actief." if applied else
                "Regel opgeslagen maar nog niet actief: fiscale regels vereisen een "
                "officiële bron en goedkeuring.")
        return self.result(
            zone, rule.confidence, summary=note, payload=rule, requires_confirmation=False)
