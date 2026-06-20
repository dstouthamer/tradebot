# 02 — Website-structuur & Sitemap
**Rol: WordPress-developer + SEO-specialist**

## 1. Uitgangspunten

- **Conversie-first:** elke pagina heeft één primaire CTA (aanvraag/WhatsApp/bellen) en die staat altijd zichtbaar.
- **SEO-architectuur:** hub-and-spoke. Dienstpagina's = hubs, lokale pagina's + blog = spokes die intern naar de hubs linken.
- **Flat & logisch:** max 3 klikken van homepage naar elke pagina. Korte, keyword-rijke URL's.
- **Mobile-first:** >70% van het verkeer is mobiel (mensen zoeken op een hete dag op hun telefoon).

## 2. Sitemap (boomstructuur)

```
[DOMEIN]/
│
├── / .......................................... Homepage
│
├── /mobiele-airco-huren/ ...................... Pillar / hoofd-dienst (belangrijkste rankingpagina)
│
├── /airco-huren/ .............................. Diensten-overzicht
│   ├── /airco-huren/particulier/ .............. Doelgroeppagina particulier
│   ├── /airco-huren/zakelijk/ ................. Doelgroeppagina zakelijk/kantoor
│   ├── /airco-huren/serverruimte/ ............. Doelgroeppagina serverruimte/IT
│   ├── /airco-huren/evenement/ ................ Doelgroeppagina evenement/horeca
│   └── /airco-huren/bouw-en-droging/ .......... Doelgroeppagina bouw/renovatie
│
├── /prijzen/ .................................. Tarieven & pakketten
├── /hoe-werkt-het/ ............................ Proces in 3-4 stappen
├── /capaciteit-berekenen/ ..................... BTU/kW-tool (lead-magnet + SEO)
│
├── /verhuur-in/ ............................... Locatie-hub (linkt naar alle steden)
│   ├── /verhuur-in/[stad-1]/ .................. Lokale landingspagina
│   ├── /verhuur-in/[stad-2]/
│   ├── /verhuur-in/[stad-3]/
│   └── ...  (zie 05 voor template)
│
├── /kennisbank/ ............................... Blog/contentcluster (SEO)
│   ├── /kennisbank/mobiele-airco-zonder-buisje/
│   ├── /kennisbank/hoeveel-kost-airco-huren/
│   ├── /kennisbank/airco-slaapkamer-tips/
│   └── ...
│
├── /over-ons/ ................................. Vertrouwen/EEAT
├── /reviews/ .................................. Klantbeoordelingen
├── /veelgestelde-vragen/ ...................... FAQ (rich snippets)
├── /contact/ .................................. Contact + aanvraagformulier
│
├── /offerte-aanvragen/ ........................ Conversie-landingspagina (Ads-bestemming)
├── /bedankt/ .................................. Thank-you page (conversie-tracking)
│
└── Footer/legal: /algemene-voorwaarden/  /privacybeleid/  /cookiebeleid/
```

## 3. URL-conventies

- Lowercase, woorden met koppelteken, geen stopwoorden waar mogelijk.
- Geen datums of categorieën in blog-URL's (`/kennisbank/onderwerp/`, niet `/2026/06/...`).
- Lokale pagina's: consistent patroon `/verhuur-in/[stad]/` — schaalbaar en herkenbaar.
- Vermijd URL-wijzigingen later; doe het nu goed (anders 301-redirects nodig).

## 4. Navigatie

**Hoofdmenu (max 6 items — keuzestress vermijden):**
`Airco huren ▾` · `Prijzen` · `Hoe werkt het` · `Verhuur in jouw regio ▾` · `Reviews` · `Contact`

- Plus prominente knop rechts: **"Aanvraag in 1 min ▸"** (afwijkende kleur).
- `Airco huren ▾` klapt uit naar de 5 doelgroeppagina's.
- `Verhuur in jouw regio ▾` toont top-steden + link naar volledige locatie-hub.

**Sticky elementen (altijd zichtbaar):**
- Mobiel: onderbalk met 3 knoppen — 📞 **Bellen** · 💬 **WhatsApp** · 📝 **Aanvraag**.
- Desktop: telefoonnummer + WhatsApp rechtsboven, sticky CTA bij scrollen.

**Footer:**
NAP-gegevens (Naam, Adres, Telefoon — identiek aan Google Business Profile voor lokale SEO), openingstijden, KvK/BTW, snelle links, dienstgebied (stedenlijst voor interne links), social, reviews-badge.

## 5. Paginastandaard (template per type)

### Dienst-/doelgroeppagina (conversie + SEO)
1. **Hero**: H1 met keyword + USP-subtekst + primaire CTA + vertrouwensbadges (reviews, "vandaag geleverd").
2. **Probleem/herkenning**: 2-3 zinnen die de pijn benoemen.
3. **Oplossing/aanbod**: wat krijg je, voor wie.
4. **USP-blok**: 3-4 iconen met voordelen.
5. **Hoe werkt het**: 3-4 stappen.
6. **Prijsindicatie + CTA**.
7. **Social proof**: reviews/logo's/cases.
8. **FAQ** (met FAQ-schema).
9. **Tweede CTA + formulier**.
10. Interne links naar relevante lokale pagina's + kennisbank.

### Lokale pagina
Zie [05 — Lokale SEO-pagina's](05-lokale-seo-paginas.md).

### Blog/kennisbank-artikel
H1 + intro met antwoord-vooraan (featured-snippet-optimalisatie), inhoudsopgave, 800-1.500 woorden, interne links naar dienstpagina's, CTA-blok halverwege en onderaan, FAQ-schema.

## 6. Interne linkstrategie

- **Homepage** linkt naar: pillar `/mobiele-airco-huren/`, 5 doelgroeppagina's, prijzen, top-3 steden.
- **Pillar-pagina** linkt naar: alle doelgroeppagina's + locatie-hub + capaciteit-tool.
- **Lokale pagina's** linken omhoog naar relevante doelgroeppagina + pillar; en naar 2-3 buur-steden (silo).
- **Blogartikelen** linken naar de meest relevante dienstpagina met keyword-rijke ankertekst.
- **Capaciteit-tool** is interne lead-magnet: linkt naar prijzen + aanvraag.

Doel: PageRank/autoriteit naar de commerciële pagina's sturen en thematische silo's bouwen die Google's begrip van relevantie versterken.

## 7. Pagina-prioriteit voor de bouw

| Prioriteit | Pagina's | Reden |
|-----------|----------|-------|
| P0 (week 1-2) | Home, pillar, prijzen, contact, offerte-aanvragen, bedankt | Conversie kan direct |
| P1 (week 2-3) | 5 doelgroeppagina's, hoe-werkt-het, FAQ, 5 lokale pagina's | Core SEO + segmenten |
| P2 (week 3-4) | Over ons, reviews, capaciteit-tool, locatie-hub | Vertrouwen + lead-magnet |
| P3 (doorlopend) | Extra lokale pagina's, kennisbank-artikelen | Schalen |
