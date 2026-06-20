"""EU-btw-kennis en grensoverschrijdende regels (feitelijk, legaal).

Bevat indicatieve standaard-btw-tarieven per EU-land en de echte regels voor verkoop
over de grens. Bewust géén schijnconstructies: een NL-ondernemer die aan NL-klanten
levert betaalt NL-btw, ongeacht waar hij "ingeschreven" staat. Lagere btw in een ander
land is alleen relevant bij **echte** grensoverschrijdende handel met de juiste regels.

Tarieven zijn indicatief (peildatum hieronder) — de dagelijkse kennis-update
(``boekhouder.knowledge``) signaleert wanneer ze gecontroleerd moeten worden.

Bron: Europese Commissie "VAT rates" + nationale belastingdiensten.
"""
from __future__ import annotations

PEILDATUM = "2025-01"
SOURCE = "https://taxation-customs.ec.europa.eu/taxation/vat/vat-rates_en"

# Standaard btw-tarief per EU-land (%). Indicatief — controleer bij de bron.
EU_BTW: dict[str, float] = {
    "LU": 17, "MT": 18, "CY": 19, "DE": 19, "RO": 19, "BG": 20, "FR": 20, "AT": 20,
    "NL": 21, "BE": 21, "ES": 21, "LT": 21, "LV": 21, "CZ": 21, "EE": 22, "IT": 22,
    "SI": 22, "IE": 23, "PL": 23, "PT": 23, "SK": 23, "EL": 24, "DK": 25, "SE": 25,
    "HR": 25, "FI": 25.5, "HU": 27,
}
NAMES: dict[str, str] = {
    "LU": "Luxemburg", "MT": "Malta", "CY": "Cyprus", "DE": "Duitsland", "RO": "Roemenië",
    "BG": "Bulgarije", "FR": "Frankrijk", "AT": "Oostenrijk", "NL": "Nederland",
    "BE": "België", "ES": "Spanje", "IT": "Italië", "IE": "Ierland", "PL": "Polen",
    "PT": "Portugal", "DK": "Denemarken", "SE": "Zweden", "FI": "Finland", "HU": "Hongarije",
}

# Echte, legale grensoverschrijdende regels.
CROSS_BORDER: list[tuple[str, str]] = [
    ("Verkoop aan een buitenlands bedrijf binnen de EU (B2B)",
     "Je factureert meestal met 0% / btw verlegd; de afnemer past de btw in zijn land toe. "
     "Vermeld beide btw-nummers en doe een ICP-opgave."),
    ("Verkoop aan particulieren in de EU (B2C goederen)",
     "Boven €10.000 totale EU-omzet reken je de btw van het land van de klant en draag je "
     "die af via de Eén-loket-regeling (OSS). Daaronder gewoon NL-btw."),
    ("Diensten",
     "Hoofdregel B2B: btw in het land van de afnemer (verlegd). B2C: meestal NL-btw, met "
     "uitzonderingen (o.a. digitale diensten via OSS)."),
    ("Export buiten de EU",
     "Levering van goederen naar buiten de EU is 0% btw (met geldige exportdocumenten)."),
]


def rate(code: str) -> float | None:
    return EU_BTW.get(code.upper())


def lowest(n: int = 5) -> list[tuple[str, float]]:
    return sorted(EU_BTW.items(), key=lambda kv: kv[1])[:n]


def highest(n: int = 3) -> list[tuple[str, float]]:
    return sorted(EU_BTW.items(), key=lambda kv: kv[1], reverse=True)[:n]


def name(code: str) -> str:
    return NAMES.get(code.upper(), code.upper())
