"""Audit trail + approval gate (masterprompt sections 12 & 13).

Two guarantees:
1. Every proposed action is logged (a logregel per section 13).
2. Nothing is booked/sent/filed without an explicit confirmation. The router parks a
   pending concept here; ``confirm`` is the only path that finalises it. Even after
   confirmation, *outbound* sends additionally require ``allow_auto_send`` to be on —
   safe-by-default, mirroring Apex's paper-trading gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from boekhouder.config import get_settings
from boekhouder.store import Store, get_store


@dataclass(slots=True)
class PendingAction:
    session_id: str
    kind: str                       # factuur | offerte | boeking
    summary: str
    artefact: Any
    finalize: Callable[[], dict] | None = None   # outbound effect, gated
    audit_id: int | None = None


class ApprovalGate:
    def __init__(self, store: Store | None = None) -> None:
        self.store = store or get_store()
        self.settings = get_settings()
        self._pending: dict[str, PendingAction] = {}

    def propose(self, action: PendingAction, *, actor: str, confidence: float,
                proposed_action: str) -> PendingAction:
        action.audit_id = self.store.log(
            actor=actor, input=action.summary, proposed_action=proposed_action,
            confidence=confidence, decision="pending")
        self._pending[action.session_id] = action
        return action

    def pending(self, session_id: str) -> PendingAction | None:
        return self._pending.get(session_id)

    def confirm(self, session_id: str, *, confirmed_by: str = "gebruiker") -> dict:
        action = self._pending.pop(session_id, None)
        if action is None:
            return {"ok": False, "message": "Er staat geen concept klaar om te bevestigen."}

        sent = False
        result: dict = {}
        if action.finalize is not None:
            if self.settings.allow_auto_send:
                result = action.finalize()
                sent = not result.get("dry_run", False)
            else:
                result = {"dry_run": True, "reason": "allow_auto_send staat uit"}

        final_id = self.store.next_number(action.kind) if action.kind in ("factuur", "offerte") else None
        self.store.log(
            actor=confirmed_by, input=action.summary, proposed_action="finalize",
            decision="confirmed", confirmed_by=confirmed_by, final_id=final_id)
        msg = (f"{action.kind.capitalize()} {final_id or ''} is definitief gemaakt"
               + (" en verzonden." if sent else " (lokaal; externe verzending staat uit)."))
        return {"ok": True, "message": msg.strip(), "final_id": final_id,
                "sent": sent, "detail": result}
