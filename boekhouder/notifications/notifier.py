"""Notification system with three priority tiers (pattern from Apex).

  P1 (CRITICAL) — needs attention now (compliance block, rood booking)
  P2 (WARNING)  — actionable (oranje item parked on the controlelijst)
  P3 (DIGEST)   — batched into a summary

Transports are pluggable; the MVP keeps an in-memory feed and can push to Telegram.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import asdict, dataclass, field
from enum import IntEnum

from boekhouder.engine.router import Reply

log = logging.getLogger("boekhouder.notifier")


class Priority(IntEnum):
    CRITICAL = 1
    WARNING = 2
    DIGEST = 3


@dataclass
class Notification:
    priority: Priority
    title: str
    body: str
    ts: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["priority"] = int(self.priority)
        return d


class Notifier:
    def __init__(self) -> None:
        self.feed: list[Notification] = []

    def emit(self, n: Notification) -> None:
        self.feed.append(n)
        self.feed = self.feed[-500:]
        emoji = {Priority.CRITICAL: "🚨", Priority.WARNING: "⚠️", Priority.DIGEST: "📋"}[n.priority]
        log.info("%s P%d %s — %s", emoji, int(n.priority), n.title, n.body[:80])

    def recent(self, n: int = 50) -> list[dict]:
        return [x.to_dict() for x in self.feed[-n:][::-1]]


def reply_to_notification(reply: Reply) -> Notification | None:
    from boekhouder.domain.enums import RiskZone

    if reply.blocked or reply.risk_zone == RiskZone.ROOD:
        return Notification(Priority.CRITICAL, f"Rood/geblokkeerd ({reply.agent})", reply.text)
    if reply.risk_zone == RiskZone.ORANJE:
        return Notification(Priority.WARNING, f"Controlepunt ({reply.agent})", reply.text)
    return None
