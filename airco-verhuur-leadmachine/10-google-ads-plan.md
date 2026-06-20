# 10 — Google Ads-plan
**Rol: SEA-specialist**

> Google Ads levert leads vanaf dag 1 (terwijl SEO opbouwt) en is dé manier om hittegolf-pieken te oogsten. Doel: zoveel mogelijk **gekwalificeerde** leads onder de doel-CPL, met budget dat meebeweegt met het weer.

## 1. Strategie

- **Search-campagnes** op koopintentie ("mobiele airco huren [stad]") = hoofdmoot.
- **Geo-targeting** strak op dienstgebied (geen budget verspillen buiten leverbereik).
- **Weer-gestuurd budget**: schaal op bij voorspelde hitte, pauzeer/verlaag bij koel weer.
- **Bel- en formulier-conversies** beide tracken; bel-extensies prominent (spoed = bellen).
- **Snelle landingspagina's** met sterke CRO (zie 06) — Ads-kwaliteit ∩ conversie.

## 2. Campagnestructuur

```
ACCOUNT
├── Campagne: Search – Mobiele airco huren [merk/generiek]   (hoogste prioriteit)
│   ├── Adgroep: Mobiele airco huren (generiek)
│   ├── Adgroep: Airco huren + per dag/week/maand
│   └── Adgroep: Airco verhuur
│
├── Campagne: Search – Lokaal (per kernstad of stadsgroep)
│   ├── Adgroep: airco huren [stad 1]
│   ├── Adgroep: airco huren [stad 2]
│   └── ...
│
├── Campagne: Search – Zakelijk/Serverruimte (hogere waarde, eigen budget)
│   ├── Adgroep: airco huren kantoor/bedrijf
│   └── Adgroep: airco/noodkoeling serverruimte
│
├── Campagne: Search – Spoed (vandaag/spoed-keywords, hoogste bod)
│
├── Campagne: Performance Max (optioneel, na data) – assets + feed
│
└── Campagne: Display/Remarketing – retargeting sitebezoekers + oud-leads
```

Splits campagnes zo dat je **budget per intentie/waarde** kunt sturen (zakelijk en spoed mogen meer kosten dan particulier).

## 3. Keywords & matchtypes

- Start met **phrase** en **exact** match op kern-keywords (controle, minder verspilling).
- Voorbeelden: `"mobiele airco huren"`, `[airco huren amsterdam]`, `"airco huren kantoor"`, `"airco huren spoed"`.
- **Broad match** alleen later met goede conversiedata + smart bidding + strakke negatives.
- **Negatieve keywords** (essentieel — bespaart budget): `kopen`, `tweedehands`, `marktplaats`, `reparatie`, `installateur` (tenzij relevant), `vacature`, `gratis`, `handleiding`, `zelf maken`, `split airco` (als je alleen mobiel verhuurt), merknamen die je niet voert, plaatsen buiten gebied.

## 4. Advertentieteksten (RSA — Responsive Search Ads)

**Koppen (mix, 10-15 stuks):**
- Mobiele Airco Huren in [Stad]
- Vandaag Besteld, Vandaag Geleverd
- Airco Huren v.a. €XX p/w
- Incl. Bezorging & Installatie
- Per Dag, Week of Maand
- Reactie Binnen 5 Minuten
- ⭐ 4,9/5 — [X] Reviews
- Spoed? Bel Direct [TELEFOON]
- Koel Slapen Vanaf Vanavond
- Zakelijk Huren met Factuur

**Beschrijvingen:**
- Huur een mobiele airco in [Stad]. Wij bezorgen, installeren én halen op. Vraag nu aan.
- Te warm thuis of op kantoor? Binnen 24 uur verkoeling. Transparante prijzen, geen verrassingen.
- Flexibel huren per dag, week of maand. Bel of app voor directe beschikbaarheid.

**Pin** waar nodig (bv. stad in kop 1) om relevantie/kwaliteit hoog te houden.

## 5. Advertentie-extensies (assets)

