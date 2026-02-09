from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# OpenRouter API Key (Render env se aayegi)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/test")
def test():
    return "APP IS WORKING"

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "My Personal AI"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Reply in simple Hindi-English mix."},
                    {"role": "user", "content": user_msg}
                ]
            },
            timeout=30
        )

        data = res.json()
        return jsonify({"reply": data["choices"][0]["message"]["content"]})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "Server error, thoda baad try karo"}), 500
