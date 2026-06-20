"""Optimalisatie-agent — proactieve, **legale** belastingoptimalisatie.

Dit is de "beste boekhouder die precies weet wat kan en net niet": maximaal scherp
binnen de wet, nooit eroverheen. Het verlaagt de **belasting** over je eerlijke omzet —
het verbergt of verlaagt **nooit** de omzet zelf (dat blokkeert de compliance-agent).

De scan is sector-, winst- en seizoensbewust (jaareinde-timing) en rangschikt de kansen
op relevantie. Alle bedragen/regelingen zijn indicatief (peiljaar 2026) en dragen een
"verdedigbaar mits onderbouwd / boekhouder-check"-stempel waar dat hoort.

Bronnen (geraadpleegd juni 2026):
- EIA/MIA/Vamil — RVO: https://www.rvo.nl/subsidies-financiering/eia en /mia-vamil
- Ondernemersaftrek/MKB-winstvrijstelling/KIA — KVK: https://www.kvk.nl/geldzaken/belastingtarieven-2026/
- Kleineondernemersregeling (KOR) btw — Belastingdienst
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain import tax_rates
from boekhouder.domain.company import CompanyProfile
from boekhouder.domain.enums import RiskZone

_KOR_OMZETGRENS = 20_000.0          # kleineondernemersregeling btw
_BV_OMSLAG_INDICATIE = 100_000.0    # ruwe winstindicatie waarboven BV interessant wordt
_VERDUURZAAM_SECTOREN = ("INSTALLATIE", "VERDUURZAMING", "ENERGIE", "BOUW")


@dataclass(slots=True)
class Opportunity:
    titel: str
    voordeel: str
    voorwaarde: str
    risico: str
    actie: str
    zone: RiskZone
    boekhouder_check: bool = False


@dataclass(slots=True)
class InvestmentBenefit:
    investering: float          # excl. btw (euro)
    kia: float
    eia: float
    mia: float
    extra_aftrek: float
    marginaal_tarief: float
    belastingbesparing: float
    btw_terug: float
    energy: bool
    milieu: bool


class OptimizationAgent(BaseAgent):
    name = "optimization"

    def scan(self, profile: CompanyProfile, totals: dict,
             today: date | None = None) -> list[Opportunity]:
        today = today or date.today()
        winst = max(0, totals.get("omzet_cents", 0) - totals.get("kosten_cents", 0)) / 100
        omzet = totals.get("omzet_cents", 0) / 100
        is_bv = profile.legal_form.upper() == "BV"
        is_eenmanszaak = not is_bv
        q4 = today.month >= 10
        sector = profile.sector.upper()

        ops: list[Opportunity] = []

        # 1. Altijd: aftrekposten compleet maken
        ops.append(Opportunity(
            "Alle aftrekposten compleet maken",
            "Elke euro zakelijke kosten met een geldig bewijsstuk verlaagt je winst en btw.",
            "Bon/factuur op bedrijfsnaam; zakelijk karakter.",
            "Laag, mits ieder bewijsstuk klopt.",
            "Stuur ontbrekende bonnen; ik koppel ze aan de bank en zet ze klaar.",
            RiskZone.GROEN))

        # 2. Sector verduurzaming/installatie: EIA / MIA / Vamil — vaak het grootste voordeel
        if any(s in sector for s in _VERDUURZAAM_SECTOREN):
            ops.append(Opportunity(
                "EIA — Energie-investeringsaftrek (jouw sector!)",
                "Ca. 40% van de investering extra aftrekbaar bovenop de normale afschrijving, "
                "voor bedrijfsmiddelen op de Energielijst (zonnepanelen, warmtepompen, "
                "isolatie, laadpalen e.d.).",
                "Bedrijfsmiddel moet op de RVO-Energielijst staan; melden bij RVO binnen "
                "3 maanden na opdracht; drempelbedrag per investering.",
                "Te missen als je de RVO-melding te laat doet.",
                "Check vóór aanschaf of het op de Energielijst staat en meld tijdig bij RVO.",
                RiskZone.ORANJE, boekhouder_check=True))
            ops.append(Opportunity(
                "MIA / Vamil — milieu-investeringen",
                "MIA: tot ~45% extra aftrek voor milieuvriendelijke bedrijfsmiddelen "
                "(Milieulijst). Vamil: 75% willekeurig afschrijven (liquiditeitsvoordeel).",
                "Bedrijfsmiddel op de Milieulijst; tijdige RVO-melding.",
                "Niet combineerbaar met EIA op hetzelfde middel.",
                "Bekijk de Milieulijst (RVO) vóór je investeert.",
                RiskZone.ORANJE, boekhouder_check=True))

        # 3. Eenmanszaak: ondernemersfaciliteiten benutten
        if is_eenmanszaak:
            ops.append(Opportunity(
                "Ondernemersaftrek volledig benutten",
                f"Zelfstandigenaftrek (€{int(tax_rates.ZELFSTANDIGENAFTREK_2026)}) + "
                f"{tax_rates.MKB_WINSTVRIJSTELLING_2026*100:.1f}".replace(".", ",")
                + "% MKB-winstvrijstelling verlagen je belastbare winst automatisch.",
                "Voldoen aan het urencriterium (1.225 uur) voor de zelfstandigenaftrek.",
                "Urencriterium niet halen → geen zelfstandigenaftrek.",
                "Houd je uren bij; dan passen we de aftrek correct toe.",
                RiskZone.GROEN))

        # 4. KIA bij investeringen
        ops.append(Opportunity(
            "KIA — kleinschaligheidsinvesteringsaftrek",
            f"28% extra aftrek bij investeringen tussen €{int(tax_rates.KIA_MIN_INVESTERING)} "
            f"en €{int(tax_rates.KIA_MAX_INVESTERING)} (2026).",
            "Het totaal aan investeringen in het jaar bepaalt het percentage.",
            "Onder de drempel van €2.901 → geen KIA.",
            "Bundel investeringen in hetzelfde jaar om boven de drempel te komen.",
            RiskZone.GROEN))

        # 5. Jaareinde-timing (sterker in Q4)
        ops.append(Opportunity(
            "Timing rond jaareinde",
            "Kosten/investeringen vóór 31-12 naar voren halen drukt de winst van dít jaar; "
            "factureren mag je legaal spreiden zolang de prestatie klopt.",
            "De prestatie/levering moet kloppen bij de gekozen datum (geen backdaten).",
            "Schijnverschuiving zonder echte prestatie = niet toegestaan.",
            ("Het is Q4 — plan resterende investeringen nú in." if q4
             else "Zet grote investeringen slim rond de jaarwisseling."),
            RiskZone.GROEN if not q4 else RiskZone.ORANJE))

        # 6. Pensioen / lijfrente
        ops.append(Opportunity(
            "Oudedagsvoorziening (lijfrente/pensioen)",
            "Aftrekbare stortingen (jaarruimte) verlagen je belastbaar inkomen nu.",
            "Binnen je fiscale jaar-/reserveringsruimte storten bij een aanbieder.",
            "Te veel storten is niet aftrekbaar; geld staat lang vast.",
            "Laat je jaarruimte berekenen en stort vóór de deadline.",
            RiskZone.ORANJE, boekhouder_check=True))

        # 7. Oninbare debiteuren -> btw terug
        ops.append(Opportunity(
            "Oninbare facturen afboeken",
            "Btw op definitief oninbare facturen kun je terugvragen; de kosten zijn aftrekbaar.",
            "Aantoonbaar dat de vordering oninbaar is.",
            "Te vroeg afboeken terwijl betaling nog komt.",
            "Markeer structurele wanbetalers; ik zet ze klaar voor afboeking.",
            RiskZone.GROEN))

        # 8. KOR (alleen bij lage omzet)
        if 0 < omzet < _KOR_OMZETGRENS:
            ops.append(Opportunity(
                "KOR — kleineondernemersregeling (btw)",
                "Bij omzet onder €20.000 kun je vrijstelling van btw krijgen (geen btw-aangifte).",
                "Aanmelden bij de Belastingdienst; geldt dan minimaal 3 jaar; geen btw-aftrek meer.",
                "Niet handig als je veel btw op inkopen/investeringen hebt.",
                "Reken voor of KOR in jouw geval voordelig is.",
                RiskZone.ORANJE, boekhouder_check=True))

        # 9. BV-omslag bij hoge winst
        if is_eenmanszaak and winst >= _BV_OMSLAG_INDICATIE:
            ops.append(Opportunity(
                "Overweeg een BV (bij deze winst)",
                "Boven ~€100.000 winst kan een BV fiscaal gunstiger zijn (vpb + box 2-timing, "
                "DGA-salaris).",
                "Gebruikelijk-loonregeling; oprichtings- en administratiekosten.",
                "Niet altijd voordelig; sterk afhankelijk van je situatie.",
                "Laat een omslagpunt-berekening maken door je fiscalist.",
                RiskZone.ORANJE, boekhouder_check=True))

        return ops

    def investment_benefit(self, investering: float, winst: float, legal_form: str,
                           *, energy: bool = False, milieu: bool = False) -> InvestmentBenefit:
        """Reken het concrete fiscale voordeel van één investering uit (indicatief).

        ``investering`` is excl. btw. EIA en MIA gelden niet samen op hetzelfde middel;
        bij twijfel kiezen we EIA (energie) en anders MIA (milieu).
        """
        kia = tax_rates.kia_deduction(investering)
        eia = tax_rates.eia_deduction(investering) if energy else 0.0
        mia = tax_rates.mia_deduction(investering) if (milieu and not energy) else 0.0
        extra = round(kia + eia + mia, 2)
        rate = tax_rates.marginal_rate(winst, legal_form)
        besparing = round(extra * rate, 2)
        btw_terug = round(investering * tax_rates.BTW_HOOG, 2)
        return InvestmentBenefit(
            investering=round(investering, 2), kia=kia, eia=eia, mia=mia, extra_aftrek=extra,
            marginaal_tarief=rate, belastingbesparing=besparing, btw_terug=btw_terug,
            energy=energy, milieu=milieu)

    def proactive_alerts(self, profile: CompanyProfile, totals: dict,
                         today: date | None = None) -> list[str]:
        """Korte, dwingende signalen die de agent uit zichzelf afgeeft."""
        today = today or date.today()
        winst = max(0, totals.get("omzet_cents", 0) - totals.get("kosten_cents", 0)) / 100
        alerts: list[str] = []
        if today.month >= 10:
            dagen = (date(today.year, 12, 31) - today).days
            alerts.append(
                f"⏰ Nog {dagen} dagen tot 31-12: investeringen en kosten die je dít jaar "
                "doet, drukken de winst van dit jaar. Plan grote aankopen nu in.")
        elif today.month <= 2:
            alerts.append("🗓️ Begin van het jaar: leg je urenregistratie en btw-reservering "
                          "meteen goed aan — dat scheelt straks werk en belasting.")
        if profile.legal_form.upper() != "BV" and winst >= _BV_OMSLAG_INDICATIE:
            alerts.append("📈 Je winst is fors — laat een BV-omslagberekening maken, dat kan "
                          "vanaf dit niveau honderden tot duizenden euro's schelen.")
        if any(s in profile.sector.upper() for s in _VERDUURZAAM_SECTOREN):
            alerts.append("🔋 Verduurzamingsinvestering gepland? Check vóór aanschaf de RVO "
                          "Energie-/Milieulijst (EIA/MIA) en meld binnen 3 maanden.")
        return alerts

    def run(self, profile: CompanyProfile, totals: dict,
            today: date | None = None) -> AgentResult:
        ops = self.scan(profile, totals, today)
        groen = sum(1 for o in ops if o.zone == RiskZone.GROEN)
        return self.result(
            RiskZone.GROEN, 0.7,
            summary=f"Legale optimalisatie-scan: {len(ops)} kansen ({groen} direct verdedigbaar).",
            advies="Maximaal voordeel binnen de wet — geen omzet verbergen, wel slim aftrekken en timen.",
            boekhouder_check=any(o.boekhouder_check for o in ops),
            requires_confirmation=False,
            payload=ops)
