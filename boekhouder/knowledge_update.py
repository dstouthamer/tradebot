"""Entrypoint voor de dagelijkse fiscale kennis-update.

Draai dagelijks via cron, bijvoorbeeld (op de server):

    0 7 * * *  cd /root/tradebot && docker compose exec -T app python -m boekhouder.knowledge_update

Het zet controlepunten klaar voor verouderde tarieven en (met LLM) een concept-
samenvatting van wijzigingen — altijd ter goedkeuring, nooit automatisch toegepast.
"""
from __future__ import annotations

import json
import logging

from boekhouder.config import get_settings
from boekhouder.knowledge import run_daily


def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    result = run_daily()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
