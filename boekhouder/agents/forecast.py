"""Prognose-agent — vooruitblik op cashflow, btw en belasting.

Deterministisch en uitlegbaar: projecteert op basis van de geïmporteerde
banktransacties (historisch netto per maand) en de geboekte omzet/kosten. Het verzint
geen cijfers — bij te weinig data zegt het dat eerlijk en vraagt om import. Alle
belastingschattingen zijn indicatief en "verdedigbaar mits onderbouwd", geen advies dat
zonder boekhouder-check als zeker mag gelden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.company import CompanyProfile
from boekhouder.domain import tax_rates
from boekhouder.domain.documents import BankTransaction
from boekhouder.domain.enums import RiskZone
from boekhouder.domain.money import Money

_VAT_PERIOD_MONTHS = {"MAAND": 1, "KWARTAAL": 3, "JAAR": 12}


@dataclass(slots=True)
class Forecast:
    horizon_days: int
    avg_monthly_net: Money
    projected_net: Money
    current_balance_estimate: Money
    vat_period_months: int
    vat_to_reserve: Money
    profit_estimate: Money
    tax_indication: Money
    warnings: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    zone: RiskZone = RiskZone.ORANJE


class ForecastAgent(BaseAgent):
    name = "forecast"

    def build(self, txns: list[BankTransaction], totals: dict,
              profile: CompanyProfile, *, horizon_days: int = 90) -> Forecast:
        net_cents = sum(t.amount.cents for t in txns)
        months = self._months_spanned(txns)
        avg_monthly = Money(int(net_cents / months)) if months else Money(0)
        projected = Money(int(avg_monthly.cents * (horizon_days / 30)))

        vat_months = _VAT_PERIOD_MONTHS.get(profile.vat_period.upper(), 3)
        net_btw = totals.get("omzet_btw_cents", 0) - totals.get("kosten_btw_cents", 0)
        vat_reserve = Money(max(net_btw, 0))

        winst_cents = totals.get("omzet_cents", 0) - totals.get("kosten_cents", 0)
        winst_eur = max(winst_cents, 0) / 100
        is_bv = profile.legal_form.upper() == "BV"
        tax = Money.euro(tax_rates.tax_indication(winst_eur, profile.legal_form))
        eff = tax_rates.effective_rate(winst_eur, profile.legal_form)

        warnings: list[str] = []
        zone = RiskZone.GROEN
        if avg_monthly.cents < 0:
            warnings.append("Gemiddelde maandelijkse cashflow is negatief.")
            zone = RiskZone.ROOD
        if vat_reserve.cents > max(net_cents, 1) * 0.5 and net_cents > 0:
            warnings.append("Btw-reservering is fors t.o.v. je cashflow — reserveer tijdig.")
            zone = RiskZone.ORANJE if zone == RiskZone.GROEN else zone
        if not txns:
            warnings.append("Geen banktransacties geïmporteerd — prognose is grof.")
            zone = RiskZone.ORANJE

        regime = (f"vennootschapsbelasting (19% tot €200.000, 25,8% daarboven) — peiljaar {tax_rates.TAX_YEAR}"
                  if is_bv else
                  f"inkomstenbelasting box 1 met zelfstandigenaftrek (€{int(tax_rates.ZELFSTANDIGENAFTREK_2026)}) "
                  f"en {tax_rates.MKB_WINSTVRIJSTELLING_2026*100:.1f}".replace(".", ",")
                  + f"% MKB-winstvrijstelling — peiljaar {tax_rates.TAX_YEAR}")
        assumptions = [
            f"Projectie op basis van gemiddelde over {months or 0} maand(en) historie.",
            f"Btw-aangifte per {profile.vat_period.lower()} ({vat_months} mnd).",
            f"Belastingindicatie: {regime} (effectief ~{eff*100:.0f}%).",
            "Heffingskortingen niet meegenomen — werkelijke aanslag valt meestal lager uit; "
            "laat je fiscalist meekijken.",
        ]
        return Forecast(
            horizon_days=horizon_days, avg_monthly_net=avg_monthly, projected_net=projected,
            current_balance_estimate=Money(net_cents), vat_period_months=vat_months,
            vat_to_reserve=vat_reserve, profit_estimate=Money(max(winst_cents, 0)),
            tax_indication=tax, warnings=warnings, assumptions=assumptions, zone=zone)

    @staticmethod
    def _months_spanned(txns: list[BankTransaction]) -> int:
        if not txns:
            return 0
        dates = [t.date for t in txns]
        lo, hi = min(dates), max(dates)
        return max(1, (hi.year - lo.year) * 12 + (hi.month - lo.month) + 1)

    def run(self, txns: list[BankTransaction], totals: dict,
            profile: CompanyProfile, *, horizon_days: int = 90) -> AgentResult:
        fc = self.build(txns, totals, profile, horizon_days=horizon_days)
        return self.result(
            fc.zone, 0.6,
            summary=f"Prognose {horizon_days} dagen",
            reasons=fc.warnings or ["Cashflow en reserveringen ogen op koers."],
            advies=("Houd je btw-reservering en buffer op peil; "
                    "laat de belastingindicatie door je fiscalist toetsen."),
            boekhouder_check=True,
            requires_confirmation=False,
            payload=fc,
        )
