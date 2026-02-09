from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import json

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# =========================
# FILE FOR PERMANENT STORAGE
# =========================
ADMIN_FILE = "admin_messages.json"


def load_admin_messages():
    if not os.path.exists(ADMIN_FILE):
        return []
    with open(ADMIN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_admin_messages(messages):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


# load messages at app start
admin_messages = load_admin_messages()


@app.route("/")
def home():
    return render_template("inbox.html")


@app.route("/test")
def test():
    return "APP IS WORKING"


# =========================
# CHAT ROUTE
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data_req = request.get_json()

        if not data_req:
            return jsonify({"reply": "Invalid data"}), 400

        user_msg = data_req.get("message", "").strip()
        user_name = data_req.get("name", "Unknown User")

        if not user_msg:
            return jsonify({"reply": "Empty message"}), 400

        # ---- TIME (DO NOT CHANGE) ----
        ist = ZoneInfo("Asia/Kolkata")
        time_now = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")

        # ---- SAVE MESSAGE PERMANENTLY ----
        messages = load_admin_messages()

        messages.append({
            "name": user_name,
            "message": user_msg,
            "time": time_now
        })

        save_admin_messages(messages)

        # ---- AI REQUEST ----
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://my-personal-ai-v6w9.onrender.com",
                "X-Title": "My Personal AI"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a friendly, smart AI assistant. Keep replies short and clear."
                    },
                    {"role": "user", "content": user_msg}
                ]
            },
            timeout=30
        )

        data = res.json()

        return jsonify({
            "reply": data["choices"][0]["message"]["content"]
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"reply": "Server error"}), 500


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin")
def admin_panel():
    return jsonify(load_admin_messages())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
