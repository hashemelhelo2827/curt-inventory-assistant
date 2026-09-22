import streamlit as st
import sys
import os
import asyncio
import pandas as pd
import uuid
import json
import time
from datetime import datetime
import streamlit.components.v1 as components

# Ensure curt is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase1.assistant_phase1 import handle_question as phase1_handle
from agent.tools.databaseserver.helper import get_db_connection

# Try to import Phase2 Chatbot, fallback to requests if backend running
try:
    from agent.model import Chatbot as phase2_chatbot
    HAS_DIRECT_PHASE2 = True
except:
    HAS_DIRECT_PHASE2 = False

import requests

# Global loop for Phase2 - reuses same loop to avoid httpx Event loop is closed, with TaskGroup fix via client.close() in agent/model.py
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

st.set_page_config(
    page_title="CURT Inventory Assistant",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Design Taste: Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --accent: #0ea5e9;
    --accent-hover: #0284c7;
    --bg: #fafaf9;
    --card: #ffffff;
    --border: #e7e5e4;
    --text: #1c1917;
    --muted: #78716c;
}

/* Global */
html, body, [class*="css"] {
    font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
}
h1, h2, h3 {
    font-family: 'Geist', sans-serif;
    letter-spacing: -0.02em;
    font-weight: 600;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Container width lock */
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #f5f5f4;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
div[data-testid="stChatMessage"][data-testid*="user"] {
    background: #1c1917;
    color: white;
    border-color: #1c1917;
}
div[data-testid="stChatMessage"][data-testid*="assistant"] {
    background: white;
}

/* Chat input */
div[data-testid="stChatInput"] {
    border-radius: 9999px;
    border: 1px solid var(--border);
    background: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

/* Buttons */
.stButton button {
    border-radius: 9999px;
    font-weight: 500;
    background: var(--accent);
    color: white;
    border: none;
    padding: 0.5rem 1.25rem;
    transition: all 0.2s;
}
.stButton button:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
}

/* Toggle / select */
div[data-testid="stSelectbox"] label {
    font-weight: 500;
    color: var(--text);
}

/* Metrics */
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}

/* Right Drawer */
.right-drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: 340px;
    height: 100vh;
    background: var(--card);
    border-left: 1px solid var(--border);
    box-shadow: -8px 0 24px rgba(0,0,0,0.08);
    transform: translateX(100%);
    transition: transform 0.28s cubic-bezier(.2,.8,.2,1);
    z-index: 1001;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.right-drawer.open {
    transform: translateX(0);
}
.drawer-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.12);
    backdrop-filter: blur(2px);
    z-index: 1000;
}
.drawer-header {
    padding: 1rem 1rem 0.75rem;
    border-bottom: 1px solid var(--border);
    background: var(--card);
}
.drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem;
}
.drawer-item {
    padding: 0.65rem 0.75rem;
    border-radius: 12px;
    border: 1px solid transparent;
    cursor: pointer;
    margin-bottom: 0.5rem;
    transition: all 0.15s;
    background: #fafaf9;
}
.drawer-item:hover {
    border-color: var(--border);
    background: white;
}
.drawer-item.active {
    background: #eef6ff;
    border-color: var(--accent);
}
.drawer-title {
    font-family: 'Geist', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.drawer-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    margin-top: 0.15rem;
}
.drawer-preview {
    font-size: 11px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 0.2rem;
}
.history-btn button {
    border-radius: 9999px !important;
    background: white !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-weight: 600 !important;
}
.history-btn button:hover {
    background: var(--text) !important;
    color: white !important;
}
.new-chat-btn button {
    background: var(--text) !important;
    color: white !important;
}
.history-btn { position: relative; z-index: 9999; }
header button[data-testid="stBaseButton-header"] { z-index: 1 !important; }
.drawer-open .block-container {
    padding-right: 360px;
}
@media (max-width: 900px) {
    .right-drawer { width: 100%; }
    .drawer-open .block-container { padding-right: 1rem; }
}

