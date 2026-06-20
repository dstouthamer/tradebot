"""Output formatters — the masterprompt's exact Dutch templates (sections 7–11).

Each function takes a produced artefact (from an ``AgentResult.payload``) and renders
the verbatim template. Numbers come straight from the domain objects, never re-derived.
"""
from __future__ import annotations

from boekhouder.agents.cfo import CfoAnalysis
from boekhouder.agents.fiscal import FiscalAdvice
from boekhouder.agents.forecast import Forecast
from boekhouder.agents.optimization import InvestmentBenefit, Opportunity
from boekhouder.domain.documents import Boeking, Quote, SalesInvoice
from boekhouder.domain.money import format_eur


def _d(value, fmt="%d-%m-%Y") -> str:
    return value.strftime(fmt) if value else "—"


def _ja_nee(value: bool) -> str:
    return "ja" if value else "nee"


# ----------------------------- section 7 ------------------------------- #
def boekingsvoorstel(b: Boeking, *, bankmatch: str = "—", advies: str = "",
                     vraag: str = "") -> str:
    lines = [
        "Boekingsvoorstel",
        f"* Leverancier: {b.supplier}",
        f"* Datum: {_d(b.doc_date)}",
        f"* Bedrag incl. btw: {format_eur(b.total_incl)}",
        f"* Btw: {format_eur(b.btw)} ({b.btw_tarief.value}%)",
        f"* Bedrag excl. btw: {format_eur(b.total_excl)}",
        f"* Categorie: {b.category}",
        f"* Project: {b.project or '—'}",
        f"* Bankmatch: {bankmatch}",
        f"* Confidence: {b.match_confidence}%",
        f"* Fiscaal risico: {b.risk_zone.value.lower()}",
        f"* Advies: {advies or (b.note or 'Klaar om te boeken na bevestiging.')}",
        f"* Actie nodig: {'boeken' if b.risk_zone.name == 'GROEN' else 'controleren'}",
        "",
        "Mijn beoordeling",
        b.note or "Zakelijk verdedigbaar op basis van het bewijs en de match.",
    ]
    if vraag:
        lines += ["", "Vraag aan gebruiker", vraag]
    return "\n".join(lines)


# ----------------------------- section 8 ------------------------------- #
def fiscaal_advies(a: FiscalAdvice) -> str:
    return "\n".join([
        "Fiscaal advies",
        f"* Onderwerp: {a.onderwerp}",
        f"* Mogelijke besparing: {a.besparing}",
        f"* Voorwaarde: {a.voorwaarde}",
        f"* Bewijs nodig: {a.bewijs}",
        f"* Risico: {a.risico}",
        f"* Boekhouder-check: {_ja_nee(a.boekhouder_check)}",
        f"* Aanbevolen actie: {a.actie}",
        "",
        "Conclusie",
        a.conclusie,
    ])


# ----------------------------- section 9 ------------------------------- #
def financiele_analyse(a: CfoAnalysis) -> str:
    f = a.fin
    return "\n".join([
        "Financiële analyse",
        f"* Omzet deze periode: {format_eur(f.omzet)}",
        f"* Kosten: {format_eur(f.kosten)}",
        f"* Brutomarge: {format_eur(f.brutomarge)} ({f.margin_pct:.0f}%)",
        f"* Nettowinst: {format_eur(f.brutomarge)}",
        f"* Btw-reservering: {format_eur(f.btw_reservering)}",
        f"* Openstaande facturen: {format_eur(f.openstaande_facturen)}",
        f"* Cashflowrisico: {a.cashflow_risk}",
        f"* Belangrijkste waarschuwing: {a.warning}",
        f"* Beste actie nu: {a.best_action}",
        "",
        "Advies",
        a.best_action,
    ])


# ----------------------- optimalisatie-scan --------------------------- #
def _eur(amount: float) -> str:
    from boekhouder.domain.money import Money

    return format_eur(Money.euro(amount))


def investerings_voordeel(b: InvestmentBenefit) -> str:
    soort = "EIA (energie)" if b.energy else "MIA (milieu)" if b.milieu else "geen EIA/MIA"
    lines = [
        f"Fiscaal voordeel van een investering van {_eur(b.investering)} (excl. btw)",
        "",
        f"* KIA (kleinschaligheid): {_eur(b.kia)}",
    ]
    if b.eia:
        lines.append(f"* EIA (energie, ~40%): {_eur(b.eia)}")
    if b.mia:
        lines.append(f"* MIA (milieu, tot 45%): {_eur(b.mia)}")
    lines += [
        f"* Totale extra aftrek: {_eur(b.extra_aftrek)}",
        f"* Geschatte belastingbesparing (≈{b.marginaal_tarief*100:.0f}% marginaal): "
        f"**{_eur(b.belastingbesparing)}**",
        f"* Btw terugvorderbaar (21%): {_eur(b.btw_terug)}",
        "",
        f"Toegepast: {soort}. Indicatief (peiljaar 2026) — EIA/MIA vereisen een "
        "RVO-melding binnen 3 maanden en het juiste bedrijfsmiddel op de Energie-/Milieulijst.",
        "Verdedigbaar mits onderbouwd; laat het door je boekhouder/fiscalist toetsen.",
    ]
    return "\n".join(lines)


