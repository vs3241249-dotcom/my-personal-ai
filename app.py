from flask import Flask, render_template, request, jsonify
import requests
import os
import json
from datetime import datetime
import pytz

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DATA_FILE = "admin_messages.json"

# ---------- LOAD OLD MESSAGES ----------
def load_messages():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ---------- SAVE MESSAGES ----------
def save_messages(messages):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

admin_messages = load_messages()

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/test")
def test():
    return "APP IS WORKING"

# ---------- CHAT ----------
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

        # ✅ IST TIME (FIXED)
        ist = pytz.timezone("Asia/Kolkata")
        time_now = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")

        # ✅ SAVE MESSAGE (PERMANENT)
        admin_messages.append({
            "name": user_name,
            "message": user_msg,
            "time": time_now
        })
        save_messages(admin_messages)

        # ---------- AI CALL ----------
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
                        "content": "You are a friendly AI assistant."
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
        print("ERROR:", e)
        return jsonify({"reply": "Server error"}), 500

# ---------- ADMIN ----------
@app.route("/admin")
def admin_panel():
    return jsonify(admin_messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
