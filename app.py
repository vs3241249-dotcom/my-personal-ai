from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/test")
def test():
    return "APP IS WORKING"

@app.route("/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    try:
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
                    {"role": "system", "content": "Reply in simple Hindi-English mix."},
                    {"role": "user", "content": user_msg}
                ]
            },
            timeout=30
        )

        data = res.json()

        # 🔴 IMPORTANT SAFETY CHECKS
        if res.status_code != 200:
            print("OPENROUTER ERROR:", data)
            return jsonify({
                "reply": "AI service issue (API key / credits / model)."
            }), 500

        if "choices" not in data:
            print("INVALID RESPONSE:", data)
            return jsonify({
                "reply": "AI response invalid. Please try again."
            }), 500

        return jsonify({
            "reply": data["choices"][0]["message"]["content"]
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({
            "reply": "Server error, please try again"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


