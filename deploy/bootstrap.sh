#!/usr/bin/env bash
# Eén-commando installatie voor de AI Boekhouder op een Ubuntu/Debian VPS.
#
# Gebruik (vanuit de gekloonde repo):
#   bash deploy/bootstrap.sh boekhouder.klimaatkampioen.nl
#
# Het script installeert Docker (indien nodig), maakt een .env met een veilige
# SECRET_KEY, zet je domein, en start de stack met automatische HTTPS via Caddy.
set -euo pipefail

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
  echo "Gebruik: bash deploy/bootstrap.sh <domein>   (bv. boekhouder.klimaatkampioen.nl)" >&2
  exit 1
fi

# 1) Docker installeren indien nodig
if ! command -v docker >/dev/null 2>&1; then
  echo "→ Docker installeren..."
  curl -fsSL https://get.docker.com | sh
fi

# 2) .env aanmaken vanaf het voorbeeld (bestaande .env blijft ongemoeid)
if [ ! -f .env ]; then
  cp .env.example .env
  echo "→ .env aangemaakt vanaf .env.example"
fi

# 3) Veilige SECRET_KEY genereren als die nog leeg/afwezig is
if grep -q '^BOEKHOUDER_SECRET_KEY=""' .env 2>/dev/null || ! grep -q '^BOEKHOUDER_SECRET_KEY=' .env; then
  SECRET=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))" 2>/dev/null \
           || openssl rand -base64 48 | tr -d '\n')
  if grep -q '^BOEKHOUDER_SECRET_KEY=' .env; then
    sed -i "s|^BOEKHOUDER_SECRET_KEY=.*|BOEKHOUDER_SECRET_KEY=\"$SECRET\"|" .env
  else
    echo "BOEKHOUDER_SECRET_KEY=\"$SECRET\"" >> .env
  fi
  echo "→ SECRET_KEY gegenereerd"
fi

# 4) OAuth redirect base op het domein zetten
if grep -q '^BOEKHOUDER_OAUTH_REDIRECT_BASE=' .env; then
  sed -i "s|^BOEKHOUDER_OAUTH_REDIRECT_BASE=.*|BOEKHOUDER_OAUTH_REDIRECT_BASE=\"https://$DOMAIN\"|" .env
else
  echo "BOEKHOUDER_OAUTH_REDIRECT_BASE=\"https://$DOMAIN\"" >> .env
fi

# 5) Starten
export DOMAIN
echo "→ Stack starten voor https://$DOMAIN ..."
docker compose up -d --build

echo
echo "✅ Klaar! Open https://$DOMAIN/  (het HTTPS-certificaat kan ~1 minuut duren)"
echo "   Meekijken met de logs:  docker compose logs -f"
