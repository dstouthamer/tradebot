"""Nederlandse belastingtarieven — peiljaar 2026, mét bronvermelding.

Alle bedragen/percentages staan hier op één auditbare plek (zoals de masterprompt voor
fiscale regels vraagt: met bron en geldigheidsjaar). De berekeningen zijn **indicatief**:
heffingskortingen (algemene heffingskorting, arbeidskorting) en persoonlijke
omstandigheden zijn niet meegenomen, dus de echte aanslag valt meestal lager uit. Laat
het altijd door een fiscalist toetsen.

Bronnen (geraadpleegd juni 2026):
- Box 1-schijven 2026: MKB Servicedesk —
  https://www.mkbservicedesk.nl/belastingen/inkomstenbelasting/belastingschijven-box-1
- Zelfstandigenaftrek & MKB-winstvrijstelling 2026: KVK —
  https://www.kvk.nl/geldzaken/belastingtarieven-2026/ (en Countus Prinsjesdag 2025)
- Vennootschapsbelasting 2026: Belastingdienst —
  https://www.belastingdienst.nl/.../veranderingen-vennootschapsbelasting-2026
- KIA-grenzen 2026: Moore DRV / KVK (zie hierboven)
"""
from __future__ import annotations

TAX_YEAR = 2026

# ---- BTW (ongewijzigd in 2026) -------------------------------------------
BTW_HOOG = 0.21
BTW_LAAG = 0.09

# ---- Inkomstenbelasting box 1 2026 (onder AOW-leeftijd) -------------------
# (bovengrens_euro, tarief). De laatste schijf heeft geen bovengrens (inf).
BOX1_BRACKETS_2026: list[tuple[float, float]] = [
    (38_883.0, 0.3570),
    (79_137.0, 0.3756),
    (float("inf"), 0.4950),
]

# ---- Ondernemersfaciliteiten (eenmanszaak/IB-ondernemer) 2026 ------------
ZELFSTANDIGENAFTREK_2026 = 1_200.0      # daalt verder naar €900 in 2027
MKB_WINSTVRIJSTELLING_2026 = 0.127      # 12,7% (ongewijzigd t.o.v. 2025)

# ---- Kleinschaligheidsinvesteringsaftrek (KIA) 2026 ----------------------
KIA_MIN_INVESTERING = 2_901.0
KIA_MAX_INVESTERING = 398_236.0
KIA_TARIEF = 0.28                       # 28% in de eerste band
KIA_BAND1_TOP = 70_602.0                # tot hier 28%
KIA_FLAT = 19_769.0                     # vast maximumbedrag in de middenband (indicatief)
KIA_BAND2_TOP = 130_745.0               # daarboven afbouw
KIA_AFBOUW = 0.0756                     # afbouwpercentage boven band 2

# ---- Energie-/Milieu-investeringsaftrek (RVO) 2026 — indicatief ----------
EIA_TARIEF = 0.40                       # ~40% extra aftrek (Energielijst)
EIA_DREMPEL = 2_800.0
MIA_TARIEF_MAX = 0.45                   # tot 45% (Milieulijst), categorie-afhankelijk

# ---- Vennootschapsbelasting (BV) 2026 ------------------------------------
VPB_GRENS = 200_000.0
VPB_LAAG = 0.19                         # tot en met de grens
VPB_HOOG = 0.258                        # daarboven

SOURCES = {
    "box1": "https://www.mkbservicedesk.nl/belastingen/inkomstenbelasting/belastingschijven-box-1",
    "ondernemersaftrek": "https://www.kvk.nl/geldzaken/belastingtarieven-2026/",
    "vpb": "https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/winst/vennootschapsbelasting/veranderingen-vennootschapsbelasting-2026/veranderingen-vennootschapsbelasting-2026",
    "kia": "https://www.kvk.nl/geldzaken/belastingtarieven-2026/",
}


def _box1_tax(belastbaar: float) -> float:
    tax = 0.0
    lower = 0.0
    for upper, rate in BOX1_BRACKETS_2026:
        if belastbaar <= lower:
            break
        slice_top = min(belastbaar, upper)
        tax += (slice_top - lower) * rate
        lower = upper
    return tax


def income_tax_eenmanszaak(winst: float) -> float:
    """Indicatieve IB over winst uit onderneming (excl. heffingskortingen)."""
    if winst <= 0:
        return 0.0
    na_zelfstandigenaftrek = max(0.0, winst - ZELFSTANDIGENAFTREK_2026)
    belastbaar = na_zelfstandigenaftrek * (1 - MKB_WINSTVRIJSTELLING_2026)
    return _box1_tax(belastbaar)


def corporate_tax_bv(winst: float) -> float:
    """Indicatieve vennootschapsbelasting (BV)."""
    if winst <= 0:
        return 0.0
    if winst <= VPB_GRENS:
        return winst * VPB_LAAG
    return VPB_GRENS * VPB_LAAG + (winst - VPB_GRENS) * VPB_HOOG


def tax_indication(winst: float, legal_form: str) -> float:
    """Kies het juiste regime op basis van de rechtsvorm."""
    return (corporate_tax_bv(winst) if legal_form.upper() == "BV"
            else income_tax_eenmanszaak(winst))


def effective_rate(winst: float, legal_form: str) -> float:
    return tax_indication(winst, legal_form) / winst if winst > 0 else 0.0


# ---- Investeringsaftrek-berekeningen (indicatief) ------------------------
def kia_deduction(investering: float) -> float:
    """Kleinschaligheidsinvesteringsaftrek over één jaar-investeringsbedrag."""
    i = investering
    if i < KIA_MIN_INVESTERING or i > KIA_MAX_INVESTERING:
        return 0.0
    if i <= KIA_BAND1_TOP:
        return round(i * KIA_TARIEF, 2)
    if i <= KIA_BAND2_TOP:
        return KIA_FLAT
    return max(0.0, round(KIA_FLAT - KIA_AFBOUW * (i - KIA_BAND2_TOP), 2))


def eia_deduction(investering: float) -> float:
    """Energie-investeringsaftrek (alleen voor bedrijfsmiddelen op de Energielijst)."""
    return round(investering * EIA_TARIEF, 2) if investering >= EIA_DREMPEL else 0.0


def mia_deduction(investering: float) -> float:
    """Milieu-investeringsaftrek (max-tarief; categorie-afhankelijk)."""
    return round(investering * MIA_TARIEF_MAX, 2) if investering >= EIA_DREMPEL else 0.0


def marginal_rate(winst: float, legal_form: str) -> float:
    """Het tarief waartegen één euro extra aftrek effectief voordeel oplevert."""
    if legal_form.upper() == "BV":
        return VPB_HOOG if winst > VPB_GRENS else VPB_LAAG
    belastbaar = max(0.0, winst - ZELFSTANDIGENAFTREK_2026) * (1 - MKB_WINSTVRIJSTELLING_2026)
    rate = BOX1_BRACKETS_2026[-1][1]
    for upper, r in BOX1_BRACKETS_2026:
        if belastbaar <= upper:
            rate = r
            break
    # Aftrek werkt bij een IB-ondernemer door de MKB-winstvrijstelling heen.
    return round(rate * (1 - MKB_WINSTVRIJSTELLING_2026), 4)
