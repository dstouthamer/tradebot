"""AI Boekhouder REST API (pattern from apex/api/main.py).

Endpoints power the dashboard, a Telegram webhook, and any external client. Everything
stays concept-only and confirmation-gated.

Run:  uvicorn boekhouder.api.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from boekhouder.config import get_settings
from boekhouder.engine.router import Router
from boekhouder.store import get_store

app = FastAPI(
    title="AI Boekhouder API",
    version="0.1.0-mvp",
    description="Nederlandse AI-boekhoud-, CFO- en fiscale optimalisatie-agent. "
                "Concept-only en bevestiging-gated by design.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_router: Router | None = None


def router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router


class BerichtRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}


@app.get("/config")
async def config():
    s = get_settings()
    return {
        "company": s.company_name,
        "require_confirmation": s.require_confirmation,
        "allow_auto_send": s.allow_auto_send,
        "integrations": {
            "telegram": s.has_telegram,
            "moneybird": s.has_moneybird,
            "llm": s.has_llm,
            "ocr": s.ocr_provider,
        },
    }


@app.post("/bericht")
async def bericht(req: BerichtRequest):
    reply = router().handle(req.message, session_id=req.session_id)
    return {
        "text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
        "requires_confirmation": reply.requires_confirmation, "blocked": reply.blocked,
    }


@app.post("/upload")
async def upload(file: UploadFile, session_id: str = "default", supplier: str = "",
                 project: str = ""):
    """Upload a bonnetje (image/pdf) or a bank export. Bank files are detected by suffix."""
    content = await file.read()
    name = (file.filename or "").lower()
    if name.endswith((".xml", ".mt940", ".sta", ".csv", ".940")):
        text = content.decode("utf-8", errors="replace")
        reply = router().handle("importeer bankafschrift", session_id=session_id,
                                file_content=text)
    else:
        msg = f"bonnetje {supplier} project {project}".strip()
        reply = router().handle(msg, session_id=session_id, image_bytes=content)
    return {"text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
            "requires_confirmation": reply.requires_confirmation}


@app.post("/approve")
async def approve(session_id: str = "default"):
    return router().gate.confirm(session_id)


@app.get("/controlelijst")
async def controlelijst():
    return get_store().controlelijst()


@app.get("/audit")
async def audit(limit: int = 100):
    return get_store().audit_trail(limit)


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    """Webhook variant of the Telegram intake (alternative to long-poll worker)."""
    from boekhouder.providers.telegram import TelegramChannel

    channel = TelegramChannel()
    msg = update.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = msg.get("text") or msg.get("caption") or ""
    image_bytes = None
    if msg.get("photo"):
        file_id = msg["photo"][-1]["file_id"]
        image_bytes = channel.download_photo(file_id)
        if not text:
            text = "bonnetje"
    reply = router().handle(text, session_id=chat_id, image_bytes=image_bytes)
    channel.send(chat_id, reply.text)
    return {"ok": True}
