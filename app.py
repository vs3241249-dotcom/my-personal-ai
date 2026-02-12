from flask import Flask, render_template, request, jsonify, redirect, session
import requests
import os
from datetime import datetime
import pytz
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import hashlib

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-this")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
MONGO_URI = os.getenv("MONGO_URI")

# ---------------- MONGODB SETUP ----------------
client = None
chats_col = None
users_col = None

try:
    if MONGO_URI:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["chatbot_db"]
        chats_col = db["chats"]
        users_col = db["users"]
        client.server_info()
        print("✅ MongoDB connected")
    else:
        print("⚠️ MONGO_URI not set")
except ServerSelectionTimeoutError as e:
    print("❌ MongoDB connection failed:", e)

# ---------------- HELPERS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def save_chat(ip, role, msg, username=None):
    if chats_col is None:
        return

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    chats_col.insert_one({
        "ip": ip,
        "username": username if username else "Guest",
        "role": role,
        "message": msg,
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    })

def get_recent_messages(ip, limit=6):
    if chats_col is None:
        return []

    rows = list(
        chats_col.find({"ip": ip})
        .sort("_id", -1)
        .limit(limit)
    )
    rows.reverse()

    return [
        {"role": r["role"], "content": r["message"]}
        for r in rows
    ]

def get_all_chats():
    if chats_col is None:
        return []

    rows = chats_col.find().sort("_id", -1)
    return [
        (
            r.get("ip"),
            r.get("username", "Guest"),
            r.get("role"),
            r.get("message"),
            r.get("time"),
            r.get("date", "")
        )
        for r in rows
    ]

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("inbox.html")

# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        if not OPENROUTER_API_KEY:
            return jsonify({"reply": "AI service not configured"}), 500

        data = request.get_json(force=True)
        user_msg = data.get("message", "").strip()
        username = data.get("username", "Guest")
        user_ip = request.remote_addr

        if not user_msg:
            return jsonify({"reply": "Message empty hai"}), 400

        save_chat(user_ip, "user", user_msg, username)

        conversation_history = get_recent_messages(user_ip)

        messages = [
            {
                "role": "system",
                "content": """
You are a smart AI assistant like ChatGPT.

Rules:
- Reply in the same language as user.
- Keep answers short, clear and natural.
- Avoid long essays unless user asks.
- Use bullet points when helpful.
- Make response easy to understand.
- Sound human and friendly.
"""
            }
        ]

        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_msg})

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://yourapp.onrender.com",
                "X-Title": "My Personal AI",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code != 200:
            print("AI ERROR:", response.text)
            return jsonify({"reply": "AI temporarily busy, try again"}), 500

        bot_reply = response.json()["choices"][0]["message"]["content"]

        save_chat(user_ip, "bot", bot_reply, username)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Chat error:", e)
        return jsonify({"reply": "Server error, please try again"}), 500

# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register_user():
    try:
        if users_col is None:
            return jsonify({"success": False}), 500

        data = request.get_json()
        name = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not name or not password:
            return jsonify({"success": False}), 400

        if users_col.find_one({"username": name}):
            return jsonify({"success": False}), 409

        users_col.insert_one({
            "username": name,
            "password": hash_pw(password)
        })

        return jsonify({"success": True})

    except:
        return jsonify({"success": False}), 500

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login_user():
    try:
        if users_col is None:
            return jsonify({"success": False}), 500

        data = request.get_json()
        name = data.get("username", "").strip()
        password = data.get("password", "").strip()

        user = users_col.find_one({"username": name})
        if not user:
            return jsonify({"success": False}), 401

        if user["password"] == hash_pw(password):
            return jsonify({"success": True, "username": name})

        return jsonify({"success": False}), 401

    except:
        return jsonify({"success": False}), 500

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/dashboard")

    error = None

    if request.method == "POST":
        pwd = request.form.get("password")

        if not ADMIN_PASSWORD:
            error = "Admin password not set"
        elif pwd == ADMIN_PASSWORD:
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

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
