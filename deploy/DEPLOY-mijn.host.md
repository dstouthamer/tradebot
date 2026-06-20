# Hosten bij mijn.host

> Ik kon de actuele pakketten/prijzen van mijn.host niet automatisch ophalen (hun site
> blokkeert geautomatiseerde toegang). Controleer de exacte specs/prijs in je
> mijn.host-account; de aanpak hieronder klopt voor elke standaard VPS.

## Welk pakket?

Een Python/FastAPI-app is een **langdraaiend proces** en heeft een **VPS / eigen
server met root- en SSH-toegang** nodig.

- ✅ **mijn.host VPS** (KVM, root/SSH, je kiest Ubuntu/Debian). **Dit is wat je nodig hebt.**
  Richtlijn om mee te starten: **2 vCPU, 4 GB RAM, 40–80 GB SSD**. Ruim voldoende voor
  een multi-tenant MVP; schaal later op.
- ❌ **Shared / webhosting (DirectAdmin/cPanel)** bij mijn.host is bedoeld voor PHP en
  draait deze app **niet**. Neem dan een VPS.

Bestel ook (of wijs) een **domein** en zet een **A-record** naar het IP van je VPS
(bijv. `boekhouder.jouwdomein.nl` → `1.2.3.4`).

## Optie A — Docker (aanbevolen, met automatische HTTPS)

Op een verse Ubuntu-VPS:

```bash
# 1) Docker installeren
curl -fsSL https://get.docker.com | sh

# 2) Code ophalen
git clone <deze-repo> boekhouder && cd boekhouder

# 3) Config: kopieer en vul in
cp .env.example .env
nano .env
#   - BOEKHOUDER_SECRET_KEY=<lange willekeurige waarde>   (VERPLICHT in productie!)
#   - eventueel Moneybird/Telegram/OAuth sleutels
#   - laat BOEKHOUDER_ALLOW_AUTO_SEND=false tot je echt wilt versturen

# Genereer een sterke secret:
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# 4) Domein zetten en starten (Caddy regelt gratis HTTPS):
export DOMAIN=boekhouder.jouwdomein.nl
docker compose up -d --build
```

Klaar: open `https://boekhouder.jouwdomein.nl/` — daar staat de **web-app** waar
mensen zich registreren, inloggen, chatten, prognoses opvragen en concepten bevestigen.
De API-docs staan op `/docs`.

Updaten:

```bash
git pull && docker compose up -d --build
```

## Optie B — zonder Docker (systemd + Nginx)

```bash
sudo apt update && sudo apt install -y python3-venv nginx
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt gunicorn
# Draai met gunicorn (zie het CMD in de Dockerfile voor de exacte parameters)
gunicorn boekhouder.api.main:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
```

Zet Nginx ervoor als reverse proxy naar `127.0.0.1:8000` en regel TLS met
`certbot --nginx`. Maak een systemd-unit zodat het automatisch (her)start.

## Data & back-ups

- De administratie staat in sqlite op het volume `boekhouder-data` (Docker) of in
  `BOEKHOUDER_DB_PATH`. **Back-up dit bestand regelmatig** (bijv. dagelijkse `cp` +
  off-site kopie).
- Voor meer gebruikers/gelijktijdigheid: stap over op PostgreSQL. De store-interface
  is daarop voorbereid; dat is de schaal-route, niet nodig voor de start.

## Logins aanzetten

- **E-mail+wachtwoord:** werkt direct, geen config nodig.
- **Google/Microsoft (gratis):** zet de client id/secret in `.env`
  (`BOEKHOUDER_GOOGLE_CLIENT_ID`, …) en `BOEKHOUDER_OAUTH_REDIRECT_BASE` op je domein.
- **iDIN (banklogin, betaald):** zet `BOEKHOUDER_IDIN_BROKER` + id/secret zodra je een
  contract bij een broker (Signicat/CM.com/bank) hebt. Zonder contract blijft de knop
  verborgen — er is geen gratis iDIN.

## Beveiliging

- Zet **altijd** een eigen `BOEKHOUDER_SECRET_KEY` in productie (tekent sessietokens).
- Zet `BOEKHOUDER_ALLOW_SIGNUP=false` als alleen jij accounts mag aanmaken.
- Houd `BOEKHOUDER_ALLOW_AUTO_SEND=false` tot je bewust facturen extern wilt versturen.
