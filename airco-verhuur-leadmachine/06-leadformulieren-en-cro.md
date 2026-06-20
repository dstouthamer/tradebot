# 06 — Leadformulieren & Conversieoptimalisatie (CRO)
**Rol: CRO-specialist**

## 1. Conversiefilosofie

Een bezoeker op een hete dag wil **nú** een oplossing. Elke seconde wrijving = verloren lead. Principes:
- **Meerdere conversiepaden**: bellen, WhatsApp én formulier — laat de bezoeker kiezen.
- **Minimale frictie**: vraag alleen wat je nu nodig hebt om terug te bellen.
- **Urgentie + geruststelling**: "reactie binnen 5 minuten" + "vrijblijvend".
- **Altijd zichtbare CTA**: sticky knoppen, geen doodlopende pagina's.

## 2. De conversiepaden (in volgorde van snelheid voor de klant)

| Pad | Wanneer | Knop | Doel |
|-----|---------|------|------|
| 📞 Bellen | Hoogste urgentie, serverruimte, spoed | Sticky, klikbaar nummer | Directe close mogelijk |
| 💬 WhatsApp | Mobiel, snel, laagdrempelig | Sticky + prefilled bericht | Snelle dialoog, opvolgbaar |
| 📝 Formulier | Buiten openingstijden, vergelijkers | Hero + secties + slot | Lead vastleggen in CRM |

WhatsApp prefilled bericht: `Hoi [BEDRIJFSNAAM], ik wil graag een mobiele airco huren in [stad]. Kan dat snel?`

## 3. Het primaire leadformulier (kort = meer leads)

**Velden (zo min mogelijk):**
1. Naam *
2. Telefoonnummer * (belangrijkste — hierop bel je terug)
3. Plaats / postcode * (capaciteit dienstgebied + relevantie)
4. Wat wil je koelen? * (dropdown: Slaapkamer/woning · Kantoor · Serverruimte · Evenement · Bouw/droging · Anders) — kwalificeert het segment
5. Vanaf wanneer? (dropdown: Vandaag/spoed · Deze week · Later/plannen) — kwalificeert urgentie
6. (optioneel) E-mail
7. (optioneel) Bericht

> E-mail optioneel houden verhoogt de conversie; telefoon is wat je echt nodig hebt. "Spoed vandaag" → triggert prioriteit in CRM (zie 09).

**Onder de knop:** "✓ Vrijblijvend ✓ Gratis advies ✓ Reactie binnen 5 minuten"
**Knoptekst:** `Verstuur — wij bellen je zo terug ▸` (geen kale "Verzenden")

### Multi-step variant (vaak hogere conversie)
Stap 1: "Wat wil je koelen?" (grote klik-tegels — lage drempel, commitment-trigger).
Stap 2: "Vanaf wanneer + waar?" (plaats + datum).
Stap 3: "Waar mogen we je bereiken?" (naam + telefoon).
Voortgangsbalk tonen. A/B-testen tegen het korte 1-stapsformulier.

## 4. Conversie-elementen per pagina

- **Hero CTA** boven de vouw, contrasterende kleur, max 1 primaire actie.
- **Vertrouwenssignalen** direct zichtbaar: reviewscore + sterren, "binnen 24u geleverd", aantal klanten, garantie, KvK.
- **Sticky mobiele onderbalk**: Bellen | WhatsApp | Aanvraag (3 knoppen).
- **Sticky desktop CTA** bij scrollen + telefoonnummer rechtsboven.
- **Social proof** verspreid (niet alleen 1 blok): quotes, logo's, casecijfers.
- **Exit-intent popup** (desktop): "Nog twijfels? App ons je vraag — gratis advies." (subtiel, niet spammen).
- **Live urgentie** (eerlijk gebruiken): "Druk seizoen — beperkte voorraad, reageer snel" alleen als waar.
- **Klik-om-te-bellen** overal op mobiel.

## 5. Vertrouwen & bezwaren wegnemen op de pagina

Plaats geruststellers naast de CTA's:
- "Geen verplichtingen — eerst advies, dan beslis je."
- "Prijs vooraf duidelijk, geen verrassingen."
- "Lokaal bedrijf, geen callcenter."
- Garantie/voorwaarden, veilige betaling, KvK-nummer.
- Reviews met naam + plaats (echtheid).

## 6. Snelheid & techniek (CRO ∩ performance)

- Laadtijd <2,5s — trage pagina = lagere conversie én lagere ranking (zie 11).
- Formulier werkt feilloos op mobiel (grote tikdoelen, juiste toetsenbordtypes: `tel` voor telefoon).
- Geen verplichte account/login.
- Direct bevestiging na verzenden + doorsturen naar `/bedankt/` (tracking + vervolginstructie).

## 7. Bedankpagina (/bedankt/) — onderschat conversiemoment

- Bevestig: "Gelukt! We bellen of appen je binnen [X] minuten."
- Zet verwachting: openingstijden, wat ze kunnen voorbereiden (m², stopcontact).
- Extra conversiekans: "Met spoed nodig? Bel ons direct: [TELEFOON]."
- Tracking-trigger voor conversie (GA4/Ads — zie 12).
- Optioneel: WhatsApp-knop "Stuur alvast een foto van je ruimte".

## 8. A/B-testplan (prioriteer op impact)

| Test | Variant A | Variant B | Hypothese |
|------|-----------|-----------|-----------|
| Formulierlengte | Kort (1 stap) | Multi-step tegels | Multi-step → meer starts & completes |
| Hero-CTA-tekst | "Aanvraag starten" | "Bekijk beschikbaarheid" | Beschikbaarheid → meer relevantie |
| Prijzen tonen | "vanaf €XX" | "op aanvraag" | Prijs tonen → meer vertrouwen & gekwalificeerde leads |
| WhatsApp-knop prominentie | Standaard | Vergroot + tekst | Meer WhatsApp-leads |
| Vertrouwensbadge | Met reviewscore | Zonder | Reviews → hogere conversie |
| Urgentie-melding | Aan | Uit | Eerlijke urgentie → snellere actie |

Regels: 1 variabele per test, voldoende verkeer/conversies voor significantie, draai tests minstens 1-2 weken (en idealiter over verschillende weerdagen, want gedrag verschilt op hete vs. koele dagen).

## 9. Conversie-KPI's om te bewaken

- **Conversieratio** bezoeker → lead (doel: 3-6%+ op landingspagina's, hoger op Ads-landings).
- Formulier-startratio vs. completion-ratio (waar haken ze af?).
- Aandeel bellen vs. WhatsApp vs. formulier.
- Conversie per kanaal (organisch/ads/lokaal) en per device.
- Lead-kwaliteit (segment + urgentie) → koppeling met sales-conversie (zie 09/12).

## 10. Tooling

- **Formulieren**: WPForms / Gravity Forms / Fluent Forms (conditionele logica, multi-step, CRM-koppeling).
- **WhatsApp**: klik-naar-chat (wa.me) of WhatsApp Business API voor automatisering (zie 08).
- **Heatmaps/sessieopnames**: Hotjar/Microsoft Clarity (gratis) — zie waar mensen afhaken.
- **A/B-testen**: Google Optimize-alternatief (bv. via plugin) of server-side.
- **Tracking**: GA4 + GTM + conversie-events (zie 12).
