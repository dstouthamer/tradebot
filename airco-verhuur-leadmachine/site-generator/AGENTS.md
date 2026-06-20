# AGENTS.md — taken die je aan een agent geeft

Jij hoeft zo min mogelijk te doen. Geef een agent (Claude Code) een van de
onderstaande opdrachten; de agent past `config.yaml` aan, draait de generator
en — als je dat wilt — publiceert naar WordPress. Kopieer een zin, vul je
wensen in, klaar.

> **Nieuwe koper opzetten?** Gebruik [`ONBOARDING.md`](ONBOARDING.md): de agent
> interviewt de koper en bouwt hun site van nul. Dit `AGENTS.md` gaat over het
> daarna onderhouden/wijzigen van een bestaande site.

## Hoe een agent te werk gaat (vaste werkwijze)

1. Lees `site-generator/config.yaml` (de enige bron van waarheid).
2. Pas alleen de gevraagde velden aan (laat de rest met rust).
3. Draai `python generate.py` en controleer dat het zonder fouten draait.
4. Controleer kort `build/preview/home.html` (titel + de gewijzigde tekst).
5. Publiceer indien gevraagd: `python wp_publish.py` (vereist `WP_URL`,
   `WP_USER`, `WP_APP_PASSWORD` in de omgeving).
6. Commit de wijziging met een duidelijke boodschap.

> Regel: nooit code raden of een ander product verzinnen — vraag het de
> gebruiker als iets onduidelijk is. Wijzig geen `build/`-bestanden met de
> hand; die worden gegenereerd.

## Kant-en-klare opdrachten (voorbeelden)

**Gegevens & branding**
- "Zet het telefoonnummer op `…` en het WhatsApp-nummer op `…`."
- "Verander de bedrijfsnaam naar `…` en de hoofdkleur naar `#…`."
- "Pas het werkgebied aan naar `…`."

**Prijzen & aanbod**
- "Update de prijzen: Basis €X/week, Comfort €Y/week."
- "Voeg een pakket toe: `…` voor `…`, prijs `…`."

**Lokale SEO uitbreiden (de groeimotor)**
- "Voeg deze 15 steden toe als lokale pagina's: `…`. Geef elke stad een
  realistische levertijd en 2-3 buurplaatsen."
- "Maak lokale pagina's voor alle plaatsen binnen 30 km van `…`."

**Teksten**
- "Maak de homepage-hero korter en zakelijker."
- "Voeg deze 3 nieuwe FAQ-vragen toe: `…`."
- "Voeg deze echte klantreview toe: `…`."

**Ander product**
- "Maak een nieuwe config voor `[product]` (zoals
  `config.voorbeeld-zonnepanelen.yaml`) en genereer de site."

**Publiceren & onderhoud**
- "Publiceer de huidige config naar WordPress."
- "Controleer of alle pagina's nog goed in WordPress staan en werk ze bij."
- "Voeg het seizoen-actieblok toe en publiceer."

## Wat een agent NIET zelfstandig doet (eerst vragen)

- Live publiceren naar de echte WordPress-site zonder expliciete go.
- De `web3forms_access_key`, domeinnaam of e-mail veranderen (gevoelig).
- Grote herstructureringen van de paginastructuur.

## Inhoudelijke kennis voor betere teksten

Voor copy, SEO-keuzes, sales- en opvolgteksten kan de agent putten uit de
draaiboeken in de map hierboven:
- SEO & keywords → `../03-seo-plan-keywords.md`
- Teksten & toon → `../04-teksten-website.md`
- Lokale pagina's → `../05-lokale-seo-paginas.md`
- Conversie/CRO → `../06-leadformulieren-en-cro.md`
- Opvolging & sales → `../07-sales-scripts.md`, `../08-opvolging-whatsapp-email.md`
