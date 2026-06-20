# Integraties

Alle integraties zitten achter een interface (`providers/base.py`) en worden gekozen
door `providers/registry.py`. Zonder credentials draait elke integratie in een veilige
keyless modus, zodat het hele systeem offline werkt en testbaar blijft.

## 1. Telegram (intake) — `providers/telegram.py`

Echte Bot API. Primair chatkanaal voor tekst én foto's (bonnetjes).

```bash
export BOEKHOUDER_TELEGRAM_TOKEN=123:abc
python -m boekhouder.worker          # long-poll
# of webhook: POST /telegram/webhook  (zie api/main.py)
```

Zonder token is de klasse inert (geen netwerk).

## 1b. WhatsApp (intake) — `providers/whatsapp.py`

Via de **Meta WhatsApp Cloud API** (officiële weg; gratis tier). Ontvangt tekst én
foto's van bonnen en stuurt antwoorden terug.

Eenmalige setup bij Meta:
1. Maak een **Meta-bedrijfsaccount** + een app met het product *WhatsApp*.
2. Noteer je **phone number id** en maak een **permanent access token**.
3. Zet in `.env`: `BOEKHOUDER_WHATSAPP_TOKEN`, `BOEKHOUDER_WHATSAPP_PHONE_ID` en een
   zelfgekozen `BOEKHOUDER_WHATSAPP_VERIFY_TOKEN`.
4. Stel in de Meta-app de **webhook** in op `https://<jouwdomein>/whatsapp/webhook` met
   dezelfde verify-token, en abonneer op `messages`.

```bash
# Verificatie (Meta doet dit automatisch): GET /whatsapp/webhook?hub.mode=...&hub.challenge=...
# Inkomend: POST /whatsapp/webhook  -> router -> antwoord in de chat
```

Zonder token is de klasse inert. Eén nummer = één bedrijf (local tenant); voor
multi-tenant via WhatsApp koppel je later nummers aan tenants.

## 2. Moneybird — `providers/moneybird.py`

Echte REST-client. Maakt **alleen concept**-verkoopfacturen (state=draft) en haalt
banktransacties op. Zonder token/administratie draait hij **dry-run**: hij retourneert
de payload die hij zou posten, maar verstuurt niets.

```bash
export BOEKHOUDER_MONEYBIRD_TOKEN=...
export BOEKHOUDER_MONEYBIRD_ADMIN_ID=...
```

Daadwerkelijk aanmaken gebeurt alleen na bevestiging én met
`BOEKHOUDER_ALLOW_AUTO_SEND=true`.

## 3. OCR — `providers/ocr_tesseract.py`

`TesseractOcr` draait echte OCR op afbeeldingen wanneer `pytesseract` + de
`tesseract`-binary aanwezig zijn (`pip install pytesseract Pillow`, plus de
systeem-binary). Anders valt het systeem terug op een deterministische
tekst/regex-extractor (`StubOcr`) die ook werkt op een getypte hint in de chat.

```bash
export BOEKHOUDER_OCR_PROVIDER=auto   # auto | tesseract | stub
```

## 4. Bank-import — `providers/bank_import.py`

Echte, offline parsers voor de drie formaten die Nederlandse banken exporteren:

- **CAMT.053** (SEPA XML) — namespace-agnostisch via stdlib `xml`.
- **MT940** (SWIFT) — `:61:`/`:86:`-regels.
- **CSV** — ING/Rabo/ABN-stijl, kolomdetectie + NL-bedragnotatie + Af/Bij-teken.

```bash
# CLI:  /bank pad/naar/afschrift.csv
# API:  POST /upload met een .xml/.mt940/.csv bestand
```

Formaat wordt automatisch gedetecteerd (`fmt="auto"`).

## 5. LLM — `providers/llm.py`

`RuleBasedLLM` (default, offline) of `ClaudeLLM` met
`BOEKHOUDER_ANTHROPIC_API_KEY` (model `claude-opus-4-8`, vereist `pip install
anthropic`). Alleen voor vrije tekst, nooit voor bedragen.
