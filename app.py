from flask import Flask, render_template, request, jsonify, redirect, session
import requests
import os
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

ADMIN_PASSWORD = "12345"   # 👈 apna strong password yahan set kar

DB_FILE = "chat.db"

# ---------------- DB INIT ----------------
def init_db():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            role TEXT,
            message TEXT,
            time TEXT
        )
    """)
    con.commit()
    con.close()

init_db()

def save_chat(ip, role, msg):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("INSERT INTO chats (ip, role, message, time) VALUES (?,?,?,?)",
                (ip, role, msg, now))
    con.commit()
    con.close()

def get_all_chats():
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("SELECT ip, role, message, time FROM chats ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows

# ---------------- USER CHAT ----------------
@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    user_ip = request.remote_addr

    save_chat(user_ip, "user", user_msg)

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
        bot_reply = data["choices"][0]["message"]["content"]

        save_chat(user_ip, "bot", bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        return jsonify({"reply": "Server error, baad me try karo"}), 500


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/dashboard")

    error = None
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            error = "Wrong password"

    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    chats = get_all_chats()
    return render_template("admin_dashboard.html", chats=chats)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


# ---------------- SEARCH ----------------
@app.route("/admin/search")
def admin_search():
    if not session.get("admin"):
        return jsonify([])

    q = request.args.get("q", "")

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("""
        SELECT ip, role, message, time FROM chats
        WHERE ip LIKE ? OR message LIKE ?
        ORDER BY id DESC
    """, (f"%{q}%", f"%{q}%"))
    rows = cur.fetchall()
    con.close()

    return jsonify(rows)


# ---------------- EXPORT ----------------
@app.route("/admin/export")
def export_csv():
    if not session.get("admin"):
        return redirect("/admin")

    chats = get_all_chats()
    csv_data = "IP,Role,Message,Time\n"
    for c in chats:
        csv_data += f"{c[0]},{c[1]},{c[2].replace(',', ' ')},{c[3]}\n"

    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=chat_history.csv"
    }


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
