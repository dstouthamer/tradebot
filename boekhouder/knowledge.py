"""Dagelijkse fiscale kennis-update — verantwoord (niet blind vertrouwen).

De agent "leert" niet stilletjes nieuwe belastingregels en past ze toe; dat is precies
wat de masterprompt verbiedt ("nooit automatisch fiscale regels aanpassen zonder bron of
review"). In plaats daarvan:

1. signaleert dit het wanneer ingebouwde tarieven/peildata mogelijk verouderd zijn en zet
   een controlepunt op de controlelijst;
2. laat het (als een LLM is geconfigureerd) een concept-samenvatting van recente
   wijzigingen opstellen, opgeslagen als **pending leerregel** die pas meetelt na
   goedkeuring door een mens/boekhouder.

Draai dagelijks via cron (zie docs) of ``python -m boekhouder.knowledge_update``.
"""
from __future__ import annotations

from datetime import date, datetime

from boekhouder.agents.learning import LearningAgent
from boekhouder.domain import eu_btw, tax_rates
from boekhouder.providers.llm import get_llm
from boekhouder.store import LOCAL_TENANT, Store, get_store

_BTW_RECHECK_DAGEN = 180


def review(today: date | None = None) -> list[dict]:
    """Welke ingebouwde fiscale kennis moet (her)gecontroleerd worden?"""
    today = today or date.today()
    items: list[dict] = []
    if today.year > tax_rates.TAX_YEAR:
        items.append({
            "onderwerp": f"Belastingtarieven peiljaar {tax_rates.TAX_YEAR}",
            "reden": f"Het is {today.year}: controleer box 1-schijven, zelfstandigenaftrek, "
                     "MKB-winstvrijstelling, KIA en vpb op de nieuwe waarden.",
            "bron": tax_rates.SOURCES["box1"],
        })
    try:
        peil = datetime.strptime(eu_btw.PEILDATUM, "%Y-%m").date()
        if (today - peil).days > _BTW_RECHECK_DAGEN:
            items.append({
                "onderwerp": "EU-btw-tarieven",
                "reden": f"Peildatum {eu_btw.PEILDATUM} is ouder dan {_BTW_RECHECK_DAGEN} "
                         "dagen; tarieven kunnen gewijzigd zijn.",
                "bron": eu_btw.SOURCE,
            })
    except ValueError:
        pass
    return items


def run_daily(store: Store | None = None, today: date | None = None) -> dict:
    """Zet controlepunten klaar voor te controleren kennis; draft optioneel een concept."""
    store = store or get_store()
    today = today or date.today()
    items = review(today)

    bestaand = {c["summary"] for c in store.controlelijst("open", LOCAL_TENANT)}
    nieuw = 0
    for it in items:
        summary = f"Controleer: {it['onderwerp']} — {it['reden']} (bron: {it['bron']})"
        if summary not in bestaand:
            store.add_controlelijst("kennis", summary, it, tenant_id=LOCAL_TENANT)
            nieuw += 1

    # Optioneel: laat een LLM een concept-samenvatting maken (pending, niet toegepast).
    concept = None
    llm = get_llm()
    if getattr(llm, "name", "") != "rule_based":
        tekst = llm.complete(
            system="Je bent een Nederlandse fiscalist. Vat bondig en met bronnen samen, "
                   "geen advies dat zonder controle als zeker geldt.",
            prompt=f"Noem de belangrijkste fiscale wijzigingen voor Nederlandse "
                   f"ondernemers in {today.year}. Kort, met bron per punt.")
        if tekst:
            rule = LearningAgent(store).remember(
                f"[CONCEPT {today.isoformat()}] {tekst[:1500]}",
                source="llm-concept", domain="fiscaal", confidence=0.3,
                approved_by=None)            # fiscaal + geen goedkeuring => niet toegepast
            concept = rule.rule_id

    store.log(tenant_id=LOCAL_TENANT, actor="systeem",
              input="dagelijkse kennis-update", proposed_action="kennis_review",
              decision=f"{nieuw} controlepunt(en); concept={concept or 'geen'}")
    return {"controlepunten": nieuw, "concept_leerregel": concept,
            "te_controleren": [it["onderwerp"] for it in items]}
