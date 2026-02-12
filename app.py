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

print("ADMIN_PASSWORD from ENV =", ADMIN_PASSWORD)

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
except ServerSelectionTimeoutError as e:
    print("MongoDB connection failed:", e)

# ---------------- HELPERS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ---------------- SAVE CHAT ----------------
def save_chat(ip, role, msg):
    if chats_col is None:
        return

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    chats_col.insert_one({
        "ip": ip,
        "role": role,
        "message": msg,
        "time": now
    })

def get_all_chats():
    if chats_col is None:
        return []

    rows = chats_col.find().sort("_id", -1)
    return [(r["ip"], r["role"], r["message"], r["time"]) for r in rows]

# ---------------- USER CHAT ----------------
@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_msg = data.get("message")
        user_ip = request.remote_addr

        save_chat(user_ip, "user", user_msg)

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Reply normally like ChatGPT."},
                    {"role": "user", "content": user_msg}
                ]
            },
            timeout=30
        )

        res.raise_for_status()
        data = res.json()

        bot_reply = data["choices"][0]["message"]["content"]

        save_chat(user_ip, "bot", bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Chat error:", e)
        return jsonify({"reply": "Server error, baad me try karo"}), 500

# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register_user():
    try:
        if users_col is None:
            return jsonify({"success": False, "message": "Database not connected"}), 500

        data = request.get_json(force=True)
        name = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not name or not password:
            return jsonify({"success": False, "message": "Username and password required"}), 400

        if users_col.find_one({"username": name}):
            return jsonify({"success": False, "message": "Username already exists"}), 409

        users_col.insert_one({
            "username": name,
            "password": hash_pw(password)
        })

        return jsonify({"success": True, "username": name})

    except Exception as e:
        print("Register Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------------- USER LOGIN (BACKWARD COMPATIBLE FIX) ----------------
@app.route("/login", methods=["POST"])
def login_user():
    try:
        if users_col is None:
            return jsonify({"success": False, "message": "Database not connected"}), 500

        data = request.get_json(force=True)
        name = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not name or not password:
            return jsonify({"success": False, "message": "Username and password required"}), 400

        user = users_col.find_one({"username": name})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 401

        stored_pw = user.get("password")

        # ✅ New users (hashed)
        if stored_pw == hash_pw(password):
            return jsonify({"success": True, "username": name})

        # ✅ Old users (plain text → auto upgrade)
        if stored_pw == password:
            users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": hash_pw(password)}}
            )
            return jsonify({"success": True, "username": name})

        return jsonify({"success": False, "message": "Wrong password"}), 401

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect("/admin/dashboard")

    error = None

    if request.method == "POST":
        pwd = request.form.get("password")

        if not ADMIN_PASSWORD:
            error = "Admin password not configured on server"
        elif pwd and pwd == ADMIN_PASSWORD:
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

    if chats_col is None:
        return jsonify([])

    q = request.args.get("q", "")

    rows = chats_col.find({
        "$or": [
            {"ip": {"$regex": q, "$options": "i"}},
            {"message": {"$regex": q, "$options": "i"}}
        ]
    }).sort("_id", -1)

    return jsonify([[r["ip"], r["role"], r["message"], r["time"]] for r in rows])

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
