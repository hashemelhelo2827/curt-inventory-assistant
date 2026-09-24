# CURT Inventory Assistant — Season 26-27

Cairo University Racing Team (Formula Student) — Generative AI Task. Small assistant that answers natural-language questions about CURT's parts inventory, live from SQLite, via rule-based Phase 1 and LLM-powered Phase 2 with Streamlit.

**Live Demo:** [_Streamlit Cloud link _](https://curt-inventory-assistant-sywpcv8sqmm8w2djbyrvdm.streamlit.app/)  
**Video:** _Add Google Drive link (2-5 min)_

---

## Architecture

```
Streamlit (streamlit_app.py) — pure frontend, no direct DB/MCP (PDF p3 Security)
    │  POST /chat {message, phase, history}  →  Flask backend/app.py:21 (POST /chat)
    │  GET /inventory                          →  Flask backend/app.py:46 (GET /inventory)
    └─ phase toggle ─┘                            │
                   Backend Flask (single source) ─┤
                        ├─ phase1: phase1/assistant_phase1.py (rule-based parser, no LLM)
                        └─ phase2: agent/model.py (MCP + Mistral) ── MCP stdio → agent/tools/databaseserver/databasetools.py
                                                                └─ helper.py → database/curt_inventory.db (SQLite)

Inventory tables: CORE_PART_INFO (part_number, part_name, quantity, category) + PART + STATUS_CONDITION + LIFECYCLE_TRACKING + ORDERS + SUPPLIER_INFO
```

- **Streamlit** pure frontend `streamlit_app.py` — chat + `chat_input`/`chat_message` scrolling, per-chat drawer `chat_store.json` + `localStorage`, toggle `Phase 1/2` without restart, sidebar live table via `GET /inventory` `BACKEND_URL` `streamlit_app.py:434`, supplier message formatting. No `from agent.model import Chatbot`, no direct `sqlite` — PDF p3 `LLM must not have direct access to DB`.
- **Backend** Flask **mandatory** `POST /chat` (`{message, phase, history}` + `flask_session` cookie → `Chatbot` → `{"response": str, "history": list}`) and `GET|POST /inventory` + `GET /health` `backend/app.py:46`. Conversation memory `flask_session` filesystem per-session + `MAX_HISTORY=20` `agent/model.py:308` for follow-up `Where are they stored?` after `How many brake pads?` PDF p4.
- **MCP Tools** `databasetools.py` via `MultiServerMCPClient` `agent/model.py:165` `DATABASE_TOOLS` stdio `python agent/tools/databaseserver/databasetools.py`. Tools: `get_by_name`, `get_by_part_number`, `get_by_category`, `get_part_status` (where is), `get_part_info` (how many), `get_all_parts`, `get_all_categories`, `get_all_suppliers`, `get_orders_by_*`, `get_supplier_by_*`, `get_low_stock(threshold)`, `flag_shortage(item_name, threshold=2)` (logs `LOW STOCK FLAG`, per spec), `get_critical_parts`, `get_due_inspections`.
- **LLM** Mistral `open-mistral-nemo` / `mistral-tiny` `https://api.mistral.ai/v1` `ChatOpenAI` `agent/model.py:23` `model_kwargs={"parallel_tool_calls": True}`. `SYSTEM_PROMPT` Rule 9 `may chain`, `recursion_limit:12` `agent/model.py:373`, `global _loop` `backend/app.py:18` + `global _global_mcp_client` `agent/model.py:159` single `TaskGroup` (avoids per-turn spawn/close race).

## Tech Stack

- **DB:** SQLite (`database/curt_inventory.db`) — can swap MySQL/PostgreSQL (spec allows).
- **Backend:** Flask, flask_session, LangChain, langchain-openai, langchain-mcp-adapters, langgraph.
- **Frontend:** Streamlit, pandas.
- **LLM:** Mistral API (free tier, 188 req/min, 625k TPM) — also supports Gemini via same ChatOpenAI base_url `https://generativelanguage.googleapis.com/v1beta/openai/` (needs `thought_signature` handling).

## Local Setup

```powershell
# 1. Clone
git clone https://github.com/<you>/curt-inventory-assistant.git
cd curt-inventory-assistant

# 2. Venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Env
copy .env.example .env
# Edit .env: Mistral_API_key=..., Mistral_API_key2=... (from https://console.mistral.ai)

# 4. DB seeding (if empty)
# database/curt_inventory.db is seeded with 10 parts: Brake Caliper, Brake Disc, ECU, Engine, Front Wing Assembly, Monocoque, Rear Wing, Rim Set, Steering Rack, Suspension Arm
# To re-seed:
python -c "import sqlite3; print('DB at database/curt_inventory.db with', sqlite3.connect('database/curt_inventory.db').execute('SELECT COUNT(*) FROM CORE_PART_INFO').fetchone()[0], 'parts')"

# 5. Run backend (required — PDF p3 LLM not direct DB, Streamlit is pure frontend)
$env:PYTHONPATH="."; python backend/app.py
# -> http://0.0.0.0:5000 (Railway uses $PORT)

# 6. Run Streamlit (needs backend up)
# Set BACKEND_URL if not default
$env:BACKEND_URL="http://127.0.0.1:5000"; streamlit run streamlit_app.py
# -> http://localhost:8501 (calls backend POST /chat + GET /inventory)
# Verify backend: curl http://127.0.0.1:5000/health -> {"status":"ok"}
#               curl http://127.0.0.1:5000/inventory -> {"status":"success","parts": [...]}
```

## API Endpoints

### POST /chat
Accepts `{"message": "Where is the ECU?"}` + session cookie, returns `{"response": "{\"answer\": \"...\", \"items\": [], \"status\": \"success\"}"}`.

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/chat -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"message":"How many brake calipers do we have?"}' -SessionVariable s
# Follow-up with history:
Invoke-WebRequest -Uri http://127.0.0.1:5000/chat -Method POST -Headers @{'Content-Type'='application/json'} -Body '{"message":"Where are they stored?"}' -WebSession $s
```

### GET /inventory
`GET` (spec) + `POST` (backward compat) `backend/app.py:46` `methods=["GET","POST"]` returns `{"status":"success","parts": [...]}` via `_fetch_all_parts` `helper.py:45`. `GET` ignores body, `POST` allows empty body.

## Tool Calling Definitions

Defined in `agent/tools/databaseserver/databasetools.py` (MCP):

- `get_by_name(part_name)` — general lookup; **for `where is` use `get_part_status`**.
- `get_part_status(part_name)` — `Use for 'where is' and location queries. Returns location, assigned_to, condition, status` helper.py:65.
- `get_part_info(part_name)` — `Use for 'how many' quantity queries. Handles singular/plural` databasetools.py:83.
- `get_by_category(category)` — `Use for 'list all items in <category>'`.
- `get_all_parts()` — `Use for 'show all parts'` → `[dict(row) for ...]` helper.py:15.
- `get_all_categories()` — distinct categories.
- `get_all_suppliers()` — `Use for 'list all suppliers'` → `id, name, contact_name, email, phone_number, website, governorate, parts_supplied[]` `databasetools.py:174`.
- `get_orders_by_part_number / get_supplier_by_*`, `get_low_stock(threshold)`, `flag_shortage(item_name, threshold=2)` — logs `LOW STOCK FLAG: {part} x{qty} < {thr}` per spec `pdf:3` `databasetools.py:126`, `get_critical_parts`, `get_due_inspections`.

LLM decides via `SYSTEM_PROMPT` Tool Routing `agent/model.py:267` + `parallel_tool_calls: True` `agent/model.py:85` — may chain multiple tools per turn, `recursion_limit:12`.

## Edge-Case Handling

- **Not in DB:** `flux capacitor` → `{"status":"not_found","answer":"I couldn't find flux capacitor in the inventory."}` SYSTEM_PROMPT Rule 3.
- **Misspelling/partial:** `brak caliper` → `get_part_info` strips trailing `s` and uses `LOWER(?)` IN `(?, singular)` → `2 Brake Calipers` (handles `brake calipers`/`brake caliper`).
- **Ambiguous/no item:** `how many do we have?` → uses `conversation_history` `MAX_HISTORY=20` `agent/model.py:306` to resolve from prior `brake calipers` context → same answer, not `Event loop is closed`.
- **API limits:** `mistral-small` hit `429 code 1300 RPM 0/0`; switched to `nemo`/`tiny` `188/625k`. `helper.py` returns `[dict(row)]` to avoid `<sqlite3.Row object>` dump.
- **Event loop:** Global `_loop` `backend/app.py:18` + `global _global_mcp_client` single `TaskGroup` `agent/model.py:159` + fresh `get_model()` per Chatbot call `agent/model.py:337` fixes `Event loop is closed` (httpx/anyio). Streamlit no longer has own `_loop` (PDF p3 proxy).

## Deployment — Railway Full-Stack (Option B, Bonus p5)

**Local is required, Railway is bonus — README must explain both.**

- **Railway (recommended, PDF p3 compliant):** Single repo, **2 services** from same GitHub:
  1. `curt-backend`: Root `.` Start `python backend/app.py` Env `Mistral_API_key`, `Mistral_API_key2`, `SECRET_KEY` Domain `curt-backend.up.railway.app` Health `GET /health` `railway.json:5` Nixpacks, `Procfile: web: python backend/app.py` `runtime.txt python-3.11`
  2. `curt-frontend`: Root `.` Start `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0` Env `BACKEND_URL=https://curt-backend.up.railway.app` Domain `curt-frontend.up.railway.app`
  Railway private networking also works: `BACKEND_URL=http://${{curt-backend.RAILWAY_PRIVATE_DOMAIN}}:5000`
  Single-service fallback: `Procfile` `web: python backend/app.py & streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0` with backend on `5000` inner, Streamlit on `$PORT` outer, frontend `BACKEND_URL=http://127.0.0.1:5000`.

