from flask import Flask, render_template, request, jsonify, redirect, session
import requests
import os
from datetime import datetime
import pytz
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"

# -------- ENV KEYS --------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
MONGO_URI = os.getenv("MONGO_URI")

# -------- MONGODB SETUP --------
client = MongoClient(MONGO_URI)
db = client["chatbot_db"]
chats_col = db["chats"]

# -------- SAVE CHAT --------
def save_chat(ip, role, msg):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    chats_col.insert_one({
        "ip": ip,
        "role": role,
        "message": msg,
        "time": now
    })

def get_all_chats():
    rows = chats_col.find().sort("_id", -1)
    return [(r["ip"], r["role"], r["message"], r["time"]) for r in rows]

# -------- USER CHAT --------
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

    except Exception:
        return jsonify({"reply": "Server error, baad me try karo"}), 500

# -------- ADMIN LOGIN --------
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

# -------- SEARCH --------
@app.route("/admin/search")
def admin_search():
    if not session.get("admin"):
        return jsonify([])

    q = request.args.get("q", "")

    rows = chats_col.find({
        "$or": [
            {"ip": {"$regex": q, "$options": "i"}},
            {"message": {"$regex": q, "$options": "i"}}
        ]
    }).sort("_id", -1)

    return jsonify([[r["ip"], r["role"], r["message"], r["time"]] for r in rows])

# -------- EXPORT --------
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

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
