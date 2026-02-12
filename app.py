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
        print("MongoDB connected successfully")
    else:
        print("MONGO_URI not set")
except Exception as e:
    print("MongoDB connection failed:", e)

# ---------------- HELPERS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ---------------- SAVE CHAT ----------------
def save_chat(ip, role, msg, username=None):
    if chats_col is None:
        return
    try:
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
    except Exception as e:
        print("Save chat error:", e)

# ---------------- MEMORY ----------------
def get_recent_messages(ip, limit=6):
    if chats_col is None:
        return []
    try:
        rows = list(
            chats_col.find({"ip": ip})
            .sort("_id", -1)
            .limit(limit)
        )
        rows.reverse()
        return [
            {"role": r.get("role"), "content": r.get("message")}
            for r in rows
            if r.get("message")
        ]
    except Exception as e:
        print("Memory error:", e)
        return []

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("inbox.html")

# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_msg = (data.get("message") or "").strip()
        username = data.get("username", "Guest")
        user_ip = request.remote_addr

        if not user_msg:
            return jsonify({"reply": "Please type a message."})

        save_chat(user_ip, "user", user_msg, username)

        # Load memory
        conversation_history = get_recent_messages(user_ip)

        system_prompt = """
You are a smart AI assistant like ChatGPT.

Rules:
- Reply in the SAME language as the user.
- Keep answers short, clear and easy to understand.
- Do NOT write long essays unless user asks.
- Use simple words.
- Break long answers into small readable parts.
- Use bullet points when helpful.
- Be natural and human-like.
"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_msg})

        if not OPENROUTER_API_KEY:
            return jsonify({"reply": "AI not configured properly."})

        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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

            response_data = res.json()

            if "choices" not in response_data:
                print("API ERROR:", response_data)
                return jsonify({"reply": "AI temporarily unavailable. Try again."})

            bot_reply = response_data["choices"][0]["message"]["content"]

        except Exception as api_error:
            print("API CALL ERROR:", api_error)
            return jsonify({"reply": "AI service error. Please try again."})

        save_chat(user_ip, "bot", bot_reply, username)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "Server error, please try again."})

# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register_user():
    try:
        if users_col is None:
            return jsonify({"success": False}), 500

        data = request.get_json(force=True)
        name = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

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

        data = request.get_json(force=True)
        name = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        user = users_col.find_one({"username": name})
        if user and user.get("password") == hash_pw(password):
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
        if ADMIN_PASSWORD and pwd == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            error = "Wrong password"

    return render_template("admin_login.html", error=error)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    rows = chats_col.find().sort("_id", -1) if chats_col else []
    chats = [
        (
            r.get("ip"),
            r.get("username", "Guest"),
            r.get("role"),
            r.get("message"),
            r.get("time"),
            r.get("date")
        )
        for r in rows
    ]

    return render_template("admin_dashboard.html", chats=chats)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
