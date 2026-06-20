"""Fiscale Optimalisatie agent (masterprompt agent E / section 8).

Goal: the lowest *legally defensible* tax burden. Returns advice in the prescribed
structure (kans/voordeel/bewijs/risico/actie + boekhouder-check). It never calls
something "veilig" when it depends on interpretation — it uses "verdedigbaar mits goed
onderbouwd". Rule-based topic matching keeps it deterministic; an LLM may add narrative
through the seam but never changes the legal stance.
"""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import RiskZone


@dataclass(slots=True)
class FiscalAdvice:
    onderwerp: str
    besparing: str
    voorwaarde: str
    bewijs: str
    risico: str
    boekhouder_check: bool
    actie: str
    conclusie: str
    zone: RiskZone


_TOPICS: list[tuple[tuple[str, ...], FiscalAdvice]] = [
    (("gereedschap", "kopen", "investeer", "investering", "aanschaf"),
     FiscalAdvice(
        onderwerp="Investering in gereedschap/bedrijfsmiddel",
        besparing="Aftrek van kosten + mogelijk kleinschaligheidsinvesteringsaftrek (KIA); "
                  "btw terugvorderbaar bij zakelijke aanschaf.",
        voorwaarde="Aantoonbaar zakelijk gebruik en aanschaf vóór jaarafsluiting telt voor dit jaar.",
        bewijs="Factuur op bedrijfsnaam, betaalbewijs, en vastlegging van zakelijk gebruik.",
        risico="Bij overwegend privégebruik is volledige aftrek niet verdedigbaar.",
        boekhouder_check=False,
        actie="Koop alleen als cashflow boven je buffer blijft; bewaar de factuur op bedrijfsnaam.",
        conclusie="Doen mits zakelijk gebruik en correcte factuur — fiscaal voordeel is reëel.",
        zone=RiskZone.GROEN,
     )),
    (("btw", "kwartaal", "aangifte", "reservering"),
     FiscalAdvice(
        onderwerp="Btw-verplichting en -reservering",
        besparing="Voorkom een betaalpiek door per factuur direct btw te reserveren.",
        voorwaarde="Reserveer het btw-deel van elke verkoopfactuur op een aparte rekening.",
        bewijs="Btw-overzicht uit het boekhoudpakket per aangifteperiode.",
        risico="Te lage reservering geeft een liquiditeitsprobleem bij de aangifte.",
        boekhouder_check=False,
        actie="Stel een vaste btw-reservering in en check het saldo vóór de aangiftedatum.",
        conclusie="Doen: structurele reservering voorkomt verrassingen.",
        zone=RiskZone.GROEN,
     )),
    (("auto", "kilometer", "km", "rit"),
     FiscalAdvice(
        onderwerp="Auto en kilometers zakelijk/privé",
        besparing="Zakelijke kilometers of werkelijke autokosten zijn (deels) aftrekbaar.",
        voorwaarde="Sluitende rittenregistratie; bij privégebruik geldt een bijtelling/correctie.",
        bewijs="Rittenadministratie, brandstof-/onderhoudsbonnen, kentekenkoppeling.",
        risico="Zonder sluitende registratie corrigeert de Belastingdienst de aftrek.",
        boekhouder_check=True,
        actie="Houd vanaf nu een rittenregistratie bij; splits zakelijk/privé correct.",
        conclusie="Alleen doen met bewijs — verdedigbaar mits goed onderbouwd.",
        zone=RiskZone.ORANJE,
     )),
    (("telefoon", "laptop", "abonnement", "software", "werkkleding", "cursus", "opleiding"),
     FiscalAdvice(
        onderwerp="Gemengde kosten (telefoon/laptop/opleiding e.d.)",
        besparing="Het zakelijke deel is aftrekbaar; btw deels terugvorderbaar.",
        voorwaarde="Bepaal een redelijke zakelijke verdeelsleutel bij gemengd gebruik.",
        bewijs="Factuur op bedrijfsnaam + onderbouwing van het zakelijk gebruikspercentage.",
        risico="100% zakelijk boeken bij duidelijk privégebruik is niet verdedigbaar.",
        boekhouder_check=True,
        actie="Boek alleen het zakelijke deel; leg de verdeelsleutel vast.",
        conclusie="Verdedigbaar mits goed onderbouwd — boek alleen het zakelijke deel.",
        zone=RiskZone.ORANJE,
     )),
    (("kosten mis", "welke kosten", "aftrekpost", "vergeet"),
     FiscalAdvice(
        onderwerp="Mogelijk ontbrekende aftrekposten",
        besparing="Veelvergeten posten: telefoon/internet zakelijk deel, vakliteratuur, "
                  "verzekeringen, kleine gereedschappen, software, zakelijke reiskosten.",
        voorwaarde="Alleen aftrekbaar met een geldig bewijsstuk en zakelijk karakter.",
        bewijs="Bonnen/facturen op bedrijfsnaam per post.",
        risico="Laag, mits elke post een geldig bewijsstuk heeft.",
        boekhouder_check=False,
        actie="Verzamel ontbrekende bonnen en lever ze aan; ik koppel ze aan de bank.",
        conclusie="Doen: laaghangend fruit met geldig bewijs.",
        zone=RiskZone.GROEN,
     )),
]

_FALLBACK = FiscalAdvice(
    onderwerp="Algemeen fiscaal signaal",
    besparing="Afhankelijk van de situatie; deel meer details voor gericht advies.",
    voorwaarde="Zakelijk karakter en geldig bewijs.",
    bewijs="Relevante facturen/bonnen en context.",
    risico="Niet te bepalen zonder details.",
    boekhouder_check=True,
    actie="Geef aan welke kosten/situatie het betreft, dan reken ik het concreet uit.",
    conclusie="Eerst meer info nodig; bij twijfel boekhouder laten meekijken.",
    zone=RiskZone.ORANJE,
)


class FiscalAgent(BaseAgent):
    name = "fiscal"

    def advise(self, message: str) -> FiscalAdvice:
        low = message.lower()
        for keywords, advice in _TOPICS:
            if any(k in low for k in keywords):
                return advice
        return _FALLBACK

    def run(self, message: str) -> AgentResult:
        a = self.advise(message)
        return self.result(
            a.zone, 0.8 if a.zone == RiskZone.GROEN else 0.6,
            summary=a.onderwerp,
            reasons=[a.besparing],
            advies=a.actie,
            bewijs_nodig=[a.bewijs],
            boekhouder_check=a.boekhouder_check,
            requires_confirmation=False,
            payload=a,
        )
