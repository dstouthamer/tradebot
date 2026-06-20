# Prognoses & belastingindicatie

De prognose-agent (`boekhouder/agents/forecast.py`) geeft een vooruitblik op basis van
je **geïmporteerde banktransacties** (historisch netto per maand) en je **geboekte
omzet/kosten**. Het verzint niets: bij te weinig data zegt het dat en vraagt het om
import.

## Wat je krijgt

- **Cashflow:** gemiddelde netto per maand en de verwachte netto over 30/60/90 dagen.
- **Btw-reservering:** te reserveren btw per aangifteperiode (maand/kwartaal/jaar uit je
  bedrijfsprofiel), berekend als verschuldigde minus voorbelasting.
- **Winst- en belastingindicatie:** bracket-gebaseerd, geen platte aanname.

## Belastingtarieven (peiljaar 2026, met bron)

Alle waarden staan in `boekhouder/domain/tax_rates.py` — één auditbare plek, met
geldigheidsjaar en bronvermelding (zoals de masterprompt voor fiscale regels eist).

| Onderdeel | 2026 | Bron |
|---|---|---|
| Btw hoog / laag | 21% / 9% (ongewijzigd) | Belastingdienst |
| Box 1 schijf 1 (t/m €38.883) | 35,70% | MKB Servicedesk |
| Box 1 schijf 2 (€38.883–€79.137) | 37,56% | MKB Servicedesk |
| Box 1 schijf 3 (vanaf €79.137) | 49,50% | MKB Servicedesk |
| Zelfstandigenaftrek | €1.200 (→ €900 in 2027) | KVK / Countus |
| MKB-winstvrijstelling | 12,7% | KVK |
| KIA | 28% bij investering €2.901–€398.236 | KVK / Moore DRV |
| Vpb (BV) | 19% t/m €200.000, 25,8% daarboven | Belastingdienst |

**Eenmanszaak:** belastbaar = (winst − zelfstandigenaftrek) × (1 − 12,7%), daarna de
box 1-schijven. **BV:** vennootschapsbelasting in twee schijven.

## Belangrijke beperkingen

- **Indicatief.** Heffingskortingen (algemene heffingskorting, arbeidskorting) en
  persoonlijke omstandigheden zijn **niet** meegenomen — de werkelijke aanslag valt
  meestal lager uit. De agent zet hier altijd "boekhouder-check: ja" bij en gebruikt
  "verdedigbaar mits onderbouwd", nooit "veilig".
- Tarieven zijn een momentopname (juni 2026). Controleer ze jaarlijks; pas ze op één
  plek aan in `tax_rates.py`.

## Bronnen

- Box 1-schijven 2026 — MKB Servicedesk:
  https://www.mkbservicedesk.nl/belastingen/inkomstenbelasting/belastingschijven-box-1
- Zelfstandigenaftrek & MKB-winstvrijstelling & KIA 2026 — KVK:
  https://www.kvk.nl/geldzaken/belastingtarieven-2026/
- Vennootschapsbelasting 2026 — Belastingdienst:
  https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/winst/vennootschapsbelasting/veranderingen-vennootschapsbelasting-2026/veranderingen-vennootschapsbelasting-2026
