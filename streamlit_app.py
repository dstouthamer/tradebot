"""AI Boekhouder — MVP dashboard.

Run:  streamlit run streamlit_app.py

A thin UI over the same ``Router``: chat box, controlelijst of uncertain items, and the
audit trail. Concept-only; finalising happens through the explicit confirm button.
"""
from __future__ import annotations

import streamlit as st

from boekhouder.engine.router import Router
from boekhouder.store import get_store

st.set_page_config(page_title="AI Boekhouder", page_icon="📊", layout="wide")


@st.cache_resource
def _router() -> Router:
    return Router()


router = _router()
store = get_store()

st.title("📊 AI Boekhouder — concept-modus")
st.caption("Niets wordt definitief geboekt of verzonden zonder jouw bevestiging.")

col_chat, col_side = st.columns([2, 1])

with col_chat:
    st.subheader("Chat")
    msg = st.text_input("Bericht", placeholder="Maak factuur voor De Vries airco montage 1850 ex btw")
    c1, c2 = st.columns(2)
    if c1.button("Verstuur", use_container_width=True) and msg:
        reply = router.handle(msg, session_id="dashboard")
        st.session_state["last"] = reply
    if c2.button("✅ Bevestig concept", use_container_width=True):
        st.session_state["last_confirm"] = router.gate.confirm("dashboard")

    last = st.session_state.get("last")
    if last:
        zone_color = {"GROEN": "🟢", "ORANJE": "🟠", "ROOD": "🔴"}.get(last.risk_zone.value, "⚪")
        st.markdown(f"**{zone_color} {last.agent}**")
        st.code(last.text, language="text")
        if last.requires_confirmation:
            st.info("Dit is een concept — klik **Bevestig concept** om definitief te maken.")
    if st.session_state.get("last_confirm"):
        st.success(st.session_state["last_confirm"].get("message", ""))

with col_side:
    st.subheader("Controlelijst")
    items = store.controlelijst()
    if not items:
        st.write("Geen openstaande controlepunten.")
    for it in items:
        st.warning(f"[{it['kind']}] {it['summary']}")

    st.subheader("Audit trail")
    for row in store.audit_trail(15):
        st.text(f"{row['ts'][:19]} · {row['proposed_action']} · {row['decision']}")
