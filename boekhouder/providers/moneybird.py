"""Moneybird integration.

A real REST client (``httpx``) for the most common NL bookkeeping package. It only
ever creates **concept** sales invoices — it never books or sends definitively. When no
token/administration is configured it operates in dry-run mode: it returns the local
concept payload it *would* have posted, so the rest of the flow is identical with or
without credentials (mirrors Apex's paper-trading default).
"""
from __future__ import annotations

import logging

import httpx

from boekhouder.config import get_settings
from boekhouder.domain.documents import BankTransaction, SalesInvoice
from boekhouder.domain.money import Money
from boekhouder.providers.base import BookkeepingProvider

log = logging.getLogger("boekhouder.moneybird")


class MoneybirdProvider(BookkeepingProvider):
    name = "moneybird"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.dry_run = not self.settings.has_moneybird

    def _client(self) -> httpx.Client:
        s = self.settings
        return httpx.Client(
            base_url=f"{s.moneybird_base_url}/{s.moneybird_admin_id}",
            headers={"Authorization": f"Bearer {s.moneybird_token}"},
            timeout=20,
        )

    def _invoice_payload(self, invoice: SalesInvoice) -> dict:
        details = []
        for line in invoice.lines:
            details.append({
                "description": line.description,
                "amount": str(line.quantity),
                "price": str(line.unit_price_excl.amount),
                "tax_rate_percentage": line.btw_tarief.rate * 100,
            })
        return {
            "sales_invoice": {
                "contact_name": invoice.customer_name,
                "reference": invoice.project_ref or "",
                "details_attributes": details,
            }
        }

    def create_concept_sales_invoice(self, invoice: SalesInvoice) -> dict:
        payload = self._invoice_payload(invoice)
        if self.dry_run:
            log.info("Moneybird dry-run: concept invoice not sent (no token configured)")
            return {"dry_run": True, "would_post": payload,
                    "total_incl": str(invoice.total_incl.amount)}
        try:
            with self._client() as c:
                # state defaults to draft -> a concept, never auto-sent.
                resp = c.post("/sales_invoices.json", json=payload)
                resp.raise_for_status()
                return {"dry_run": False, "moneybird": resp.json()}
        except Exception as exc:  # noqa: BLE001 - never crash the chat flow
            log.warning("Moneybird create failed (%s); returning local concept", exc)
            return {"dry_run": True, "error": str(exc), "would_post": payload}

    def list_bank_transactions(self) -> list[BankTransaction]:
        if self.dry_run:
            return []
        try:
            with self._client() as c:
                resp = c.get("/financial_mutations.json")
                resp.raise_for_status()
                out: list[BankTransaction] = []
                for m in resp.json():
                    from datetime import date as _date

                    d = m.get("date") or ""
                    try:
                        parsed = _date.fromisoformat(d[:10])
                    except ValueError:
                        parsed = _date.today()
                    out.append(BankTransaction(
                        date=parsed,
                        amount=Money.euro(m.get("amount", "0")),
                        description=m.get("message", "") or "",
                        source="moneybird",
                        txn_id=str(m.get("id", "")),
                    ))
                return out
        except Exception as exc:  # noqa: BLE001
            log.warning("Moneybird list failed (%s)", exc)
            return []
