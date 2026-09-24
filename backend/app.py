import asyncio
import os
from flask import Flask, request, jsonify, session
from flask_session import Session
from agent.model import Chatbot
from agent.tools.databaseserver.helper import _fetch_all_parts

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key-change-me")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Global loop for Chatbot - reuses same loop to avoid httpx Event loop is closed, with TaskGroup fix via client.close()
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({
            "error": "Missing 'message'"
        }), 400

    message = data["message"]
    # Optional phase routing (PDF p3/p4): frontend sends phase="phase1" for rule-based, default phase2 LLM
    phase = data.get("phase", "phase2")
    # Allow frontend per-chat history (Streamlit multi-chat) to override session history
    # Falls back to Flask session for PDF p3 follow-up example (How many brake pads? -> Where are they stored?)
    req_history = data.get("history")
    if isinstance(req_history, list):
        history = req_history
    else:
        history = session.get("conversation_history", [])

    # Phase 1 — rule-based (no LLM) via same backend for PDF compliance (Streamlit pure HTTP)
    if phase == "phase1" or str(phase).lower().startswith("phase 1"):
        try:
            from phase1.assistant_phase1 import handle_question as phase1_handle
            response = phase1_handle(message)
            # maintain history for phase1 as simple user+assistant pairs
            history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": response}]
            session["conversation_history"] = history[-20:]
            return jsonify({
                "response": response,
                "history": history
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Phase 2 — LLM with function calling via MCP
    response, history = _loop.run_until_complete(Chatbot(
        message,
        history
    ))

    session["conversation_history"] = history

    return jsonify({
        "response": response,
        "history": history
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    # GET per spec, POST kept for backward compat (Streamlit/backend)
    if request.method == "POST":
        data = request.get_json(silent=True)
        # allow empty body for POST as well (spec says GET, impl was POST)
        # only require body if provided, but not mandatory
        if data is not None and not data and request.data:
            return jsonify({
                "error": "Missing request body"
            }), 400

    try:
        parts = _fetch_all_parts()

        return jsonify({
            "status": "success",
            "parts": parts
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    # Railway injects PORT, local defaults to 5000; bind 0.0.0.0 for container
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
