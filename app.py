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
def chat():
    try:
        data_req = request.get_json()
        if not data_req or "message" not in data_req:
            return jsonify({"reply": "Message missing"}), 400

        user_msg = data_req.get("message", "").strip()
        if not user_msg:
            return jsonify({"reply": "Empty message"}), 400

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
        "content": "You are a friendly, smart AI assistant like ChatGPT. Reply in simple, natural English. Keep answers short, clear, and human-like. Use emojis sometimes 🙂 but not too many. Do not use unnecessary symbols or long lists. Be conversational and helpful."
    },
    {"role": "user", "content": user_msg}
]

            },
            timeout=30
        )

        data = res.json()
        print("OPENROUTER RESPONSE:", data)

        if "choices" not in data:
            return jsonify({"reply": str(data)}), 500

        return jsonify({
            "reply": data["choices"][0]["message"]["content"]
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"reply": "Server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