- **Bel-extensie** (cruciaal — spoed → bellen), met belrapportage/conversie.
- **Sitelinks**: Prijzen · Hoe werkt het · Zakelijk · Reviews.
- **Highlight-extensies**: Installatie inbegrepen · Levering binnen 24u · Flexibele huur · Lokale service.
- **Snippet-extensies**: Doelgroepen (Particulier, Kantoor, Serverruimte, Evenement).
- **Locatie-extensie** (indien GBP gekoppeld).
- **Leadformulier-extensie** (optioneel).

## 6. Landingspagina's voor Ads

- Stuur **niet** naar de homepage. Stuur naar de relevante dienst-/lokale pagina of een dedicated `/offerte-aanvragen/`.
- Match tussen advertentietekst en landingspagina (message match) → hogere kwaliteitsscore + conversie.
- Boven de vouw: keyword in H1, prijs/USP, formulier + bel/WhatsApp. Snel laden (zie 11).
- Aparte landings per segment (zakelijk vs. particulier vs. spoed).

## 7. Biedstrategie & budget

- **Start:** handmatig of "Klikken maximaliseren" met bodlimiet om data te verzamelen.
- **Na ~15-30 conversies:** over naar **Doel-CPA / Conversies maximaliseren** (smart bidding).
- **Budget weergestuurd:**
  - Koel/normaal: basis-budget laag, vooral zakelijk/serverruimte (weeronafhankelijk).
  - Hitte voorspeld (>27°C in [REGIO]): budget en doel-CPA omhoog, particulier + spoed agressief.
  - Dagdelen/ad-schedule: pas biedingen aan op wanneer mensen zoeken (avond/ochtend hitte).
- **CPL-doel**: zie 01 (richt < €12-25 afhankelijk van fase/segment).

## 8. Weer-trigger workflow (concurrentievoordeel)

```
Monitor weersverwachting [REGIO] (KNMI/weather API)
IF max_temp_komende_3_dagen >= 27°C:
    verhoog dagbudget piekcampagnes (x2–x4)
    verhoog doel-CPA / biedingen
    activeer "Spoed"-campagne
    stuur hittegolf-mailing naar lijst (zie 08)
ELSE:
    basisbudget, focus zakelijk/serverruimte
```
Kan handmatig (dagelijkse weercheck) of geautomatiseerd via scripts/Make + Google Ads API.

## 9. Conversietracking (Ads-specifiek)

- Importeer conversies: formulier-submit (`/bedankt/`), bel-conversies (bel-extensie + on-site klik-naar-bellen), WhatsApp-klik.
- Tel **gekwalificeerde** leads, niet alleen klikken. Idealiter: offline conversie-import vanuit CRM (geboekt = €-waarde terug naar Ads) → smart bidding optimaliseert op échte klanten, niet op formuliertjes.
- Koppel GA4 + Google Ads. Zie 12.

## 10. Optimalisatie-ritme

| Frequentie | Actie |
|-----------|-------|
| Dagelijks (seizoen) | Weer-budget bijstellen, zoektermen → negatives, biedingen |
| Wekelijks | Zoektermenrapport, advertentie-prestaties (pauzeer slechte RSA-assets), CPL per campagne |
| Maandelijks | Landingspagina-conversie, biedstrategie evalueren, budgetverdeling per segment, offline-conversiewaarde |
| Seizoenseinde | Account "winterstand": pauzeer particulier, behoud zakelijk + remarketing |

## 11. Veelgemaakte fouten vermijden

- ❌ Naar homepage sturen → ✅ dedicated landingspagina.
- ❌ Alleen broad match zonder negatives → ✅ phrase/exact + strakke negatives.
- ❌ Geen bel-tracking → ✅ bel-conversies meten (spoedmarkt).
- ❌ Vast budget jaarrond → ✅ weergestuurd schalen.
- ❌ Optimaliseren op klikken/leads i.p.v. klanten → ✅ offline-conversies uit CRM.
- ❌ Buiten leverbereik adverteren → ✅ strakke geo-targeting.
