# 03 — SEO-plan & Keywords
**Rol: SEO-specialist**

## 1. Strategie in één zin

Domineer de **commerciële zoekintentie** ("mobiele airco huren [stad]") via lokale landingspagina's + sterke dienstpagina's, voed die met een **informatief contentcluster** dat featured snippets pakt en autoriteit opbouwt, en versterk alles met **lokale SEO (Google Business Profile) + reviews + links.**

## 2. Keyword-onderzoek (clusters)

> Volumes wisselen sterk per seizoen en regio. Valideer met Google Keyword Planner / Search Console / Ahrefs. Onderstaande indeling is op intentie, niet op exact volume.

### Cluster A — Commercieel kern (hoogste prioriteit)
Intentie: nu huren. Hier zit het geld.
- mobiele airco huren
- airco huren
- airco verhuur
- mobiele airco huren [stad/regio]
- airco huren [stad]
- airco huren per dag / per week / per maand
- airco huren spoed / vandaag
- airconditioning huren

### Cluster B — Doelgroep/segment
- airco huren kantoor / bedrijf / zakelijk
- airco huren serverruimte / serverkast koelen huren
- airco huren slaapkamer
- airco huren evenement / festival / tent
- mobiele koeling huren horeca
- noodkoeling huren / airco huren bij storing

### Cluster C — Prijs/beslissing (hoge koopintentie)
- airco huren prijs / kosten / tarief
- wat kost mobiele airco huren
- mobiele airco huren goedkoop
- airco huren of kopen

### Cluster D — Informatief (top-of-funnel, snippet-magneet)
- mobiele airco zonder buisje (en: werkt dat?)
- hoeveel kW/BTU airco voor [x] m²
- mobiele airco verbruik / stroomverbruik
- mobiele airco slaapkamer tips / geluid
- hoe werkt een mobiele airco
- airco of ventilator

### Cluster E — Lokaal (schaalbaar, zie 05)
- mobiele airco huren + [elke stad/dorp in dienstgebied]

## 3. Keyword → pagina-mapping

| Pagina | Primair keyword | Secundaire keywords |
|--------|----------------|---------------------|
| Homepage | mobiele airco huren [REGIO] | airco verhuur, airco huren |
| `/mobiele-airco-huren/` (pillar) | mobiele airco huren | airconditioning huren, airco verhuur |
| `/airco-huren/zakelijk/` | airco huren kantoor | airco huren bedrijf, zakelijk |
| `/airco-huren/serverruimte/` | airco huren serverruimte | serverkast koelen, noodkoeling |
| `/airco-huren/particulier/` | airco huren slaapkamer | mobiele airco woning |
| `/airco-huren/evenement/` | airco huren evenement | mobiele koeling festival, tent |
| `/prijzen/` | mobiele airco huren prijs | airco huren kosten, tarief |
| `/capaciteit-berekenen/` | hoeveel kW airco voor m² | btu berekenen airco |
| `/verhuur-in/[stad]/` | mobiele airco huren [stad] | airco huren [stad] |
| Kennisbank-artikelen | per Cluster D-onderwerp | long-tail varianten |

**Regel:** één primair keyword per pagina, geen kannibalisatie. Als twee pagina's om hetzelfde keyword strijden → samenvoegen of differentiëren op intentie.

## 4. On-page SEO-checklist (per pagina)

