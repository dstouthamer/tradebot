# Architectuur

## Lagen

```
boekhouder/
  config.py        Settings (pydantic) + compliance-switches, één auditbare plek
  domain/          enums, money/btw-helpers, document-dataclasses, learning, company
  agents/          de masterprompt-rollen A–J, elk: data in -> AgentResult uit
  providers/       integraties achter interfaces + keyless fallback (registry)
  engine/          rules (thresholds), router (orchestrator), formatters, audit
  store.py         sqlite: nummering, audit log, learning rules, controlelijst, bank
  api/ cli.py worker.py   surfaces (FastAPI / REPL / Telegram long-poll)
streamlit_app.py   dashboard
```

## Het universele contract: `AgentResult`

Elke agent spreekt dezelfde taal (analoog aan Apex's `AgentSignal`, maar dan
boekhoudkundig):

```python
AgentResult(
    agent, risk_zone,            # GROEN / ORANJE / ROOD  (de richtinggevende uitspraak)
    confidence,                  # 0..1
    summary, reasons, advies,
    bewijs_nodig, actie_nodig,   # boeken | controleren | bevestigen | afwijzen | ...
    boekhouder_check,            # moet een fiscalist meekijken?
    requires_confirmation,       # is dit slechts een concept?
    blocked,                     # compliance hard-stop
    payload,                     # de geproduceerde artefact (Boeking/Factuur/...)
)
```

## De pipeline (router)

1. **Compliance pre-check** op het ruwe bericht — een hard-stop overschrijft alles.
2. **Intake** classificeert intentie + entiteiten + ontbrekende velden.
3. **Specialist-agent** draait (OCR → match → boeking, of factuur/offerte/advies).
4. **Approval gate** parkeert het concept; pas `confirm` maakt het definitief.
5. **Formatter** rendert het exacte Nederlandse template (sectie 7–11).

## Safe-by-default

- `require_confirmation=True` en `allow_auto_send=False` standaard.
- Bevestiging finaliseert; *externe verzending* vereist daarnaast `allow_auto_send`.
- Elke voorgestelde actie levert een logregel (sectie 13); onzekere posten gaan op de
  controlelijst.

## Keyless degradatie

`providers/registry.py` kiest een echte implementatie als die geconfigureerd is, anders
een deterministische stub. Daardoor draait én test het systeem volledig zonder keys
(zie [INTEGRATIONS.md](INTEGRATIONS.md)).
