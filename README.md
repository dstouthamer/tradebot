# 🧾 AI Boekhouder — CFO- & fiscale-optimalisatie-agent (NL)

Een Nederlandse AI-boekhoudagent die bonnen en facturen verwerkt, ze koppelt aan
banktransacties, verkoopfacturen en offertes opstelt via chat, financieel en fiscaal
advies geeft — en de belastingdruk zo laag mogelijk houdt **binnen de wet**.

> ⚠️ **Veilig by design.** Niets wordt definitief geboekt, verzonden of ingediend
> zonder jouw expliciete bevestiging. De agent doet **nooit** aan fraude, backdaten,
> verzonnen kosten, privé-uitgaven als zakelijk, of het verbergen van omzet. Bij twijfel
> krijg je een legaal alternatief. Dit is geen vervanging voor je boekhouder/fiscalist.

## Wat het doet

| Capability | Status (MVP) |
|---|---|
| Inloggen (e-mail+wachtwoord) + multi-tenant (SaaS, data per bedrijf gescheiden) | ✅ |
| Login met Google/Microsoft (gratis) / iDIN banklogin (betaald) | ✅ stekker via config |
| Intake via chat (WhatsApp-stijl korte commando's) | ✅ |
| OCR & bonnetjesherkenning (Tesseract + keyless tekst-fallback) | ✅ |
| Bankkoppeling: CAMT.053 / MT940 / CSV import + matching | ✅ |
| Conceptboekingen met groen/oranje/rood risico | ✅ |
| Verkoopfacturen & offertes via chat (concept, bevestiging-gated) | ✅ |
| **Prognoses** (cashflow / btw / indicatieve belasting) + CFO-advies | ✅ |
| Fiscale optimalisatie & CFO-advies (vaste outputformats) | ✅ |
| Compliance-bewaking (blokkeert fraude, biedt legaal alternatief) | ✅ |
| Learning rules met versiebeheer + bron | ✅ |
| Telegram-bot intake (tekst + foto) | ✅ met token |
| Moneybird concept-facturen + banktransacties | ✅ met token (anders dry-run) |
| **Obsidian-export** (boekhouding als Markdown-notities in je vault) | ✅ keyless, lokaal |
| FastAPI backend + Streamlit dashboard + CLI | ✅ runnable |
| Hosten op een VPS (bv. mijn.host) met Docker + automatische HTTPS | ✅ zie deploy/ |
| LLM-reasoning via Claude (claude-opus-4-8) | 🧩 seam, aan met API-key |

## Quickstart (geen API-keys nodig — draait keyless)

```bash
pip install -r requirements.txt

# 1) Deterministische tests
PYTHONPATH=. python tests/test_core.py        # of: python -m pytest tests/ -q

# 2) Chat in de terminal
python -m boekhouder.cli

# 3) …of de web-app met inloggen (registreren + chat + prognoses in de browser)
uvicorn boekhouder.api.main:app --reload      # open http://localhost:8000/
#                                              # API-docs op http://localhost:8000/docs

# 4) …of het lokale dashboard
streamlit run streamlit_app.py
```

Voorbeelden in de CLI:

```
Maak factuur voor De Vries airco montage 1850 ex btw
Maak offerte hybride warmtepomp Apeldoorn 6500 incl btw
/bank tests/fixtures/sample_ing.csv
/obsidian                                   # exporteer naar je Obsidian-vault
Bonnetje Gamma project Jansen 124,80 12-06-2026
Hoeveel btw moet ik betalen dit kwartaal?
Boek deze prive aankoop als zakelijk        # -> wordt geblokkeerd (rood)
ja                                          # bevestigt het laatste concept
```

## Echte integraties aanzetten

Kopieer `.env.example` naar `.env` en vul in wat je wilt gebruiken — alles is optioneel:

```bash
BOEKHOUDER_TELEGRAM_TOKEN=...     # python -m boekhouder.worker  (long-poll bot)
BOEKHOUDER_MONEYBIRD_TOKEN=...    # concept-facturen in Moneybird
BOEKHOUDER_MONEYBIRD_ADMIN_ID=...
BOEKHOUDER_OBSIDIAN_VAULT=...     # exporteer je boekhouding als Markdown-notities
BOEKHOUDER_ANTHROPIC_API_KEY=...  # LLM-reasoning seam (claude-opus-4-8)
BOEKHOUDER_ALLOW_AUTO_SEND=false  # laat op false tot je echt wilt versturen
```

## Architectuur

```
chat / API / Telegram
        │
   ┌────▼─────┐  compliance pre-check (blokkeert fraude)
   │  Router  │──────────────────────────────────────┐
   └────┬─────┘                                               │
        │ Intake bepaalt intentie                             │
        ▼                                                     ▼
  ┌──────────────────────────── agents ─────────────────────┐
  │ OCR · Bank-matching · Boekhoud · Factuur · Offerte · Fiscaal · CFO │
  │ Learning · Compliance        (allemaal -> AgentResult groen/oranje/rood)
  └───────────────────────────────────────────────┘
        │                                  │
   approval gate (geen actie zonder 'ja')  providers (OCR/bank/Moneybird/Telegram/Obsidian/LLM)
        │                                  │
   audit log + controlelijst        keyless fallback per provider
```

Zie [`docs/`](docs/) voor architectuur, agentcontracten, compliance-regels, integraties,
[inloggen/multi-tenant](docs/AUTH.md) en [prognoses & belastingtarieven 2026 met bronnen](docs/PROGNOSE.md).
Hosten: [`deploy/DEPLOY-mijn.host.md`](deploy/DEPLOY-mijn.host.md).

**Opslag:** standaard sqlite (lokaal/MVP). Voor schaal zet je een Postgres-URL in
`BOEKHOUDER_DATABASE_URL` — dezelfde code draait op beide. Belastingindicaties zijn
onderbouwd op peiljaar 2026 (zie bronnen) maar **indicatief** (excl. heffingskortingen);
laat ze door je fiscalist toetsen.

## Inloggen & meerdere bedrijven (SaaS)

```bash
# registreer een bedrijf + account, log in, gebruik de API met de token
curl -X POST localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"jij@bedrijf.nl","password":"geheim123","company_name":"Mijn Bedrijf"}'
# -> {"token":"...", "tenant_id":"..."}
curl localhost:8000/bericht -H "Authorization: Bearer <token>" \
  -H 'content-type: application/json' -d '{"message":"Geef een prognose"}'
```

E-mail+wachtwoord werkt direct en gratis. Google/Microsoft-login activeer je met
client-keys in `.env`. **iDIN (banklogin) kan niet gratis** — dat vereist een betaald
broker-contract; tot die tijd gebruik je e-mail of Google/Microsoft. Details in
[docs/AUTH.md](docs/AUTH.md).

## Hosten bij mijn.host

Een Python-app heeft een **VPS** nodig (root/SSH) — niet de klassieke shared
webhosting. Met Docker staat het in een paar commando's live mét gratis HTTPS:

```bash
cp .env.example .env   # zet BOEKHOUDER_SECRET_KEY!
export DOMAIN=boekhouder.jouwdomein.nl
docker compose up -d --build
```

Volledige stap-voor-stap (incl. pakketkeuze, back-ups, logins): zie
[`deploy/DEPLOY-mijn.host.md`](deploy/DEPLOY-mijn.host.md).

## Herkomst

De architectuur (agentcontract, router-ensemble, pluggable providers met keyless
fallback, prioriteit-notifier, safe-by-default config, deterministische tests) is
ontleend aan het Apex-platform dat als bundle in deze repo zat.

## Disclaimer

Educatief/hulpmiddel. Geen fiscaal of juridisch advies. Controleer belangrijke
beslissingen met je boekhouder of fiscalist.
