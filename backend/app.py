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

    history = session.get("conversation_history", [])

    response, history = _loop.run_until_complete(Chatbot(
        message,
        history
    ))

    session["conversation_history"] = history

    return jsonify({
        "response": response
    })


@app.route("/inventory", methods=["POST"])
def inventory():
    data = request.get_json()

    if not data:
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
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)