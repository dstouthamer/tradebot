# 09 — CRM-pipeline
**Rol: Automation-specialist + sales closer**

## 1. Doel

Eén centraal systeem waarin elke lead binnenkomt, zichtbaar is, automatisch wordt opgevolgd en door de fasen naar "verhuurklant" beweegt — met meetbare conversie per stap.

## 2. Toolkeuze

| Tool | Sterk in | Voor wie |
|------|----------|----------|
| **Pipedrive** | Simpele visuele pipeline, betaalbaar | Starter/MKB, sales-gedreven |
| **HubSpot (free/starter)** | All-in-one marketing+sales, gratis start | Groei, veel automatisering |
| **GoHighLevel** | WhatsApp/SMS/funnels ingebouwd, agency-stijl | Wie alles in 1 wil |
| **Trengo / Pipedrive + Make** | WhatsApp-centric inbox | WhatsApp-zware leadflow |

Aanbeveling starter: **Pipedrive of HubSpot** + Make/Zapier voor koppelingen. Schaal je op WhatsApp-volume → overweeg GoHighLevel/Trengo.

## 3. Pipeline-stages

```
1. NIEUWE LEAD          → net binnen, nog geen contact
2. GECONTACTEERD        → gebeld/geappt, gesprek gaande
3. GEKWALIFICEERD       → ruimte/periode/budget bekend, past
4. OFFERTE/VOORSTEL     → prijs gecommuniceerd, wacht op ja
5. GEBOEKT              → akkoord, leverafspraak staat
6. GELEVERD/LOPEND      → unit draait bij klant
7. RETOUR/AFGEROND      → opgehaald, factuur voldaan
8. VERLOREN / NURTURE   → geen deal nu → seizoens-nurture
```

Stage-conversie meten (zie 12): elke overgang is een meetpunt. Waar zakken leads weg?

## 4. Leadvelden (datamodel)

**Contact:** naam · telefoon · e-mail · plaats/postcode.
**Aanvraag:** segment (particulier/kantoor/serverruimte/evenement/bouw) · ruimte-m² / kW-advies · gewenste startdatum · huurperiode · urgentie (spoed/deze week/later).
**Sales:** bron (organisch/Ads/lokaal/referral) · toegewezen aan · prioriteit (hoog/mid/laag) · geschatte waarde · status/stage · laatste contactmoment · volgende actie + datum.
**Operationeel (na boeking):** leveradres · leverdatum/tijdvak · unit/serienummer · borg · betaalstatus · einddatum/ophaaldatum.

## 5. Lead-scoring & prioritering

Automatische prioriteit op basis van formulierdata:

| Signaal | Prioriteit |
|---------|-----------|
| Segment = serverruimte OF urgentie = spoed/vandaag | 🔴 Hoog — bel direct |
| Zakelijk + deze week | 🟠 Mid-hoog |
| Particulier + deze week | 🟡 Mid |
| "Later/plannen" | 🟢 Laag — nurture, reminder rond datum |
| Buiten dienstgebied | ⚪ Diskwalificeer / doorverwijs |

Hoge prioriteit → bovenaan de bellijst + directe push naar sales.

## 6. Automatiseringen in het CRM

| Trigger | Automatische actie |
|---------|-------------------|
| Nieuwe lead binnen | Lead aanmaken, prioriteit zetten, bel-taak (+5 min), bevestiging WhatsApp+e-mail (zie 08), sales notificeren |
| Stage → Geboekt | Boekingsbevestiging sturen, leverafspraak plannen, ophaal-reminder + review-taak inplannen |
| Geen contact na 5/30 min | Vervolg-taak + WhatsApp-nudge |
| Geen reactie na 7 dagen | Naar "Verloren/Nurture" + nurture-flow aan |
| Stage → Retour/Afgerond | Factuurcheck, review-verzoek, oud-klant-tag voor seizoens-nurture |
| Geen "volgende actie" gezet | Waarschuwing naar sales (geen lead mag stil blijven liggen) |

## 7. Voorraad-/beschikbaarheidskoppeling (kritiek in deze markt)

- Houd realtime bij hoeveel units beschikbaar zijn (per capaciteit).
- Sales ziet bij boeking of voorraad er is → voorkom dubbelboeking.
- Bij uitverkocht: bied wachtlijst/alternatieve capaciteit/latere datum aan i.p.v. lead verliezen.
- Koppel leverplanning (route/agenda) aan boekingen.

## 8. Dashboard & rapportage (sales/PM)

Wekelijks/dagelijks zicht op:
- Nieuwe leads (per bron/segment).
- Leads per stage + waarde in pipeline.
- Conversie per stage (lead→contact→offerte→geboekt).
- Gemiddelde reactietijd (kern-KPI) en doorlooptijd lead→klant.
- Win/verlies-ratio + verliesredenen.
- Omzet geboekt vs. doel + bezetting voorraad.

## 9. Verliesredenen vastleggen (leren & verbeteren)

Bij "Verloren" altijd reden taggen: te duur · te traag gereageerd · voorraad op · ging zelf kopen · weer koelde af · koos concurrent · buiten gebied · geen reactie. → Input voor CRO, prijs, voorraad en proces (zie 12).

## 10. Minimale start (als je klein begint)

Geen budget voor een groot CRM? Start met:
- Pipedrive/HubSpot gratis tier **of** een gedeelde spreadsheet met de stages als kolommen.
- WhatsApp Business (labels = stages) voor de chat-leads.
- Eén regel die alles draaglijk maakt: **elke lead krijgt binnen 5 minuten een mens aan de lijn, en niemand mag zonder "volgende actie" blijven staan.**
Upgrade zodra het leadvolume de handmatige opvolging overstijgt.