- [ ] **Title tag** (≤60 tekens): `Mobiele Airco Huren [Stad] | Vandaag Geleverd | [BEDRIJFSNAAM]`
- [ ] **Meta description** (≤155 tekens, met USP + CTA + keyword) — beïnvloedt CTR.
- [ ] **Eén H1** met primair keyword, natuurlijk geformuleerd.
- [ ] Logische H2/H3-structuur met secundaire keywords.
- [ ] Keyword in eerste 100 woorden + in URL.
- [ ] Interne links (zie 02) met beschrijvende ankertekst.
- [ ] Geoptimaliseerde afbeeldingen (WebP, alt-tekst met keyword, comprimeren).
- [ ] **Schema-markup** (zie §6).
- [ ] Unieke content (geen gedupliceerde lokale pagina's — zie 05).
- [ ] CTA + telefoonnummer zichtbaar.
- [ ] Mobielvriendelijk, Core Web Vitals groen.

## 5. Technische SEO

- **Core Web Vitals**: LCP <2,5s, INP <200ms, CLS <0,1. (Zie 11 voor caching/CDN/lazy-load.)
- **HTTPS** overal, één canonieke versie (https + non-www of www — kies één, redirect de rest).
- **XML-sitemap** (Yoast/RankMath) + indienen in Search Console.
- **Robots.txt** netjes; thank-you/bedankt-pagina op `noindex`.
- **Schone URL-structuur** + breadcrumbs (met BreadcrumbList-schema).
- **Geen broken links / 404's**; 301-redirects voor wijzigingen.
- **Hreflang** niet nodig (NL-only), tenzij ook BE bediend wordt.
- **Gestructureerde data** valideren met Rich Results Test.
- **Mobile-first indexing**-proof: identieke content mobiel/desktop.

## 6. Schema-markup (gestructureerde data)

| Schema | Waar | Effect |
|--------|------|--------|
| `LocalBusiness` (+ `HVACBusiness`) | Home/contact/lokale pagina's | Lokale knowledge panel, NAP, openingstijden |
| `Service` / `Product` (+ `Offer`, prijs) | Dienst/prijspagina's | Prijs-rich-snippets |
| `FAQPage` | FAQ + dienstpagina-FAQ's | Uitklap-snippets in SERP (meer ruimte) |
| `AggregateRating` / `Review` | Reviews-pagina, home | Sterren in zoekresultaat → hogere CTR |
| `BreadcrumbList` | Alle pagina's | Nette SERP-breadcrumbs |
| `WebSite` + `SearchAction` | Sitebreed | Sitelinks searchbox |

## 7. Lokale SEO (essentieel — zie ook 05)

1. **Google Business Profile** volledig: categorie "Airconditioning-verhuurservice"/"Verhuurbedrijf", dienstgebied (geen winkel? stel servicegebied in), foto's units + bus + team, openingstijden, producten/diensten met prijzen, UTM-gelinkte website.
2. **NAP-consistentie**: exact dezelfde Naam/Adres/Telefoon op site, GBP, en alle vermeldingen.
3. **Lokale citaties**: bedrijvengidsen (Telefoonboek, Detelefoongids, Yelp, branchedirectories, lokale ondernemersverenigingen).
4. **Reviews**: structureel verzamelen (zie 08 voor automatische review-vraag). Reageer op álle reviews. Mik op meer + hogere score dan concurrenten.
5. **GBP-posts**: wekelijks (aanbod, hittegolf-actie) — houdt profiel actief.
6. **Lokale landingspagina's** met unieke content per gebied (zie 05).

## 8. Contentkalender (eerste kwartaal)

| Week | Type | Onderwerp (voorbeeld) | Doel-keyword |
|------|------|----------------------|--------------|
| 1 | Pillar | Mobiele airco huren — complete gids | mobiele airco huren |
| 2 | Lokaal x3 | Top-3 steden dienstgebied | airco huren [stad] |
| 3 | Blog | Mobiele airco zonder buisje — kan dat? | mobiele airco zonder buisje |
| 4 | Blog | Wat kost een mobiele airco huren? | airco huren prijs |
| 5 | Lokaal x3 | Volgende 3 steden | airco huren [stad] |
| 6 | Blog | Hoeveel kW airco heb je nodig per m²? | kw airco berekenen |
| 7 | Blog | Airco huren of kopen? | airco huren of kopen |
| 8 | Lokaal x3 | Volgende 3 steden | airco huren [stad] |
| 9 | Blog | Beste mobiele airco voor de slaapkamer | airco slaapkamer |
| 10 | Doelgroep | Serverruimte koelen — noodkoeling | airco serverruimte |
| 11 | Lokaal x3 | Volgende 3 steden | |
| 12 | Blog | Mobiele airco stroomverbruik & kosten | mobiele airco verbruik |

Tempo daarna: 2-4 stukken/maand. Prioriteer lokale pagina's vóór en tijdens seizoen.

## 9. Linkbuilding (autoriteit)

- **Lokaal/relevant**: verhuurplatforms, branchegidsen, lokale nieuwssites (pers bij hittegolf — "tekort aan airco's" is een nieuwshaakje), samenwerkingen met installateurs/eventbureaus/bouwbedrijven (wederzijdse verwijzing).
- **Digital PR**: data/tip-artikel ("zo overleef je de hittegolf") pitchen aan regionale media.
- **Reviews & vermeldingen** op verhuurmarktplaatsen.
- **Leverancier-/partnerpagina's**: laat je vermelden door merken/leveranciers van de units.
- Vermijd gekochte spamlinks — focus op relevantie en lokaliteit.

## 10. Meten & rapporteren (SEO)

Maandelijks via Search Console + GA4 + rank-tracker:
- Posities top-keywords (per cluster), klikken, vertoningen, CTR.
- Organische sessies → leads (doel-conversies).
- Geïndexeerde pagina's & dekkingsfouten.
- Top-landingspagina's & nieuwe winnende queries → nieuwe content-ideeën.
- Backlink-groei & Domain Rating-trend.

Zie [12 — Conversieplan](12-conversieplan-meten-optimaliseren.md) voor de volledige meetopzet.
