"""Audit trail + approval gate (masterprompt sections 12 & 13).

Two guarantees:
1. Every proposed action is logged (a logregel per section 13).
2. Nothing is booked/sent/filed without an explicit confirmation. The router parks a
   pending concept here; ``confirm`` is the only path that finalises it. Even after
   confirmation, *outbound* sends additionally require ``allow_auto_send`` to be on —
   safe-by-default, mirroring Apex's paper-trading gate.

Everything is tenant-scoped: pending concepts and audit entries belong to one tenant.
On confirm the artefact is persisted so prognoses/financiën erop kunnen rekenen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from boekhouder.config import get_settings
from boekhouder.domain.documents import Boeking, SalesInvoice
from boekhouder.store import LOCAL_TENANT, Store, get_store


@dataclass(slots=True)
class PendingAction:
    session_id: str
    kind: str                       # factuur | offerte | boeking
    summary: str
    artefact: Any
    tenant_id: str = LOCAL_TENANT
    finalize: Callable[[], dict] | None = None   # outbound effect, gated
    audit_id: int | None = None


class ApprovalGate:
    def __init__(self, store: Store | None = None) -> None:
        self.store = store or get_store()
        self.settings = get_settings()
        self._pending: dict[str, PendingAction] = {}

    @staticmethod
    def _key(tenant_id: str, session_id: str) -> str:
        return f"{tenant_id}:{session_id}"

    def propose(self, action: PendingAction, *, actor: str, confidence: float,
                proposed_action: str) -> PendingAction:
        action.audit_id = self.store.log(
            tenant_id=action.tenant_id, actor=actor, input=action.summary,
            proposed_action=proposed_action, confidence=confidence, decision="pending")
        self._pending[self._key(action.tenant_id, action.session_id)] = action
        return action

    def pending(self, session_id: str, tenant_id: str = LOCAL_TENANT) -> PendingAction | None:
        return self._pending.get(self._key(tenant_id, session_id))

    def confirm(self, session_id: str, *, tenant_id: str = LOCAL_TENANT,
                confirmed_by: str = "gebruiker") -> dict:
        action = self._pending.pop(self._key(tenant_id, session_id), None)
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

        final_id = (self.store.next_number(action.kind, tenant_id=tenant_id)
                    if action.kind in ("factuur", "offerte") else None)
        self._persist(action, final_id, sent, tenant_id)
        self.store.log(
            tenant_id=tenant_id, actor=confirmed_by, input=action.summary,
            proposed_action="finalize", decision="confirmed",
            confirmed_by=confirmed_by, final_id=final_id)
        msg = (f"{action.kind.capitalize()} {final_id or ''} is definitief gemaakt"
               + (" en verzonden." if sent else " (lokaal; externe verzending staat uit)."))
        if result.get("message"):                       # bv. Moneybird-instructie + link
            msg += " " + result["message"]
            if result.get("link"):
                msg += f" ({result['link']})"
        return {"ok": True, "message": msg.strip(), "final_id": final_id,
                "sent": sent, "detail": result}

    def _persist(self, action: PendingAction, final_id: str | None, sent: bool,
                 tenant_id: str) -> None:
        """Sla de bevestigde artefact op zodat prognoses/financiën erop kunnen rekenen."""
        art = action.artefact
        try:
            if action.kind == "factuur" and isinstance(art, SalesInvoice):
                art.invoice_number = final_id or art.invoice_number
                art.is_concept = False
                self.store.save_invoice(art, tenant_id,
                                        status="verzonden" if sent else "definitief")
            elif action.kind == "boeking" and isinstance(art, Boeking):
                art.is_definitief = True
                self.store.save_booking(art, tenant_id)
        except Exception:  # noqa: BLE001 - persistence must never block confirmation
            pass
