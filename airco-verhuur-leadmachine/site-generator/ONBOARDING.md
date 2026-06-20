# ONBOARDING.md — interview-draaiboek voor de AI-agent

**Doel:** een nieuwe koper krijgt binnen één gesprek een complete, live
leadmachine. De agent **interviewt de koper**, vult de config in, genereert
de site, laat de preview zien en publiceert. De koper hoeft niets technisch
te doen.

> Dit is het script dat de verkopende partij meelevert. De agent leest dit,
> stelt de vragen, en is daarna klaar. Niets hier zelf invullen of verzinnen —
> **altijd de koper vragen**. Stel onbekende velden niet zomaar in; bij twijfel
> doorvragen.

---

## Werkwijze van de agent (stap voor stap)

1. **Begroet** de koper en leg in 2 zinnen uit wat er gaat gebeuren:
   "Ik stel je een paar vragen over je bedrijf en product. Daarna staat je
   complete vindbare website met leadformulier klaar. Klaar? We beginnen."
2. **Interview** de koper met de vragenblokken hieronder. Stel vragen in
   kleine groepjes, niet allemaal tegelijk. Bevestig wat je invult.
3. **Genereer suggesties** voor copy (USP's, segmenten, FAQ, tagline) op basis
   van de antwoorden, en **laat de koper ze goedkeuren of bijschaven**.
4. Schrijf de config naar `config.<klantnaam>.yaml` (kopie van
   `config.template.yaml`, ingevuld).
5. Draai `python generate.py config.<klantnaam>.yaml`.
6. Los alle punten op die `validate_config` / de generator meldt.
7. Laat de koper `build/preview/home.html` bekijken; verwerk feedback.
8. **Vraag toestemming** en publiceer (`python wp_publish.py config.<klantnaam>.yaml`,
   met de WordPress-gegevens van de koper) — of lever het importbestand op.

---

## De vragen (in deze volgorde)

### Blok 1 — Bedrijf
- Wat is je bedrijfsnaam?
- Wat is (of wordt) je website-adres (domein)?
- Op welk telefoonnummer mogen klanten je bereiken? *(agent leidt
  `phone_link` internationaal af, bv. 085-1234567 → +31851234567)*
- Wat is je WhatsApp-nummer? *(internationaal zonder +, bv. 31612345678)*
- Op welk e-mailadres wil je aanvragen ontvangen? *(wordt `lead.to_email`
  én meestal `business.email`)*
- In welk gebied/welke regio werk je?
- Wat is je bedrijfsadres? *(voor lokale SEO; mag weggelaten als de koper geen
  bezoekadres heeft — gebruik dan servicegebied)*
- KvK-nummer?
- Heb je al reviews? Zo ja: gemiddelde score en aantal. *(alleen invullen als
  het klopt — nooit verzinnen)*
- Wat zijn je openingstijden / bereikbaarheid?

### Blok 2 — Product / dienst
- Wat verhuur/verkoop/lever je precies? *(→ `noun`, `noun_plural`)*
- Doe je het "huren", "kopen" of "laten installeren"? *(→ `verb`, `verb_noun`)*
- Wat is het belangrijkste voordeel voor de klant in één zin? *(→ `what_you_offer`)*
- Welk probleem lost het op? *(→ `pain`)*
- Wat beloof je de klant (snelheid, ontzorging)? *(→ `promise`)*
- Vanaf welke prijs, en per wat? *(→ `price_from`, `price_unit`)*
- Wat is een passende pakkettenindeling? *(→ `packages`: naam, voor wie,
  inhoud, prijs — vraag er 2-4)*

### Blok 3 — Doelgroepen (segmenten → eigen pagina's)
- Voor welke soorten klanten/situaties is dit bedoeld?
  *(bv. particulier, kantoor, serverruimte, evenement)*
- Per segment: korte beschrijving + 2-3 concrete voordelen + de call-to-action.
  *(De agent maakt hiervan `segments`-items met `slug`, `name`, `h1`, `intro`,
  `bullets`, `cta`. H1 mag {region} bevatten.)*

### Blok 4 — Vertrouwen
- 3-4 USP's (waarom bij jou?). *(→ `usps`, met een passend emoji-icoon)*
- Een korte "over ons"-tekst (of antwoorden waaruit de agent die opstelt).
- Eventuele echte klantreviews (naam, plaats, tekst). *(alleen echte —
  anders leeg laten)*

### Blok 5 — Veelgestelde vragen
- Wat vragen klanten het vaakst? *(minstens 4 → `faq`. De agent vult aan met
  logische vragen over levertijd, prijs, installatie, garantie — laat de koper
  de antwoorden bevestigen.)*

### Blok 6 — Werkgebied (lokale SEO — de groeimotor)
- In welke plaatsen lever/werk je? *(Vraag de belangrijkste steden eerst,
  daarna omliggende plaatsen. Hoe meer plaatsen, hoe meer vindbaarheid.)*
- Per plaats (kort): typische levertijd en 2-3 buurplaatsen.
  *(→ `cities`-items met `name`, `slug`, `neighborhoods`, `delivery_time`,
  `neighbors`. De agent maakt per stad unieke tekst — nooit identieke
  doorplak-pagina's, zie `../05-lokale-seo-paginas.md`.)*

### Blok 7 — Stijl & afronding
- Heb je huisstijlkleuren? *(→ `brand.primary_color`, `accent_color`)*
- Een pakkende slogan? *(→ `brand.tagline`; anders stelt de agent er een voor)*
- Korte SEO-haak voor titels (bv. "Vandaag Geleverd")? *(→ `copy.seo_hook` e.d.)*

### Blok 8 — Leads laten binnenkomen (eenmalig)
- Leg uit: aanvragen komen via een gratis dienst binnen op het opgegeven
  e-mailadres. Vraag de koper een gratis key te maken op
  <https://web3forms.com> en geef die door. *(→ `lead.web3forms_access_key`)*
- Heeft de koper al WordPress + hosting? Zo ja, vraag (veilig) om de
  WordPress-gegevens voor publicatie via `wp_publish.py`. Zo nee, lever het
  `build/wordpress-import.xml` op met de importinstructies uit de README.

---

## Slimme defaults & regels

- **Niets verzinnen over feiten** (reviews, KvK, prijzen, openingstijden) —
  altijd vragen.
- **Wel mogen** voorstellen: tagline, USP-formuleringen, FAQ-aanvullingen,
  segment- en stadsteksten — maar laat de koper ze goedkeuren.
- `slug` afleiden uit de naam (kleine letters, koppeltekens, geen accenten).
- `phone_link` en `whatsapp` netjes internationaal formatteren.
- `to_email` = `business.email` tenzij de koper iets anders wil.
- Laat de koper kiezen: **direct publiceren** (REST API) of **importbestand**
  ontvangen.
- Eindig pas als `validate_config` geen problemen meer meldt.

## Wil je het zonder agent?

Een koper kan ook zelf het interview doen via de terminal:
```bash
python intake.py
```
Dat stelt dezelfde kernvragen en schrijft een werkende config.
