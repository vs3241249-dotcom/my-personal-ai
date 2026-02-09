from flask import Flask, render_template, request, jsonify, redirect, session, send_file
import requests, os, sqlite3, datetime, csv, io

app = Flask(__name__)
app.secret_key = "supersecret123"   # change later

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

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

        c.execute("INSERT INTO chats (ip, role, message, timestamp) VALUES (?, ?, ?, ?)",
                  (user_ip, "bot", reply, time))
        conn.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "Server error, thoda baad try karo"}), 500

    finally:
        conn.close()


# ========== ADMIN SYSTEM ==========

def admin_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")


@app.route("/admin")
@admin_required
def admin_panel():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT ip, role, message, timestamp FROM chats ORDER BY id DESC LIMIT 1000")
    rows = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", chats=rows)


@app.route("/admin/search")
@admin_required
def admin_search():
    q = request.args.get("q", "")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    SELECT ip, role, message, timestamp FROM chats
    WHERE message LIKE ? OR ip LIKE ?
    ORDER BY id DESC
    """, (f"%{q}%", f"%{q}%"))
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)


@app.route("/admin/export")
@admin_required
def admin_export():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT ip, role, message, timestamp FROM chats ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["IP", "Role", "Message", "Time"])
    writer.writerows(rows)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="chat_history.csv")