/* Header */
.curt-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.curt-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    background: white;
    border: 1px solid var(--border);
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
}
.curt-title {
    font-size: 2.5rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
    margin: 0;
    color: var(--text);
}
.curt-subtitle {
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 0.25rem;
    max-width: 60ch;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="curt-header">
    <div style="font-size: 2.5rem;">🏎️</div>
    <div>
        <div class="curt-badge">Cairo University Racing Team · Season 26–27</div>
        <h1 class="curt-title">CURT Inventory Assistant</h1>
        <div class="curt-subtitle">Ask about parts, locations, stock, or orders — rule-based or LLM-powered, live from the database.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Chat Store (frontend only, per-browser via localStorage + file fallback) ---
STORE_PATH = os.path.join(os.path.dirname(__file__), "chat_store.json")

def _load_store():
    try:
        if os.path.exists(STORE_PATH):
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except:
        pass
    return {"phase1": {}, "phase2": {}, "active_phase1": None, "active_phase2": None}

def _save_store():
    try:
        data = {
            "phase1": st.session_state.get("chats_phase1", {}),
            "phase2": st.session_state.get("chats_phase2", {}),
            "active_phase1": st.session_state.get("active_chat_id_phase1"),
            "active_phase2": st.session_state.get("active_chat_id_phase2"),
        }
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def _new_chat_id():
    return uuid.uuid4().hex[:8]

def _ensure_chat(phase_key):
    # phase_key: "phase1" or "phase2"
    chats = st.session_state[f"chats_{phase_key}"]
    active_key = f"active_chat_id_{phase_key}"
    active = st.session_state.get(active_key)
    if not active or active not in chats:
        nid = _new_chat_id()
        chats[nid] = {"id": nid, "title": "New chat", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": [], "conversation_history": []}
        st.session_state[active_key] = nid
        _save_store()
        return nid
    return active

def _get_active_chat(phase_key):
    chats = st.session_state.get(f"chats_{phase_key}", {})
    active = st.session_state.get(f"active_chat_id_{phase_key}")
    if active and active in chats:
        return chats[active]
    return None

# --- Session State ---
if "chats_phase1" not in st.session_state or "chats_phase2" not in st.session_state:
    _data = _load_store()
    # migrate legacy single-chat if exists
    legacy_messages = st.session_state.get("chat_messages", [])
    legacy_conv = st.session_state.get("conversation_history", [])
    if "chats_phase1" not in st.session_state:
        st.session_state.chats_phase1 = _data.get("phase1", {})
    if "chats_phase2" not in st.session_state:
        st.session_state.chats_phase2 = _data.get("phase2", {})
    if "active_chat_id_phase1" not in st.session_state:
        st.session_state.active_chat_id_phase1 = _data.get("active_phase1")
    if "active_chat_id_phase2" not in st.session_state:
        st.session_state.active_chat_id_phase2 = _data.get("active_phase2")
    # seed legacy if both empty and legacy has data
    if not st.session_state.chats_phase1 and not st.session_state.chats_phase2 and legacy_messages:
        nid = _new_chat_id()
        st.session_state.chats_phase1[nid] = {"id": nid, "title": (legacy_messages[0]["content"][:32] if legacy_messages else "New chat"), "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": list(legacy_messages), "conversation_history": list(legacy_conv)}
        st.session_state.active_chat_id_phase1 = nid
        nid2 = _new_chat_id()
        st.session_state.chats_phase2[nid2] = {"id": nid2, "title": "New chat", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": [], "conversation_history": []}
        st.session_state.active_chat_id_phase2 = nid2
        _save_store()
    # ensure at least one chat per phase
    if not st.session_state.chats_phase1:
        nid = _new_chat_id()
        st.session_state.chats_phase1[nid] = {"id": nid, "title": "New chat", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": [], "conversation_history": []}
        st.session_state.active_chat_id_phase1 = nid
    if not st.session_state.chats_phase2:
        nid = _new_chat_id()
        st.session_state.chats_phase2[nid] = {"id": nid, "title": "New chat", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": [], "conversation_history": []}
        st.session_state.active_chat_id_phase2 = nid
    if not st.session_state.active_chat_id_phase1:
        st.session_state.active_chat_id_phase1 = list(st.session_state.chats_phase1.keys())[0]
    if not st.session_state.active_chat_id_phase2:
        st.session_state.active_chat_id_phase2 = list(st.session_state.chats_phase2.keys())[0]
    _save_store()

if "drawer_open" not in st.session_state:
    st.session_state.drawer_open = False
if "chat_search" not in st.session_state:
    st.session_state.chat_search = ""
# legacy compat for old code paths
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# --- Sidebar: Live Inventory ---
with st.sidebar:
    st.markdown("### 📦 Live Inventory")
    st.caption("Pulled live from `database/curt_inventory.db` — for demo/debugging.")
    
    # Toggle Phase
    phase = st.selectbox(
        "Assistant Mode",
        ["Phase 2 — LLM (Mistral nemo/tiny)", "Phase 1 — Rule-based"],
        index=0,
        help="Switch without restarting. Phase 1 uses keyword matching, Phase 2 uses Mistral with function calling."
    )
    is_phase1 = phase.startswith("Phase 1")
    
    st.divider()
    
    # Quick stats
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as c FROM CORE_PART_INFO")
            total_parts = cur.fetchone()["c"]
            cur.execute("SELECT SUM(quantity) as s FROM CORE_PART_INFO")
            total_qty = cur.fetchone()["s"] or 0
            cur.execute("SELECT COUNT(*) as c FROM CORE_PART_INFO WHERE quantity < 2")
            low = cur.fetchone()["c"]
        col1, col2 = st.columns(2)
        col1.metric("Part Models", total_parts)
        col2.metric("Low Stock <2", low)
        st.caption(f"Total units: {total_qty}")
    except Exception as e:
        st.error(f"DB error: {e}")
    
    # Inventory table
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.part_number, c.part_name, c.quantity, c.category, 
                       GROUP_CONCAT(DISTINCT p.car_position) as positions
                FROM CORE_PART_INFO c
                LEFT JOIN PART p ON p.part_number = c.part_number
                GROUP BY c.part_number
                ORDER BY c.category, c.part_name
            """)
            rows = [dict(r) for r in cur.fetchall()]
            if rows:
                df = pd.DataFrame(rows)
                df.columns = ["Part #", "Name", "Qty", "Category", "Positions"]
                st.dataframe(df, use_container_width=True, hide_index=True, height=280)
            else:
                st.info("No parts found.")
    except Exception as e:
        st.error(f"Table error: {e}")
    
    # Expandable panels
    with st.expander("Critical Parts"):
        try:
            from agent.tools.databaseserver.databasetools import get_critical_parts
            crit = get_critical_parts()
            if crit:
                for r in crit[:5]:
                    st.write(f"**{r['part_name']}** ({r['category']}) — next: {r['next_inspection_due']}")
            else:
                st.write("No critical parts.")
        except Exception as e:
            st.write(f"Error: {e}")
    
    with st.expander("Due Inspections"):
        try:
            from agent.tools.databaseserver.databasetools import get_due_inspections
            due = get_due_inspections()
            if due:
                for r in due[:5]:
                    st.write(f"**{r['part_name']}** [{r['part_id']}] — {r['next_inspection_due']}")
            else:
                st.write("No overdue inspections.")
        except Exception as e:
            st.write(f"Error: {e}")
    
    st.divider()
    # Clear active chat only (per-phase)
    if st.button("Clear Active Chat"):
        _pk = "phase1" if is_phase1 else "phase2"
        _chat = _get_active_chat(_pk)
        if _chat:
            _chat["messages"] = []
            _chat["conversation_history"] = []
            _chat["title"] = "New chat"
            _chat["updated_at"] = datetime.now().isoformat()
            _save_store()
        st.rerun()
    
    st.caption("Backend: Flask `POST /chat` + `GET /inventory` · LLM: Mistral nemo/tiny via `api.mistral.ai/v1` · DB: SQLite")

# --- Top Bar with History Toggle ---
st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
_top_col1, _top_col2 = st.columns([5, 1])
with _top_col2:
    st.markdown('<div class="history-btn" style="position:relative; z-index:10;">', unsafe_allow_html=True)
    if st.button("🕘 History", key="toggle_drawer", use_container_width=True):
        st.session_state.drawer_open = not st.session_state.drawer_open
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Right Drawer State ---
phase_key = "phase1" if is_phase1 else "phase2"
active_chat = _get_active_chat(phase_key)
if active_chat is None:
    _ensure_chat(phase_key)
    active_chat = _get_active_chat(phase_key)

# Sync to localStorage (per-browser) + file already saved
try:
    _p1_json = json.dumps(st.session_state.chats_phase1)
    _p2_json = json.dumps(st.session_state.chats_phase2)
    _a1 = st.session_state.active_chat_id_phase1
    _a2 = st.session_state.active_chat_id_phase2
    components.html(f"""
    <script>
    try {{
        localStorage.setItem('curt_phase1_v1', JSON.stringify({_p1_json}));
        localStorage.setItem('curt_phase2_v1', JSON.stringify({_p2_json}));
        localStorage.setItem('curt_active_phase1', "{_a1}");
        localStorage.setItem('curt_active_phase2', "{_a2}");
    }} catch(e) {{}}
    </script>
    """, height=0)
except:
    pass

# --- Layout: Main + Right Slide Menu ---
if st.session_state.drawer_open:
    col_main, col_drawer = st.columns([2.7, 1.3], gap="large")
else:
    col_main = st.container()
    col_drawer = None

# Drawer content (right)
if col_drawer is not None:
    with col_drawer:
        st.markdown('<div style="position:sticky; top:1rem; background:white; border:1px solid var(--border); border-radius:16px; padding:1rem; box-shadow:0 4px 12px rgba(0,0,0,0.06); max-height:85vh; overflow-y:auto;">', unsafe_allow_html=True)
        st.markdown(f"**{'Phase 1' if is_phase1 else 'Phase 2'} History**")
        st.caption(f"{len(st.session_state[f'chats_{phase_key}'])} chats · per-phase · survives refresh")
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
        if st.button("＋ New chat", key="new_chat_btn", use_container_width=True):
            nid = _new_chat_id()
            st.session_state[f"chats_{phase_key}"][nid] = {"id": nid, "title": "New chat", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "messages": [], "conversation_history": []}
            st.session_state[f"active_chat_id_{phase_key}"] = nid
            _save_store()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.text_input("Search", placeholder="Filter chats…", key="chat_search", label_visibility="collapsed")
        _q = st.session_state.chat_search.lower().strip()
        _sorted = sorted(st.session_state[f"chats_{phase_key}"].values(), key=lambda x: x.get("updated_at",""), reverse=True)
        if _q:
            _sorted = [c for c in _sorted if _q in c.get("title","").lower() or _q in " ".join([m.get("content","") for m in c.get("messages",[])][:2]).lower()]
        if not _sorted:
            st.caption("No chats yet.")
        else:
            for _c in _sorted:
                _is_active = _c["id"] == st.session_state[f"active_chat_id_{phase_key}"]
                _title = _c.get("title","New chat")
                _msgs = _c.get("messages",[])
                if _msgs:
                    _preview = _msgs[0]["content"][:38] + ("…" if len(_msgs[0]["content"])>38 else "")
                else:
                    _preview = "No messages yet"
                _count = len(_msgs)
                _ts = _c.get("updated_at","")[:16].replace("T"," ")
                # Card style
                with st.container(border=True):
                    label = f"{'● ' if _is_active else ''}{_title}"
                    if st.button(label, key=f"switch_{phase_key}_{_c['id']}", use_container_width=True, help=_preview):
                        st.session_state[f"active_chat_id_{phase_key}"] = _c["id"]
                        _save_store()
                        st.rerun()
                    st.caption(f"{_count} msgs · {_ts}")
                    if _count:
                        st.markdown(f'<div class="drawer-preview">{_preview}</div>', unsafe_allow_html=True)
                    if st.button("Delete", key=f"del_{phase_key}_{_c['id']}", use_container_width=True):
                        if len(st.session_state[f"chats_{phase_key}"]) <= 1:
                            _c["messages"] = []
                            _c["conversation_history"] = []
                            _c["title"] = "New chat"
                            _c["updated_at"] = datetime.now().isoformat()
                        else:
                            was_active = _is_active
                            del st.session_state[f"chats_{phase_key}"][_c["id"]]
                            if was_active:
                                newest = sorted(st.session_state[f"chats_{phase_key}"].values(), key=lambda x: x.get("updated_at",""), reverse=True)[0]
                                st.session_state[f"active_chat_id_{phase_key}"] = newest["id"]
                        _save_store()
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Main Chat Display (per-phase active chat) ---
active_messages = active_chat.get("messages", []) if active_chat else []
with col_main:
    for msg in active_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # Suggested prompts (only when active chat empty)
    if not active_messages:
        st.markdown("**Try asking:**")
        cols = st.columns(3)
        suggestions = [
            "How many brake calipers do we have?",
            "Where is the ECU?",
            "List all items in Brakes",
        ]
        for i, s in enumerate(suggestions):
            if cols[i].button(s, use_container_width=True):
                st.session_state.pending_prompt = s
                st.rerun()

# --- Chat Input ---
prompt = st.chat_input("Ask about CURT inventory...")
# Handle suggestion click
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    # Add user message to active chat (per-phase)
    if active_chat.get("title") == "New chat":
        active_chat["title"] = prompt[:32] + ("…" if len(prompt) > 32 else "")
    active_chat["messages"].append({"role": "user", "content": prompt})
    active_chat["updated_at"] = datetime.now().isoformat()
    # keep legacy conversation_history in sync for phase2
    _save_store()
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Checking inventory..."):
            try:
                if is_phase1:
                    # Phase 1 direct -> per-phase active chat
                    reply = phase1_handle(prompt)
                    st.markdown(reply)
                    active_chat["messages"].append({"role": "assistant", "content": reply})
                    active_chat["conversation_history"].append({"role": "user", "content": prompt})
                    active_chat["conversation_history"].append({"role": "assistant", "content": reply})
                    active_chat["updated_at"] = datetime.now().isoformat()
                    _save_store()
                else:
                    # Phase 2: try direct Chatbot first (no backend needed), fallback to backend HTTP if direct fails
                    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:5000/chat")
                    # Use active chat's conversation_history (separated per chat)
                    conv_hist = active_chat.get("conversation_history", [])
                    if HAS_DIRECT_PHASE2:
                        try:
                            resp, new_hist = _loop.run_until_complete(
                                phase2_chatbot(prompt, conv_hist)
                            )
                            import json as _json
                            try:
                                j = _json.loads(resp)
                                answer = j.get("answer", resp)
                                items = j.get("items", [])
                                status = j.get("status", "success")
                                if status == "not_found":
                                    st.warning(answer)
                                else:
                                    st.markdown(answer)
                                if items:
                                    for it in items[:10]:
                                        st.markdown(f"- {it}")
                                active_chat["messages"].append({"role": "assistant", "content": answer + ("" if not items else "\n\n" + "\n".join(f"- {x}" for x in items))})
                            except:
                                clean = resp.strip()
                                if clean.startswith("```"):
                                    clean = clean.strip("`").replace("json", "", 1).strip()
                                    try:
                                        j = _json.loads(clean)
                                        st.markdown(j.get("answer", clean))
                                        if j.get("items"):
                                            for it in j["items"]:
                                                st.markdown(f"- {it}")
                                        active_chat["messages"].append({"role": "assistant", "content": j.get("answer", clean)})
                                    except:
                                        st.markdown(clean)
                                        active_chat["messages"].append({"role": "assistant", "content": clean})
                                else:
                                    st.markdown(clean)
                                    active_chat["messages"].append({"role": "assistant", "content": clean})
                            active_chat["conversation_history"] = new_hist
                            active_chat["updated_at"] = datetime.now().isoformat()
                            _save_store()
                        except Exception as e:
                            raise e
                    else:
                        r = requests.post(backend_url, json={"message": prompt}, timeout=40)
                        r.raise_for_status()
                        data = r.json()
                        resp = data.get("response", "")
                        import json as _json2
                        j = _json2.loads(resp)
                        st.markdown(j.get("answer", resp))
                        if j.get("items"):
                            for it in j["items"]:
                                st.markdown(f"- {it}")
                        active_chat["messages"].append({"role": "assistant", "content": j.get("answer", resp)})
                        active_chat["conversation_history"].append({"role": "user", "content": prompt})
                        active_chat["conversation_history"].append({"role": "assistant", "content": resp})
                        active_chat["updated_at"] = datetime.now().isoformat()
                        _save_store()
            except Exception as e:
                err_msg = f"Error: {str(e)[:300]}"
                st.error(err_msg)
                active_chat["messages"].append({"role": "assistant", "content": err_msg})
                active_chat["updated_at"] = datetime.now().isoformat()
                _save_store()

# Footer
st.divider()
st.caption("CURT26-27 · Phase 1 rule-based + Phase 2 LLM (Mistral) · Toggle via sidebar · Inventory live from SQLite")
