from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔑 OpenRouter API Key
OPENROUTER_API_KEY = "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"

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "My Personal AI"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI. Reply in very simple, easy language like ChatGPT or Gemini."
                    },
                    {
                        "role": "user",
                        "content": user_msg
                    }
                ]
            }
        )

        data = res.json()
        reply = data["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print(e)
        return jsonify({"reply": "⚠️ AI busy hai, thoda baad try karo"}), 500


if __name__ == "__main__":
    app.run(debug=True)
