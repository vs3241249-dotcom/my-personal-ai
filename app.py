from flask import Flask, render_template, request, jsonify
import requests
import os
import json
from datetime import datetime
import pytz

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DATA_FILE = "admin_messages.json"

# 🔁 Load messages from file
def load_messages():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Save messages to file
def save_messages(messages):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/test")
def test():
    return "APP IS WORKING"

# 🧠 CHAT ROUTE
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data_req = request.get_json()
        if not data_req:
            return jsonify({"reply": "Invalid data"}), 400

        user_msg = data_req.get("message", "").strip()
        user_name = data_req.get("name", "Guest User")

        if not user_msg:
            return jsonify({"reply": "Empty message"}), 400

        # 🕒 INDIA TIME (FIXED)
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)

        # 📥 LOAD OLD MESSAGES
        admin_messages = load_messages()

        # ➕ ADD NEW MESSAGE (DATE-WISE)
        admin_messages.append({
            "date": now.strftime("%d-%m-%Y"),
            "time": now.strftime("%H:%M:%S"),
            "name": user_name,
            "message": user_msg
        })

        # 💾 SAVE BACK TO FILE
        save_messages(admin_messages)

        # 🤖 SEND TO OPENROUTER
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
                        "content": "You are a friendly, smart AI assistant. Keep replies short, clear and human-like 🙂"
                    },
                    {"role": "user", "content": user_msg}
                ]
            },
            timeout=30
        )

        data = res.json()
        reply = data["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"reply": "Server error"}), 500


# 🛡️ ADMIN PANEL (PERMANENT HISTORY)
@app.route("/admin")
def admin_panel():
    return jsonify(load_messages())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
