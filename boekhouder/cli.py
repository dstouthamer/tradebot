"""Interactive Dutch chat REPL — the keyless demo surface.

Run:  python -m boekhouder.cli
Type a message like the masterprompt examples; type 'quit' to exit. A bank export can
be loaded with:  /bank <path-to-file>
"""
from __future__ import annotations

import sys

from boekhouder.engine.router import Router


def _banner() -> str:
    return (
        "AI Boekhouder — concept-modus (niets wordt definitief zonder jouw 'ja').\n"
        "Tip: voor de web-app met inloggen draai 'uvicorn boekhouder.api.main:app' "
        "en open http://localhost:8000/\n"
        "Stuur mij je eerste bon, factuur, banktransactie, offerteverzoek of "
        "factuuropdracht.\nVoorbeelden:\n"
        "  Maak factuur voor De Vries airco montage 1850 ex btw\n"
        "  Bonnetje Gamma project Jansen warmtepomp 124,80\n"
        "  Maak offerte hybride warmtepomp Apeldoorn 6500 incl btw\n"
        "  Hoeveel btw moet ik betalen dit kwartaal?\n"
        "  Geef een prognose voor de komende maanden\n"
        "  /bank pad/naar/afschrift.csv\n"
        "  (typ 'quit' om te stoppen)\n"
    )


def main() -> None:
    router = Router()
    print(_banner())
    while True:
        try:
            msg = input("» ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg:
            continue
        if msg.lower() in ("quit", "exit", "stop"):
            break
        file_content = None
        if msg.startswith("/bank "):
            path = msg[len("/bank "):].strip()
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    file_content = fh.read()
            except OSError as exc:
                print(f"Kan bestand niet lezen: {exc}\n")
                continue
            msg = "importeer bankafschrift"
        reply = router.handle(msg, file_content=file_content)
        print(f"\n{reply.text}\n")
        print(f"[{reply.agent} · {reply.risk_zone.value}"
              + (" · bevestiging nodig" if reply.requires_confirmation else "") + "]\n")


if __name__ == "__main__":
    sys.exit(main())
