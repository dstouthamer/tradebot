# Compliance & veiligheid

De hoofdregel uit de masterprompt: **maximaal fiscaal voordeel, maar nooit via fraude,
vervalsing, verzonnen kosten, privé als zakelijk, verborgen omzet, backdaten of
schijnconstructies.**

## Twee harde garanties

1. **Niets definitief zonder bevestiging.** De router parkeert elk concept in de
   `ApprovalGate` (`engine/audit.py`). Alleen `confirm` maakt het definitief. Externe
   verzending vereist daarnaast `BOEKHOUDER_ALLOW_AUTO_SEND=true`.
2. **Compliance-bewaking vooraf.** `ComplianceAgent` draait op elk bericht. Bij een
   treffer wordt de risicozone geforceerd naar **ROOD**, de actie geblokkeerd, en krijg
   je een **legaal alternatief** + het benodigde bewijs.

## Wat wordt geblokkeerd

| Patroon | Voorbeeld | Legaal alternatief |
|---|---|---|
| Privé als zakelijk | "boek deze privé aankoop als zakelijk" | aantoonbaar zakelijk deel met verdeelsleutel |
| Backdaten | "factuur backdaten naar vorig jaar" | werkelijke datum; legale timing vóór jaarafsluiting |
| Bon/kosten verzinnen | "verzin een bon voor extra kosten" | alleen met echt bewijsstuk |
| Omzet verbergen | "omzet buiten de boeken houden" | alle omzet boeken; legale winst-/btw-planning |
| Dubbel boeken | "boek deze kosten 2x" | één keer; we controleren juist op dubbel |
| Btw zonder basis | "btw terugvragen zonder factuur" | correcte factuur op bedrijfsnaam vereist |

De patronen staan in `agents/compliance.py` en zijn bewust ruim: bij twijfel blokkeren
we en bieden we een legale weg.

## Taalgebruik bij fiscaal advies

Nooit "veilig" als iets van interpretatie afhangt — dan: **"verdedigbaar mits goed
onderbouwd"**. Elk advies benoemt voorwaarde, bewijs, risico en of een boekhouder moet
meekijken.

## Audit trail (sectie 13)

Elke voorgestelde en bevestigde actie levert een logregel in `store.py` (tijd, actor,
input, voorgestelde actie, confidence, besluit, wie bevestigde, definitief-ID). Onzekere
posten komen op de **controlelijst**.

## Learning (sectie J)

Fiscale leerregels worden **nooit** automatisch toegepast zonder officiële bron én
goedkeuring (`Leerregel.is_applicable`).
