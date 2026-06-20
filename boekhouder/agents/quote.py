"""Offerte agent (masterprompt agent H).

Builds a concept ``Quote`` from an intake ``Intent``. For a vague request it produces a
rough quote, states its assumptions (aannames/stelposten) explicitly, adds validity,
and never sends automatically.
"""
from __future__ import annotations

from datetime import date, timedelta

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.agents.intake import Intent
from boekhouder.domain.company import CompanyProfile
from boekhouder.domain.documents import LineItem, Quote
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.money import Money, btw_from_incl

_DEFAULT_ASSUMPTIONS = [
    "Leidinglengte maximaal 5 meter.",
    "Montage op normaal bereikbare buitenmuur.",
    "Standaard elektrische aansluiting aanwezig binnen 3 meter.",
    "Geen hak-, breek- of steigerwerk inbegrepen (stelpost bij meerwerk).",
]
_DEFAULT_EXCLUSIONS = [
    "Dakdoorvoer en bijzondere bouwkundige aanpassingen.",
    "Verwijdering/afvoer van bestaande installatie tenzij vermeld.",
]


class QuoteAgent(BaseAgent):
    name = "quote"

    def __init__(self, profile: CompanyProfile | None = None) -> None:
        super().__init__()
        self.profile = profile or CompanyProfile.from_settings()

    def build(self, intent: Intent, *, quote_number: str | None = None,
              today: date | None = None) -> Quote:
        today = today or date.today()
        amount = intent.amount or Money(0)
        if intent.amount_basis == "incl":
            unit_excl = btw_from_incl(amount, intent.btw_tarief).excl
        else:
            unit_excl = amount
        unit_excl = Money(int(unit_excl.cents / max(intent.quantity, 1)))
        desc = intent.description or "Werkzaamheden"
        if intent.location and intent.location.lower() not in desc.lower():
            desc = f"{desc} te {intent.location}"
        line = LineItem(desc, intent.quantity, unit_excl, intent.btw_tarief)
        return Quote(
            customer_name=intent.customer or "Onbekende klant",
            lines=[line],
            quote_number=quote_number,
            quote_date=today,
            valid_until=today + timedelta(days=self.profile.quote_validity_days),
            project_description=desc,
            assumptions=list(_DEFAULT_ASSUMPTIONS),
            exclusions=list(_DEFAULT_EXCLUSIONS),
        )

    def run(self, intent: Intent, *, quote_number: str | None = None,
            today: date | None = None) -> AgentResult:
        if not intent.amount:
            return self.result(
                RiskZone.ORANJE, 0.5,
                summary="Voor een offerte heb ik minimaal een richtprijs of omschrijving nodig.",
                bewijs_nodig=["richtprijs of omvang van de klus"],
                actie_nodig="aanvullen",
                requires_confirmation=False,
            )
        quote = self.build(intent, quote_number=quote_number, today=today)
        return self.result(
            RiskZone.GROEN, 0.9,
            summary=f"Offerteconcept voor {quote.customer_name}: totaal {quote.total_incl}.",
            reasons=["Offerte gemaakt op basis van jouw input met expliciete aannames."],
            advies="Offerteconcept staat klaar met aannames en stelposten. "
                   "Wil je dat ik hem definitief maak en verstuur?",
            actie_nodig="bevestigen",
            payload=quote,
        )
