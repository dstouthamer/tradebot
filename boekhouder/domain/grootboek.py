"""Nederlands grootboekschema (vereenvoudigd, decimale rekeningindeling).

De Boekhoud-agent kiest hiermee automatisch de juiste **grootboekrekening** voor een
boeking — met het belangrijke onderscheid tussen **kosten** (4xxx/7xxx, direct ten laste
van het resultaat) en **investeringen/activa** (0xxx, op de balans en afschrijven).

Dit is een praktische standaardindeling; een echt pakket (Moneybird/e-Boekhouden) kan
een eigen of RGS-schema gebruiken. De koppeling is bewust simpel en uitbreidbaar.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Grootboek:
    nummer: str
    naam: str
    soort: str          # kosten | activa | balans | omzet


SCHEMA: list[Grootboek] = [
    # 0xxx — vaste activa (investeringen, afschrijven)
    Grootboek("0200", "Inventaris", "activa"),
    Grootboek("0250", "Gereedschap", "activa"),
    Grootboek("0300", "Machines en installaties", "activa"),
    Grootboek("0350", "Zonnepanelen/energie-installaties", "activa"),
    Grootboek("0700", "Vervoermiddelen", "activa"),
    # 1xxx — balans
    Grootboek("1300", "Debiteuren", "balans"),
    Grootboek("1530", "Te vorderen btw (voorbelasting)", "balans"),
    Grootboek("1600", "Crediteuren", "balans"),
    Grootboek("1520", "Af te dragen btw", "balans"),
    # 4xxx — kosten
    Grootboek("4400", "Huisvestingskosten", "kosten"),
    Grootboek("4500", "Autokosten", "kosten"),
    Grootboek("4600", "Representatiekosten", "kosten"),
    Grootboek("4700", "Kantoorkosten", "kosten"),
    Grootboek("4805", "Telefoon en internet", "kosten"),
    Grootboek("4810", "Verzekeringen", "kosten"),
    Grootboek("4820", "Opleidingskosten", "kosten"),
    Grootboek("4830", "Software en abonnementen", "kosten"),
    Grootboek("4840", "Werkkleding", "kosten"),
    Grootboek("4900", "Algemene kosten", "kosten"),
    # 7xxx — inkoop / 8xxx — omzet
    Grootboek("7000", "Inkoopwaarde / materialen", "kosten"),
    Grootboek("8000", "Omzet", "omzet"),
]
BY_NUMMER: dict[str, Grootboek] = {g.nummer: g for g in SCHEMA}

# Kosten-/inkooprekeningen op trefwoord (leverancier + omschrijving + categorie).
_KOSTEN_RULES: list[tuple[tuple[str, ...], str]] = [
    (("shell", "bp", "esso", "tango", "tankstation", "brandstof", "diesel", "benzine"), "4500"),
    (("restaurant", "horeca", "lunch", "diner", "albert heijn", "catering", "koffie"), "4600"),
    (("telefoon", "kpn", "vodafone", "t-mobile", "odido", "internet", "mobiel"), "4805"),
    (("software", "saas", "adobe", "microsoft 365", "google workspace", "licentie", "abonnement"), "4830"),
    (("verzekering", "aov", "aansprakelijkheid"), "4810"),
    (("cursus", "opleiding", "training", "seminar"), "4820"),
    (("werkkleding", "bedrijfskleding", "veiligheidsschoen"), "4840"),
    (("huur", "pand", "eneco", "nuon", "vattenfall", "huisvesting", "gas en licht"), "4400"),
    (("gamma", "hornbach", "praxis", "materialen", "installatie", "leiding", "buis",
      "kabel", "cv", "fitting", "groothandel"), "7000"),
    (("kantoor", "papier", "printer", "inkt", "bol", "staples", "postzegel"), "4700"),
]

# Activa-rekeningen voor investeringen op trefwoord.
_ACTIVA_RULES: list[tuple[tuple[str, ...], str]] = [
    (("zonnepan", "warmtepomp", "zonneboiler", "zonnecollector", "thuisbatterij",
      "accu", "laadpaal", "installatie"), "0350"),
    (("machine", "boormachine"), "0300"),
    (("gereedschap", "steiger"), "0250"),
    (("auto", "bus", "bestelbus", "aanhanger", "vervoer"), "0700"),
    (("laptop", "computer", "apparatuur", "inventaris", "bureau", "meubilair"), "0200"),
]


def classify(text: str, *, is_investment: bool = False, energy: bool = False) -> Grootboek:
    """Kies de grootboekrekening op basis van de tekst en of het een investering is."""
    low = text.lower()
    if is_investment:
        if energy:
            return BY_NUMMER["0350"]
        for kws, nr in _ACTIVA_RULES:
            if any(k in low for k in kws):
                return BY_NUMMER[nr]
        return BY_NUMMER["0200"]            # standaard activa: inventaris
    for kws, nr in _KOSTEN_RULES:
        if any(k in low for k in kws):
            return BY_NUMMER[nr]
    return BY_NUMMER["4900"]                # standaard: algemene kosten
