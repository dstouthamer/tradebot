"""Factuur agent (masterprompt agent G).

Builds a concept ``SalesInvoice`` from an intake ``Intent``. Asks only for the minimal
missing fields. Never sends — the router/audit gate requires explicit confirmation,
and the standard reply is "Conceptfactuur staat klaar. Wil je dat ik deze definitief
maak en verstuur?".
"""
from __future__ import annotations

from datetime import date, timedelta

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.agents.intake import Intent
from boekhouder.domain.company import CompanyProfile
from boekhouder.domain.documents import LineItem, SalesInvoice
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.money import Money, btw_from_excl, btw_from_incl


class InvoiceAgent(BaseAgent):
    name = "invoice"

    def __init__(self, profile: CompanyProfile | None = None) -> None:
        super().__init__()
        self.profile = profile or CompanyProfile.from_settings()

    def build(self, intent: Intent, *, invoice_number: str | None = None,
              today: date | None = None) -> SalesInvoice:
        today = today or date.today()
        # Derive a per-line excl unit price from the intent amount + basis.
        amount = intent.amount or Money(0)
        if intent.amount_basis == "incl":
            unit_excl = btw_from_incl(amount, intent.btw_tarief).excl
        else:
            unit_excl = amount
        unit_excl = Money(int(unit_excl.cents / max(intent.quantity, 1)))
        line = LineItem(
            description=intent.description or "Werkzaamheden",
            quantity=intent.quantity,
            unit_price_excl=unit_excl,
            btw_tarief=intent.btw_tarief,
        )
        return SalesInvoice(
            customer_name=intent.customer or "Onbekende klant",
            lines=[line],
            invoice_number=invoice_number,
            invoice_date=today,
            due_date=today + timedelta(days=self.profile.payment_term_days),
            project_ref=intent.project,
            iban=self.profile.iban or None,
        )

    def run(self, intent: Intent, *, invoice_number: str | None = None,
            today: date | None = None) -> AgentResult:
        missing = list(intent.missing)
        if not intent.amount:
            if "bedrag" not in missing:
                missing.append("bedrag")
        if missing:
            return self.result(
                RiskZone.ORANJE, 0.5,
                summary="Ik mis nog wat gegevens voor de factuur.",
                bewijs_nodig=missing,
                actie_nodig="aanvullen",
                requires_confirmation=False,
            )
        invoice = self.build(intent, invoice_number=invoice_number, today=today)
        # btw sanity check (groen): line total reconciles.
        _ = btw_from_excl(invoice.total_excl, intent.btw_tarief)
        return self.result(
            RiskZone.GROEN, 0.95,
            summary=f"Conceptfactuur voor {invoice.customer_name}: totaal {invoice.total_incl}.",
            advies="Conceptfactuur staat klaar. Wil je dat ik deze definitief maak en verstuur?",
            actie_nodig="bevestigen",
            payload=invoice,
        )
