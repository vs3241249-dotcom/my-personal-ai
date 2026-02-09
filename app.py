from flask import Flask, render_template, request, jsonify
import requests, os, sqlite3, datetime

app = Flask(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DB = "chats.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        role TEXT,
        message TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    user_ip = request.remote_addr
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        # Save user message
        c.execute("INSERT INTO chats (ip, role, message, timestamp) VALUES (?, ?, ?, ?)",
                  (user_ip, "user", user_msg, time))
        conn.commit()

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

        reply = res.json()["choices"][0]["message"]["content"]

        # Save bot reply
        c.execute("INSERT INTO chats (ip, role, message, timestamp) VALUES (?, ?, ?, ?)",
                  (user_ip, "bot", reply, time))
        conn.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "Server error, thoda baad try karo"}), 500

    finally:
        conn.close()


# ✅ ADMIN API (Permanent History)
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT ip, role, message, timestamp FROM chats ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    data = [
        {"ip": r[0], "role": r[1], "message": r[2], "time": r[3]}
        for r in rows
    ]
    return jsonify(data)
