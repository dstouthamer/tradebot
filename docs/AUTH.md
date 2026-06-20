# Inloggen & multi-tenant

Elk bedrijf is een **tenant**; alle administratiedata (boekingen, facturen, bank,
audit, controlelijst, leerregels, nummering) is per tenant afgeschermd. Een gebruiker
hoort bij één tenant.

## Login-methoden

| Methode | Status | Nodig |
|---|---|---|
| **E-mail + wachtwoord** | ✅ werkt direct, gratis | niets |
| **Google / Microsoft (OAuth)** | ✅ stekker, gratis | client id/secret in `.env` |
| **iDIN (banklogin)** | 🧩 stekker, **betaald** | broker-contract (Signicat/CM.com/bank) |

> **iDIN kan niet gratis.** Elke iDIN-aansluiting loopt via een betaalde broker met
> setup- en transactiekosten. De knop verschijnt alleen als er een contract is
> geconfigureerd. Tot die tijd gebruik je e-mail/wachtwoord of Google/Microsoft.

## Hoe het technisch werkt

- **Wachtwoorden:** PBKDF2-HMAC-SHA256 met salt (`auth/passwords.py`), standaardbibliotheek.
- **Sessies:** staatloze, HMAC-ondertekende tokens met vervaltijd (`auth/tokens.py`).
  Geen serverstate; manipulatie/verloop maakt een token ongeldig.
- **Geheim:** zet in productie `BOEKHOUDER_SECRET_KEY` (anders een onveilige dev-fallback).

## API

```
POST /auth/register   {email, password, company_name}  -> {token, tenant_id}
POST /auth/login      {email, password}                 -> {token, tenant_id}
GET  /auth/methods                                       -> beschikbare login-methoden
GET  /auth/me         (Bearer token)                     -> huidige gebruiker/tenant
GET  /auth/{google|microsoft}/login                      -> redirect naar provider
GET  /auth/{google|microsoft}/callback?code=...          -> {token}
```

Alle administratie-endpoints (`/bericht`, `/upload`, `/approve`, `/controlelijst`,
`/audit`) vereisen de header `Authorization: Bearer <token>` en werken automatisch
binnen de tenant van de gebruiker.

## CLI / dashboard / Telegram

- De **CLI** en het **Streamlit-dashboard** draaien op de standaard `local`-tenant
  (geen login nodig voor lokaal gebruik).
- De **Telegram-bot** is bedoeld als één-bedrijf-bot en werkt op de `local`-tenant.
  Voor multi-tenant via chat zou je Telegram-gebruikers aan tenants koppelen (uitbreiding).
