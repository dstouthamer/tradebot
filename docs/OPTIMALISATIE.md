# Legale belastingoptimalisatie

> **De grens.** De agent verlaagt je **belasting**, nooit je **opgegeven omzet**. Omzet
> verbergen/minder opgeven, kosten verzinnen of backdaten = fraude → de compliance-agent
> blokkeert dat (ROOD) en biedt een legaal alternatief. "Scherp tot aan de grens, niet
> eroverheen" — verdedigbaar mits goed onderbouwd.

## De optimalisatie-scan

Typ in de chat **"bespaar belasting"** (of: optimaliseer / aftrekposten / minder
belasting). De `OptimizationAgent` (`boekhouder/agents/optimization.py`) geeft een
geprioriteerde lijst kansen — sector-, winst- en seizoensbewust:

| Kans | Voor wie | Zone |
|---|---|---|
| Alle aftrekposten compleet maken | iedereen | 🟢 |
| **EIA** (Energie-investeringsaftrek, ~40%) | verduurzaming/installatie | 🟠 (RVO-melding) |
| **MIA/Vamil** (milieu, tot ~45% / 75% afschrijven) | verduurzaming | 🟠 (RVO-melding) |
| Ondernemersaftrek + MKB-winstvrijstelling | eenmanszaak | 🟢 |
| KIA (28%, investering €2.901–€398.236) | bij investeringen | 🟢 |
| Timing rond jaareinde (kosten/investeringen) | iedereen (sterker in Q4) | 🟢/🟠 |
| Oudedagsvoorziening (lijfrente/pensioen) | iedereen | 🟠 |
| Oninbare facturen afboeken → btw terug | iedereen | 🟢 |
| KOR (btw-vrijstelling) | omzet < €20.000 | 🟠 |
| Overweeg BV | eenmanszaak, winst ≳ €100.000 | 🟠 |

Voor jouw sector (verduurzaming/installatie) is **EIA/MIA/Vamil** vaak het grootste,
volledig legale voordeel.

## Concrete bedragen bij een investering

Noem een bedrag, dan rekent de agent het voordeel uit. Bijv. *"ik wil investeren in
zonnepanelen voor 20000"*:

```
Fiscaal voordeel van een investering van €20.000,00 (excl. btw)
* KIA: €5.600,00   * EIA (energie, ~40%): €8.000,00
* Totale extra aftrek: €13.600,00
* Geschatte belastingbesparing (≈31% marginaal): €4.239,12
* Btw terugvorderbaar (21%): €4.200,00
```

KIA is getrapt, EIA/MIA gelden niet samen op hetzelfde middel, en de besparing rekent
met je marginale tarief (eenmanszaak via de MKB-winstvrijstelling, of vpb bij een BV).

## Proactief

- De agent geeft **uit zichzelf** signalen via `proactive_alerts`: jaareinde-timing
  ("nog X dagen tot 31-12 — investeer dit jaar nog"), BV-omslag bij hoge winst, en een
  RVO-reminder voor verduurzamingsinvesteringen.
- De **prognose** sluit af met een tip om de scan te draaien.
- Onderwerpen met 🟠 dragen altijd "boekhouder-check"; bedragen/regelingen zijn
  indicatief (peiljaar 2026) — laat ze door je fiscalist toetsen.

## Bronnen

- EIA/MIA/Vamil — RVO: https://www.rvo.nl/subsidies-financiering/eia · /mia-vamil
- Ondernemersaftrek/MKB/KIA — KVK: https://www.kvk.nl/geldzaken/belastingtarieven-2026/
- KOR — Belastingdienst
