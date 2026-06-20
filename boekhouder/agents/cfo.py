"""CFO Advies agent (masterprompt agent I / section 9).

Produces a financial snapshot + one concrete action. It computes from whatever figures
it is given (typically aggregated by the store from concept bookings/invoices); when
data is missing it says so plainly rather than inventing numbers.
"""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.money import Money


@dataclass(slots=True)
class Financials:
    omzet: Money = Money(0)
    kosten: Money = Money(0)
    btw_reservering: Money = Money(0)
    openstaande_facturen: Money = Money(0)

    @property
    def brutomarge(self) -> Money:
        return self.omzet - self.kosten

    @property
    def margin_pct(self) -> float:
        return (self.brutomarge.cents / self.omzet.cents * 100) if self.omzet.cents else 0.0


@dataclass(slots=True)
class CfoAnalysis:
    fin: Financials
    cashflow_risk: str
    warning: str
    best_action: str
    zone: RiskZone


class CfoAgent(BaseAgent):
    name = "cfo"

    @staticmethod
    def financials_from_totals(totals: dict) -> Financials:
        """Bouw ``Financials`` uit de geaggregeerde store-cijfers."""
        net_btw = totals.get("omzet_btw_cents", 0) - totals.get("kosten_btw_cents", 0)
        return Financials(
            omzet=Money(totals.get("omzet_cents", 0)),
            kosten=Money(totals.get("kosten_cents", 0)),
            btw_reservering=Money(max(net_btw, 0)),
            openstaande_facturen=Money(totals.get("open_cents", 0)),
        )

    def analyse(self, fin: Financials | None) -> CfoAnalysis:
        if fin is None or (fin.omzet.cents == 0 and fin.kosten.cents == 0):
            empty = fin or Financials()
            return CfoAnalysis(
                empty,
                cashflow_risk="onbekend",
                warning="Nog onvoldoende geboekte data voor een betrouwbare analyse.",
                best_action="Importeer je bankafschrift en verwerk recente bonnen/facturen, "
                            "dan geef ik een concrete analyse.",
                zone=RiskZone.ORANJE,
            )
        margin = fin.margin_pct
        if margin < 20:
            zone, warning = RiskZone.ROOD, "Brutomarge is laag; tarief of materiaalopslag te krap."
            action = "Verhoog je arbeidstarief of materiaalopslag op dit type werk."
        elif fin.openstaande_facturen.cents > fin.omzet.cents * 0.4:
            zone, warning = RiskZone.ORANJE, "Veel openstaande facturen; debiteurenrisico."
            action = "Stuur betalingsherinneringen en werk bij late betalers met aanbetaling."
        else:
            zone, warning = RiskZone.GROEN, "Marge en cashflow ogen gezond."
            action = "Houd je btw-reservering op peil en bouw buffer op."
        risk = "hoog" if zone == RiskZone.ROOD else "verhoogd" if zone == RiskZone.ORANJE else "laag"
        return CfoAnalysis(fin, cashflow_risk=risk, warning=warning, best_action=action, zone=zone)

    def run(self, fin: Financials | None = None) -> AgentResult:
        a = self.analyse(fin)
        return self.result(
            a.zone, 0.7,
            summary="Financiële analyse",
            reasons=[a.warning],
            advies=a.best_action,
            requires_confirmation=False,
            payload=a,
        )
