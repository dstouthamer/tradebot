# 12 — Conversieplan: Meten & Optimaliseren
**Rol: CRO-specialist + projectmanager**

> Wat je niet meet, kun je niet verbeteren. Dit document bindt alles samen: van klik tot betaalde verhuurklant, met een vaste optimalisatie-cyclus.

## 1. De volledige funnel (meetpunten)

```
VERTONING (Google SEO/Ads)
   │  ← CTR
KLIK / BEZOEK
   │  ← bounce, scroll, paginaduur
LANDINGSPAGINA-ENGAGEMENT
   │  ← form-start, klik bel/WhatsApp
LEAD (aanvraag/bel/app)            ◄── conversieratio bezoeker→lead
   │  ← reactietijd
CONTACT GELEGD
   │  ← kwalificatieratio
GEKWALIFICEERDE LEAD
   │  ← offerte→ja
GEBOEKT
   │  ← levering
VERHUURKLANT  ───►  REVIEW + HERHAAL/SEIZOEN
```

Elke pijl = een conversieratio die je meet en verbetert.

## 2. Kern-KPI's & doelen

| KPI | Definitie | Doel |
|-----|-----------|------|
| Bezoeker → lead | leads / sessies | 3-6% (site), hoger op Ads-landings |
| **Reactietijd** | tijd lead → eerste menselijk contact | < 5 min |
| Lead → gekwalificeerd | passende leads / totaal | > 70% |
| Offerte → geboekt | boekingen / offertes | > 40% |
| **Lead → klant** | klanten / leads | 25% → 35%+ |
| CPL (Ads) | adspend / leads | < €12-25 |
| CAC | totale kosten / klant | < marge per verhuur |
| ROAS | omzet / adspend | > [doel] |
| Reviewscore / aantal | GBP-rating | > concurrent |

## 3. Tracking-events (implementatie in GA4/GTM — zie 11)

| Event | Trigger | Waarvoor |
|-------|---------|----------|
| `start_form` | eerste veldfocus | funnel-afhaakpunt |
| `generate_lead` | formulier-submit (/bedankt/) | hoofdconversie |
| `click_to_call` | klik op `tel:`-link | bel-leads (groot in spoedmarkt) |
| `click_whatsapp` | klik op wa.me-knop | WhatsApp-leads |
| `view_pricing` | bezoek /prijzen/ | koopintentie-signaal |
| `scroll_75` | diepe scroll | engagement |

Koppel: GA4 ↔ Google Ads ↔ Search Console. Idealiter **offline conversie-import** uit CRM (geboekt/omzet terug naar Ads) zodat smart bidding op échte klanten optimaliseert, niet op formuliertjes.

## 4. Dashboards

**Wekelijks operationeel dashboard (sales/PM):**
- Leads totaal + per bron/segment + per device.
- Gemiddelde reactietijd (alarm bij >5 min).
- Pipeline-stand & conversie per stage (uit CRM, zie 09).
- CPL + adspend + boekingen + omzet vs. doel.

**Maandelijks strategisch dashboard (PM):**
- SEO: posities top-keywords, organisch verkeer, nieuwe rankende pagina's.
- Funnel-conversies maand-op-maand + seizoenscorrectie.
- Win/verlies-redenen (uit CRM).
- ROI per kanaal (SEO vs. Ads vs. lokaal vs. referral).
- Reviewgroei.

## 5. Attributie & bron-inzicht

- UTM-tagging op alle Ads/e-mail/GBP-links.
- Vraag bij telefonische leads "hoe heb je ons gevonden?" → vul bron in CRM (telefoon-leads zijn anders lastig te attribueren).
- Gebruik data-driven attributie in GA4/Ads.
- Let op: veel leads zien meerdere touchpoints (SEO + Ads + reviews) — beoordeel kanalen niet puur last-click.

## 6. Optimalisatie-cyclus (maandelijks ritueel)

