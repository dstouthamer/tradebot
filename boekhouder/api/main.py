"""AI Boekhouder REST API (pattern from apex/api/main.py).

Multi-tenant: de administratie-endpoints vereisen een Bearer-token (zie /auth). Elke
gebruiker werkt strikt binnen de eigen tenant. Alles blijft concept-only en
bevestiging-gated.

Run:  uvicorn boekhouder.api.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from boekhouder.api.auth_api import current_session
from boekhouder.api.auth_api import router as auth_router
from boekhouder.auth.service import Session
from boekhouder.config import get_settings
from boekhouder.engine.router import Router
from boekhouder.store import LOCAL_TENANT, get_store

app = FastAPI(
    title="AI Boekhouder API",
    version="0.2.0-mvp",
    description="Nederlandse AI-boekhoud-, CFO- en fiscale optimalisatie-agent. "
                "Multi-tenant, concept-only en bevestiging-gated by design.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)

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
        "require_confirmation": s.require_confirmation,
        "allow_auto_send": s.allow_auto_send,
        "allow_signup": s.allow_signup,
        "integrations": {
            "telegram": s.has_telegram, "moneybird": s.has_moneybird, "llm": s.has_llm,
            "ocr": s.ocr_provider, "google_login": s.has_google_oauth,
            "microsoft_login": s.has_microsoft_oauth, "idin_login": s.has_idin,
        },
    }


@app.post("/bericht")
async def bericht(req: BerichtRequest, session: Session = Depends(current_session)):
    reply = router().handle(req.message, session_id=req.session_id, tenant_id=session.tenant_id)
    return {
        "text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
        "requires_confirmation": reply.requires_confirmation, "blocked": reply.blocked,
    }


@app.post("/upload")
async def upload(file: UploadFile, session_id: str = "default", supplier: str = "",
                 project: str = "", session: Session = Depends(current_session)):
    """Upload a bonnetje (image/pdf) or a bank export. Bank files are detected by suffix."""
    content = await file.read()
    name = (file.filename or "").lower()
    if name.endswith((".xml", ".mt940", ".sta", ".csv", ".940")):
        reply = router().handle("importeer bankafschrift", session_id=session_id,
                                tenant_id=session.tenant_id,
                                file_content=content.decode("utf-8", errors="replace"))
    else:
        msg = f"bonnetje {supplier} project {project}".strip()
        reply = router().handle(msg, session_id=session_id, tenant_id=session.tenant_id,
                                image_bytes=content)
    return {"text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
            "requires_confirmation": reply.requires_confirmation}


@app.post("/approve")
async def approve(session_id: str = "default", session: Session = Depends(current_session)):
    return router().gate.confirm(session_id, tenant_id=session.tenant_id)


@app.get("/controlelijst")
async def controlelijst(session: Session = Depends(current_session)):
    return get_store().controlelijst(tenant_id=session.tenant_id)


@app.get("/audit")
async def audit(limit: int = 100, session: Session = Depends(current_session)):
    return get_store().audit_trail(limit, tenant_id=session.tenant_id)


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    """Telegram intake (single-bot = single company -> local tenant). Zie docs."""
    from boekhouder.providers.telegram import TelegramChannel

    channel = TelegramChannel()
    msg = update.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = msg.get("text") or msg.get("caption") or ""
    image_bytes = None
    if msg.get("photo"):
        image_bytes = channel.download_photo(msg["photo"][-1]["file_id"])
        text = text or "bonnetje"
    reply = router().handle(text, session_id=chat_id, tenant_id=LOCAL_TENANT,
                            image_bytes=image_bytes)
    channel.send(chat_id, reply.text)
    return {"ok": True}
