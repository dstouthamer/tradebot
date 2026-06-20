"""Btw-aangifte (kwartaal) — berekenen en klaarzetten.

Berekent de aangifte omzetbelasting uit de geboekte facturen (verschuldigde btw) en
boekingen (voorbelasting). Indienen gebeurt nooit automatisch: dat vereist een echt
kanaal (Digipoort/eHerkenning of je boekhoudpakket) én een expliciete bevestiging.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.money import Money


def current_quarter(today: date | None = None) -> tuple[int, int]:
    today = today or date.today()
    return today.year, (today.month - 1) // 3 + 1


@dataclass(slots=True)
class VatReturn:
    year: int
    quarter: int
    omzet_excl: Money
    verschuldigd: Money         # af te dragen btw (output)
    voorbelasting: Money        # terug te vorderen btw (input)
    saldo: Money                # > 0 betalen, < 0 terugkrijgen

    @property
    def te_betalen(self) -> bool:
        return self.saldo.cents >= 0


class VatReturnAgent(BaseAgent):
    name = "vat_return"

    def build(self, figures: dict) -> VatReturn:
        return VatReturn(
            year=figures["year"], quarter=figures["quarter"],
            omzet_excl=Money(figures["omzet_excl_cents"]),
            verschuldigd=Money(figures["verschuldigd_cents"]),
            voorbelasting=Money(figures["voorbelasting_cents"]),
            saldo=Money(figures["saldo_cents"]),
        )

    def run(self, figures: dict) -> AgentResult:
        vr = self.build(figures)
        richting = "te betalen" if vr.te_betalen else "terug te ontvangen"
        return self.result(
            RiskZone.GROEN, 0.8,
            summary=f"Btw-aangifte Q{vr.quarter} {vr.year}: {abs(vr.saldo.cents) / 100:.2f} euro {richting}.",
            advies="Controleer de cijfers; indienen kan na bevestiging (vereist een "
                   "ingesteld kanaal zoals Moneybird/Digipoort).",
            actie_nodig="bevestigen",
            boekhouder_check=True,
            payload=vr)
