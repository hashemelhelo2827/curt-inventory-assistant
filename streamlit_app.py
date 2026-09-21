import streamlit as st
import sys
import os
import asyncio
import pandas as pd
from datetime import datetime

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

# Global event loop for Phase2 (like backend/app.py:19 - avoids 'Event loop is closed' with httpx/anyio)
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

# --- Session State ---
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []  # for backend-style history
if "phase1_history" not in st.session_state:
    st.session_state.phase1_history = []  # list of (role, content)
if "phase2_history" not in st.session_state:
    st.session_state.phase2_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []  # for Streamlit chat display: list of dict {role, content}

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
    if st.button("Clear Chat"):
        st.session_state.conversation_history = []
        st.session_state.phase1_history = []
        st.session_state.phase2_history = []
        st.session_state.chat_messages = []
        st.rerun()
    
    st.caption("Backend: Flask `POST /chat` + `GET /inventory` · LLM: Mistral nemo/tiny via `api.mistral.ai/v1` · DB: SQLite")

# --- Main Chat Display ---
# Show history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Suggested prompts (only when empty)
if not st.session_state.chat_messages:
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
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Checking inventory..."):
            try:
                if is_phase1:
                    # Phase 1 direct
                    reply = phase1_handle(prompt)
                    # Phase 1 returns plain text, wrap as JSON-like for consistency
                    # But spec says return clear answer - keep as is
                    st.markdown(reply)
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    st.session_state.phase1_history.append({"role": "user", "content": prompt})
                    st.session_state.phase1_history.append({"role": "assistant", "content": reply})
                else:
                    # Phase 2: try direct Chatbot first (no backend needed), fallback to backend HTTP if direct fails
                    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:5000/chat")
                    # Try direct import (faster, no network)
                    if HAS_DIRECT_PHASE2:
                        try:
                            # Use global loop (like backend/app.py:19) - avoids Event loop is closed
                            resp, new_hist = _loop.run_until_complete(
                                phase2_chatbot(prompt, st.session_state.conversation_history)
                            )
                            # resp is JSON string like {"answer": "...", "items": [], "status": "success"}
                            # Try to parse for pretty display
                            import json
                            try:
                                j = json.loads(resp)
                                # Pretty display
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
                                # Store raw for history
                                st.session_state.chat_messages.append({"role": "assistant", "content": answer + ("" if not items else "\n\n" + "\n".join(f"- {x}" for x in items))})
                            except:
                                # Fallback: show raw (may have markdown fencing)
                                # Strip ```json fences if present
                                clean = resp.strip()
                                if clean.startswith("```"):
                                    clean = clean.strip("`").replace("json", "", 1).strip()
                                    try:
                                        j = json.loads(clean)
                                        st.markdown(j.get("answer", clean))
                                        if j.get("items"):
                                            for it in j["items"]:
                                                st.markdown(f"- {it}")
                                        st.session_state.chat_messages.append({"role": "assistant", "content": j.get("answer", clean)})
                                    except:
                                        st.markdown(clean)
                                        st.session_state.chat_messages.append({"role": "assistant", "content": clean})
                                else:
                                    st.markdown(clean)
                                    st.session_state.chat_messages.append({"role": "assistant", "content": clean})
                            st.session_state.conversation_history = new_hist
                            st.session_state.phase2_history = new_hist
                        except Exception as e:
                            # Fallback to backend HTTP
                            raise e
                    else:
                        # Direct not available, use backend HTTP
                        r = requests.post(backend_url, json={"message": prompt}, timeout=40)
                        r.raise_for_status()
                        data = r.json()
                        resp = data.get("response", "")
                        import json
                        j = json.loads(resp)
                        st.markdown(j.get("answer", resp))
                        if j.get("items"):
                            for it in j["items"]:
                                st.markdown(f"- {it}")
                        st.session_state.chat_messages.append({"role": "assistant", "content": j.get("answer", resp)})
                        # For backend, history is stored server-side via session, but also keep local
                        st.session_state.conversation_history.append({"role": "user", "content": prompt})
                        st.session_state.conversation_history.append({"role": "assistant", "content": resp})
            except Exception as e:
                err_msg = f"Error: {str(e)[:300]}"
                st.error(err_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": err_msg})

# Footer
st.divider()
st.caption("CURT26-27 · Phase 1 rule-based + Phase 2 LLM (Mistral) · Toggle via sidebar · Inventory live from SQLite")