```
1. METEN     → trek funnel-data + CRM-conversies + verliesredenen.
2. DIAGNOSE  → waar lekt de funnel het meest? (bv. veel leads, lage close;
               of veel bezoek, weinig leads; of trage reactie.)
3. HYPOTHESE → "Als we X veranderen, stijgt conversie Y omdat Z."
4. TEST      → A/B-test (zie 06) of procesverandering (sneller bellen, beter script).
5. EVALUEER  → significant beter? Uitrollen. Niet? Verwerpen, volgende.
6. HERHAAL.
```

Prioriteer verbeteringen op **impact × gemak** (ICE/PIE-scoring).

## 7. Diagnose-gids (veelvoorkomende lekken → actie)

| Symptoom | Waarschijnlijke oorzaak | Actie |
|----------|------------------------|-------|
| Veel verkeer, weinig leads | Zwakke CRO / trage pagina / geen prijs | Zie 06 + 11: CTA's, vertrouwen, snelheid, prijs tonen |
| Veel leads, lage close | Trage reactie / zwakke sales / prijs | Zie 07/08: <5 min bellen, scripts, bezwaren |
| Hoge CPL | Brede keywords / slechte landings | Zie 10: negatives, message match, biedingen |
| Hoog verkeer, lage CTR in SERP | Zwakke titles/meta / geen sterren | Zie 03: meta's herschrijven, review-schema |
| Leads buiten gebied | Geo/targeting te ruim | Strakkere geo (Ads) + dienstgebied duidelijk (site) |
| Veel "weer koelde af"-verlies | Te trage opvolging op piekdag | Snellere close + reserveer-aanbod (zie 07) |
| Lage rankings | Dunne lokale pagina's / techniek | Zie 05/11: uniek maken, CWV, links |

## 8. Reactiesnelheid bewaken (de #1 hefboom)

- Log timestamp van elke lead + eerste contact in CRM.
- Alarm/escalatie als een lead >5 min onbeantwoord is.
- Wekelijkse review van trage opvolgingen → wat ging mis?
- Buiten openingstijden: automatische bevestiging + duidelijke "we bellen je morgen om [tijd]" + WhatsApp-opt-in. Overweeg avond/weekend-bereikbaarheid in hoogseizoen (daar liggen de hete dagen).

## 9. Seizoens-/weereffect in de meting

- Normaliseer conversiedata voor temperatuur (een slechte conversieweek kan gewoon een koele week zijn).
- Houd een "graaddagen vs. leads"-verband bij → voorspel capaciteit en budget.
- Vergelijk year-over-year, niet alleen maand-op-maand.

## 10. Continu verbeteren — 90-dagen prioriteiten

**Maand 1:** tracking waterdicht, reactietijd <5 min borgen, eerste A/B-test formulier.
**Maand 2:** landingspagina-conversie optimaliseren, Ads-negatives + biedingen, reviews actief verzamelen.
**Maand 3:** offline-conversie-import naar Ads, lokale pagina's uitbreiden o.b.v. winnende queries, sales-script bijschaven op verliesredenen.
**Daarna:** elke maand de optimalisatie-cyclus (§6) draaien op het grootste funnel-lek.

---

## Slot — hoe alles samenwerkt

1. **SEO (03/05) + Ads (10)** trekken gericht verkeer.
2. **Website + CRO (02/04/06/11)** zet bezoekers om in leads.
3. **Automation (08) + CRM (09)** zorgt dat geen lead wacht en alles wordt opgevolgd.
4. **Sales (07)** zet leads om in betalende verhuurklanten — snel.
5. **Meten (12)** vindt het zwakste punt en de cyclus verbetert het.
6. **Tevreden klant → review → betere SEO/conversie → meer leads.** Het vliegwiel draait.

**De winstfactor in deze markt blijft: snelheid.** Sneller ranken, sneller laden, sneller reageren, sneller closen. Wie het snelst is bij een zwetende klant op een hete dag, wint de verhuur.
