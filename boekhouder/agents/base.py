"""Base agent contract and the shared ``AgentResult`` schema.

Every agent returns the same shape so the router and formatters can treat them
uniformly — the accounting analog of Apex's ``AgentSignal``. The directional verdict
is a ``RiskZone`` traffic-light (groen/oranje/rood) instead of BUY/SELL.

``confidence`` is in [0, 1]. ``payload`` carries the concrete artefact an agent
produced (a Boeking, SalesInvoice, Quote, dict of analysis, …) so downstream code can
format it without re-deriving anything.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from boekhouder.domain.enums import RiskZone


@dataclass(slots=True)
class AgentResult:
    agent: str
    risk_zone: RiskZone
    confidence: float                       # [0, 1]
    summary: str = ""                       # one-line Dutch summary for the user
    reasons: list[str] = field(default_factory=list)
    advies: str = ""                        # concrete recommendation / next action
    bewijs_nodig: list[str] = field(default_factory=list)   # evidence still required
    actie_nodig: str | None = None          # boeken | controleren | afwijzen | bevestigen | None
    boekhouder_check: bool = False          # should an accountant review this?
    requires_confirmation: bool = True      # is this only a concept until confirmed?
    blocked: bool = False                   # compliance hard-stop
    payload: Any = None                     # the produced artefact
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def clamp(self) -> "AgentResult":
        self.confidence = max(0.0, min(1.0, self.confidence))
        return self


class BaseAgent:
    """Subclass and implement ``run``. Keep agents pure: data in, AgentResult out."""

    name: str = "base"

    def __init__(self) -> None:
        self.log = logging.getLogger(f"boekhouder.agents.{self.name}")

    def result(self, risk_zone: RiskZone, confidence: float, **kwargs: Any) -> AgentResult:
        return AgentResult(
            agent=self.name, risk_zone=risk_zone, confidence=confidence, **kwargs
        ).clamp()