- **Streamlit Cloud (if you prefer):** Deploy backend to Railway as above, set Streamlit Cloud Secrets `BACKEND_URL=https://curt-backend.up.railway.app` (Streamlit is pure HTTP, no `Mistral_API_key` needed on frontend). Streamlit Cloud alone cannot run Flask — must proxy to Railway backend.

- **Health checks:** `GET /health -> ok`, `GET /inventory -> parts`.

## Reflection (Task 6)

- **Decisions:** Multi-tool chaining `parallel_tool_calls: True` + explicit docstrings to fix `not_found` mismatches and `thought_signature` chains; `MAX_HISTORY 20` for longer follow-ups; `recursion_limit:12`; global event loop to fix Flask/Streamlit `Event loop is closed`; `dict(row)` to fix Row serialization; Mistral `nemo` over `small` for RPM; supplier list as message `streamlit_app.py:668` dict handling.
- **With more time (now done as stubs):** `flag_shortage(item_name, threshold=2)` `databasetools.py:126` logs `LOW STOCK FLAG` per spec `pdf:3`; vector RAG `agent/tools/rag.py` TF-IDF `sklearn` over `CORE_PART_INFO` descriptions for PDF Q16; auth `streamlit_app.py` `st.text_input` password `CURT2026` or `flask_httpauth` for backend; evaluation `tests/eval_phase2.py` 20 Q/A accuracy (Phase1 30/30, Phase2 LLM judged); Railway `railway.json` + `Procfile` + `runtime.txt:1` `python-3.11`; video walkthrough 2-5 min (Phase1 human, Phase2 `list all suppliers` message, live DB, tool flow `get_all_suppliers` + `flag_shortage`).

## Submission

- GitHub: `https://github.com/<you>/curt-inventory-assistant`
- Video: Google Drive public link (2-5 min: Phase1/2, live DB, tool flow, code walkthrough)
- Email: `sda.curt@gmail.com` subject `Generative AI Task Submission - [Your Name]` with repo + video + `.env.example` (never `.env`).

---
Generated for CURT26-27 — Phase1 `phase1/assistant_phase1.py:224` + Phase2 `agent/model.py:253` + Streamlit `streamlit_app.py:1`.