def investerings_tip(b: InvestmentBenefit, energy: bool, milieu: bool) -> str:
    """Korte proactieve tip bij een herkende investering in een bon/boeking."""
    if b.extra_aftrek > 0:
        parts = [f"KIA {_eur(b.kia)}"]
        if b.eia:
            parts.append(f"EIA {_eur(b.eia)}")
        if b.mia:
            parts.append(f"MIA {_eur(b.mia)}")
        rvo = (" Staat het op de RVO Energie-/Milieulijst? Meld binnen 3 mnd."
               if (energy or milieu) else "")
        return (f"💡 Lijkt een investering ({_eur(b.investering)} excl. btw): "
                f"{' + '.join(parts)} → geschat ~{_eur(b.belastingbesparing)} minder belasting "
                f"(btw terug {_eur(b.btw_terug)}).{rvo} "
                f"Typ 'investering {int(b.investering)}' voor de volledige berekening.")
    if energy or milieu:
        return ("💡 Lijkt een verduurzamingsaankoop. Onder de aftrekdrempel, maar check de "
                "RVO-lijst en of afschrijven gunstiger is.")
    return ("💡 Lijkt een bedrijfsmiddel (>€450): meestal afschrijven over meerdere jaren; "
            "boven €2.901 aan investeringen dit jaar kan KIA gelden.")


def optimalisatie_scan(ops: list[Opportunity], alerts: list[str] | None = None) -> str:
    icon = {"GROEN": "🟢", "ORANJE": "🟠", "ROOD": "🔴"}
    lines = [
        "Legale belastingoptimalisatie — maximaal voordeel binnen de wet",
        "(Ik verlaag je belasting, nooit je opgegeven omzet. Omzet verbergen = fraude.)",
        "",
    ]
    if alerts:
        lines += alerts + [""]
    for i, o in enumerate(ops, 1):
        lines.append(f"{i}. {icon.get(o.zone.value, '•')} {o.titel}")
        lines.append(f"   Voordeel: {o.voordeel}")
        lines.append(f"   Voorwaarde: {o.voorwaarde}")
        lines.append(f"   Risico: {o.risico}")
        lines.append(f"   Actie: {o.actie}"
                     + ("  · (boekhouder-check)" if o.boekhouder_check else ""))
        lines.append("")
    lines.append("Conclusie: dit is verdedigbaar mits goed onderbouwd. De rode grens "
                 "(omzet verbergen, kosten verzinnen, backdaten) blijft uit.")
    return "\n".join(lines)


# --------------------------- prognose --------------------------------- #
def prognose(f: Forecast) -> str:
    lines = [
        f"Prognose (komende {f.horizon_days} dagen)",
        f"* Gem. netto cashflow per maand: {format_eur(f.avg_monthly_net)}",
        f"* Verwachte netto cashflow {f.horizon_days} dagen: {format_eur(f.projected_net)}",
        f"* Btw te reserveren (per {f.vat_period_months} mnd): {format_eur(f.vat_to_reserve)}",
        f"* Geschatte winst tot nu: {format_eur(f.profit_estimate)}",
        f"* Indicatieve belasting: {format_eur(f.tax_indication)}",
        "",
        "Waarschuwingen",
    ]
    lines += [f"  - {w}" for w in (f.warnings or ["geen"])]
    lines += ["", "Aannames"] + [f"  - {a}" for a in f.assumptions]
    lines += ["", "Advies",
              "Indicatief — laat belastingcijfers door je boekhouder/fiscalist toetsen."]
    return "\n".join(lines)


# ----------------------------- section 10 ------------------------------ #
def factuur(inv: SalesInvoice, company_name: str = "", iban: str = "") -> str:
    head = [
        f"CONCEPTFACTUUR {inv.invoice_number or '(nummer volgt)'}",
        f"Van: {company_name or '—'}",
        f"Aan: {inv.customer_name}",
        f"Factuurdatum: {_d(inv.invoice_date)}    Vervaldatum: {_d(inv.due_date)}",
        "",
        "Omschrijving                       Aantal   Prijs ex   Btw%    Totaal ex",
    ]
    for ln in inv.lines:
        head.append(
            f"{ln.description[:34]:<34} {ln.quantity:>6.0f}  "
            f"{format_eur(ln.unit_price_excl):>9}  {ln.btw_tarief.value:>4}  "
            f"{format_eur(ln.line_excl):>10}")
    head += [
        "",
        f"Totaal ex btw: {format_eur(inv.total_excl)}",
        f"Btw:           {format_eur(inv.total_btw)}",
        f"Totaal incl:   {format_eur(inv.total_incl)}",
        "",
        f"Betaalinstructie: voldoe binnen de termijn op {iban or inv.iban or 'IBAN (in te stellen)'}.",
    ]
    if inv.project_ref:
        head.append(f"Projectreferentie: {inv.project_ref}")
    return "\n".join(head)


# ----------------------------- section 11 ------------------------------ #
def offerte(q: Quote, company_name: str = "") -> str:
    head = [
        f"OFFERTE {q.quote_number or '(nummer volgt)'}",
        f"Van: {company_name or '—'}    Datum: {_d(q.quote_date)}    Geldig tot: {_d(q.valid_until)}",
        f"Aan: {q.customer_name}",
        "",
        f"Projectomschrijving: {q.project_description or '—'}",
        "",
        "Werkzaamheden / materialen / arbeid:",
    ]
    for ln in q.lines:
        head.append(f"  - {ln.description}: {format_eur(ln.line_excl)} ex btw")
    if q.assumptions:
        head += ["", "Aannames / stelposten:"] + [f"  - {a}" for a in q.assumptions]
    if q.exclusions:
        head += ["", "Uitsluitingen:"] + [f"  - {e}" for e in q.exclusions]
    head += [
        "",
        f"Prijs ex btw: {format_eur(q.total_excl)}",
        f"Btw:          {format_eur(q.total_btw)}",
        f"Prijs incl:   {format_eur(q.total_incl)}",
        "",
        f"Akkoord? Antwoord met 'akkoord' om de opdracht te bevestigen "
        f"(geldig tot {_d(q.valid_until)}).",
    ]
    return "\n".join(head)
