# 08 — Opvolging via WhatsApp & E-mail (Automation)
**Rol: Automation-specialist**

> Doel: **geen enkele lead valt tussen wal en schip.** De seconde dat een lead binnenkomt, start een geautomatiseerde flow die de klant geruststelt én een mens aanzet tot bellen — en die blijft opvolgen tot er een ja of definitieve nee is.

## 1. Reactietijd-regel (het hart van de machine)

| Moment | Actie | Kanaal | Automatisch/handmatig |
|--------|-------|--------|----------------------|
| 0 min (lead binnen) | Instant bevestiging naar klant | WhatsApp + e-mail | Automatisch |
| 0 min | Bel-taak + notificatie naar sales | CRM/push/WhatsApp | Automatisch |
| < 5 min | Persoonlijk bellen | Telefoon | Handmatig (sales) |
| 5 min (geen gehoor) | "Net gebeld, app me terug" | WhatsApp | Half-automatisch |
| 30 min | Tweede belpoging | Telefoon | Handmatig |
| 2-4 uur | Opvolg-app met aanbod/vraag | WhatsApp | Automatisch (indien nog geen contact) |
| Dag 1 avond | E-mail met aanbod + reviews | E-mail | Automatisch |
| Dag 2 | Derde belpoging + app | Telefoon/WhatsApp | Half-automatisch |
| Dag 3 | "Laatste kans / nog interesse?" | WhatsApp/e-mail | Automatisch |
| Dag 5-7 | Afsluiten of naar lange-termijn-nurture | E-mail | Automatisch |

## 2. WhatsApp-flows

### 2.1 Instant bevestiging (0 min)
> Hoi [voornaam]! 👋 Bedankt voor je aanvraag bij [BEDRIJFSNAAM] voor een mobiele airco in [plaats]. We bekijken 'm direct en bellen je binnen enkele minuten. Liever nu al iets kwijt? Stuur gerust een berichtje of foto van je ruimte. ❄️

### 2.2 Geen gehoor na belpoging (5 min)
> Hoi [voornaam], ik probeerde je net te bellen over je airco-aanvraag maar kreeg je niet te pakken. Wanneer schikt het, of zal ik 'm direct voor je inplannen? — [NAAM], [BEDRIJFSNAAM]

### 2.3 Opvolging na 2-4 uur (nog geen contact)
> Hoi [voornaam], het blijft warm de komende dagen 🥵. Voor jouw ruimte ([type], [plaats]) kunnen we vandaag nog leveren vanaf €XX incl. installatie. Zal ik 'm reserveren? Op = op tijdens dit seizoen.

### 2.4 Boekingsbevestiging (na close)
> Top, geregeld! ✅ Je mobiele airco:
> 📍 [adres]
> 📅 [datum], tussen [tijdvak]
> ❄️ [unit/capaciteit]
> 💶 €XX incl. bezorging, installatie & ophalen
> We appen je als de monteur onderweg is. Tot dan! — [BEDRIJFSNAAM]

### 2.5 Onderweg-melding (leverdag)
> Hoi [voornaam], onze monteur is onderweg naar [adres], aankomst rond [tijd]. 🚐 Tot zo!

### 2.6 Tijdens huur — check & upsell
> Hoi [voornaam], lekker koel zo? 😎 Mocht je 'm langer willen houden of een extra unit nodig hebben, één appje en ik regel het. Wil je dat ik de ophaaldatum ([datum]) bevestig?

### 2.7 Ophaal-reminder
> Hoi [voornaam], je huurperiode loopt af op [datum]. Wil je verlengen of zullen we ophalen? Laat het me weten dan plan ik het in. 🙌

### 2.8 Review-verzoek (1-2 dagen na retour)
> Bedankt voor het huren bij [BEDRIJFSNAAM], [voornaam]! 🙏 Was je tevreden? Een review helpt ons enorm — kost je 30 seconden: [REVIEW-LINK]. Alvast bedankt!

## 3. E-mail-flows

### 3.1 Bevestiging (0 min, automatisch)
**Onderwerp:** We hebben je aanvraag — we bellen je zo ❄️
> Beste [voornaam], bedankt voor je aanvraag voor een mobiele airco in [plaats]. Een van ons belt je binnen enkele minuten (tijdens openingstijden). Met spoed nodig? Bel direct: [TELEFOON]. — [BEDRIJFSNAAM]

