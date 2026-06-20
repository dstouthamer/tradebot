# Agentrollen

Elke rol uit de masterprompt is een kleine, testbare klasse in `boekhouder/agents/`.
Allemaal retourneren ze een `AgentResult` (zie [ARCHITECTURE.md](ARCHITECTURE.md)).

| Rol (masterprompt) | Klasse | Doet |
|---|---|---|
| A. Intake | `intake.IntakeAgent` | bericht → `Intent` (intentie, entiteiten, ontbrekende velden, route) |
| B. OCR & Bonnetjes | `ocr.OcrAgent` | document/tekst → velden + bewijskwaliteit; vraagt om betere foto bij rood |
| C. Bank Matching | `bank_matching.BankMatchingAgent` | scoort match (bedrag/datum/naam/IBAN) → confidence + reden |
| D. Boekhoud | `bookkeeping.BookkeepingAgent` | conceptboeking + risicozone |
| E. Fiscale optimalisatie | `fiscal.FiscalAgent` | advies in vast format; nooit "veilig" bij interpretatie |
| F. Compliance & Controle | `compliance.ComplianceAgent` | blokkeert fraude, biedt legaal alternatief |
| G. Factuur | `invoice.InvoiceAgent` | conceptverkoopfactuur |
| H. Offerte | `quote.QuoteAgent` | conceptofferte met expliciete aannames/stelposten |
| I. CFO Advies | `cfo.CfoAgent` | financiële analyse + één concrete actie |
| J. Learning | `learning.LearningAgent` | versie-/bron-beheerde leerregels |

## Beslismodel (groen/oranje/rood)

- **Groen** — direct verdedigbaar: duidelijk zakelijk, correct bewijs, goede match.
- **Oranje** — scherp maar mogelijk verdedigbaar: gemengd/onzeker, extra bewijs of
  boekhouder-check nodig; vaak op de controlelijst.
- **Rood** — niet doen: geen bewijs, privé, onjuiste factuur, dubbel, of fraude.

## Confidence-banding bankmatch (`engine/rules.py`)

| Confidence | Actie |
|---|---|
| 95–100% | automatisch voorstellen als match (`boeken`) |
| 80–94% | match voorstellen, gebruiker bevestigt (`bevestigen`) |
| 50–79% | op de controlelijst (`controleren`) |
| < 50% | niet koppelen, vraag info (`afwijzen`) |

## LLM-seam

Agents die baat hebben bij vrije tekst (intake-verfijning, fiscaal/CFO-narratief) gaan
via `providers/llm.py`. Default is `RuleBasedLLM` (deterministisch, offline). Met
`BOEKHOUDER_ANTHROPIC_API_KEY` wordt `ClaudeLLM` (claude-opus-4-8) gebruikt — maar
**nooit** voor de bedragen; die komen altijd uit de deterministische engine.