### 3.2 Aanbod-mail dag 1 (geen contact)
**Onderwerp:** Je mobiele airco staat klaar — vandaag nog mogelijk
> Inhoud: korte herhaling aanbod, prijsindicatie, 3 USP's, 2 reviews, duidelijke CTA (bel/app/plan in), foto unit. Urgentie: "tijdens warme dagen is onze voorraad beperkt".

### 3.3 Herinnering dag 3
**Onderwerp:** Nog interesse in verkoeling, [voornaam]?
> Korte, vriendelijke nudge + weersverwachting-haakje + makkelijke 1-klik-actie (WhatsApp/bel).

### 3.4 Laatste mail dag 5-7
**Onderwerp:** Zullen we je aanvraag sluiten?
> "We willen je niet lastigvallen. Nog steeds verkoeling nodig? Klik hier en we regelen het vandaag. Anders sluiten we je aanvraag — je bent altijd welkom terug." (Reactivatie-trigger.)

### 3.5 Seizoens-nurture (lange termijn, niet-geconverteerde leads + oud-klanten)
- **Voorjaar (april/mei):** "De zomer komt eraan — reserveer nu je airco met vroegboekvoordeel."
- **Hittegolf-alert:** "Komend weekend [X]°C in [REGIO] — verzeker je van een unit voordat ze op zijn."
- **Zakelijk:** onderhouds-/seizoenscontract aanbieden.

## 4. Segment- & urgentie-routing

Pas de flow aan op de leadgegevens uit het formulier (zie 06):
- **"Spoed/vandaag"** → directe bel-prioriteit + snelle WhatsApp, sla trage e-mailtimers over.
- **"Serverruimte"** → escaleer naar telefoon onmiddellijk, hoogste prioriteit (zie 07/09).
- **"Later/plannen"** → minder agressief, meer e-mail-nurture, reminder rond gewenste datum.
- **Zakelijk** → offerte-mail + persoonlijke opvolging; particulier → snelle close-app.

## 5. Technische opzet (tools & koppelingen)

**Optie A — Lean/betaalbaar:**
- Formulier (WPForms/Fluent) → Zapier/Make → CRM + e-mail (bv. via SMTP) + WhatsApp (via klik-naar-chat of API-provider).
- E-mailautomatisering: MailerLite/Brevo/ActiveCampaign.
- Bel-taken: notificatie naar sales via app/Slack/WhatsApp.

**Optie B — Geïntegreerd:**
- CRM met ingebouwde automatisering (HubSpot/Pipedrive/GoHighLevel) dat WhatsApp + e-mail + taken centraal regelt.
- WhatsApp Business API (via Twilio/360dialog/Trengo) voor automatische templates (let op: WhatsApp vereist goedgekeurde message templates voor proactieve berichten buiten 24-uursvenster).

**Belangrijk bij WhatsApp Business API:**
- Proactieve berichten = goedgekeurde templates nodig.
- Binnen 24u na klantbericht mag je vrij reageren (service window).
- Opt-in vastleggen (klant deed aanvraag = legitiem belang, maar wees netjes).

## 6. Compliance (AVG/GDPR)

- Toestemming/grondslag voor opvolging vastleggen (aanvraag = grondslag voor contact over die aanvraag).
- Duidelijke privacyverklaring + verwerkingsregister.
- Afmeldmogelijkheid in marketing-e-mails (verplicht).
- Onderscheid: transactionele opvolging (aanvraag afhandelen) vs. marketing-nurture (toestemming netjes regelen).
- Bewaar leaddata niet langer dan nodig.

## 7. Flow-overzicht (pseudocode automation)

```
ON form_submit:
    create_lead(CRM, data)            # zie 09
    set_priority(data.urgentie, data.segment)
    send_whatsapp(template="bevestiging_instant")
    send_email(template="bevestiging")
    create_task(sales, "Bel binnen 5 min", due=now+5min)
    notify(sales_channel)

IF no_contact AND elapsed >= 5min:
    send_whatsapp(template="net_gebeld")
IF no_contact AND elapsed >= 2h:
    send_whatsapp(template="opvolging_aanbod")
IF no_contact AND elapsed >= 1d:
    send_email(template="aanbod_dag1")
IF no_contact AND elapsed >= 3d:
    send_whatsapp/email(template="herinnering")
IF no_contact AND elapsed >= 7d:
    send_email(template="laatste_kans")
    move_stage(CRM, "Koud / nurture")

ON booked:
    send_whatsapp(template="boekingsbevestiging")
    schedule(template="onderweg", at=leverdag)
    schedule(template="ophaal_reminder", at=einddatum-1d)
    schedule(template="review_verzoek", at=retour+1d)
```
