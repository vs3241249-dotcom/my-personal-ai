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
except ServerSelectionTimeoutError as e:
    print("MongoDB connection failed:", e)

# ---------------- HELPERS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ---------------- SAVE CHAT ----------------
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
        "time": now.isoformat()
    })

# ---------------- GET ALL CHATS ----------------
def get_all_chats():
    if chats_col is None:
        return []

    rows = chats_col.find().sort("_id", -1)

    return [
        {
            "ip": r.get("ip"),
            "username": r.get("username", "Guest"),
            "role": r.get("role"),
            "message": r.get("message"),
            "time": r.get("time")
        }
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
        data = request.get_json(force=True)

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"reply": "Please type a message."}), 400

        username = data.get("username", "Guest")
        user_ip = request.remote_addr

        save_chat(user_ip, "user", user_msg, username)

        system_prompt = """
You are My Personal AI, a modern intelligent assistant created exclusively for this website.

IDENTITY:
- Your name is "My Personal AI."
- If asked your name, say exactly: "My name is My Personal AI."
- Never say you are ChatGPT.
- Never mention OpenAI.

LANGUAGE:
- Always reply in the same language as the user.
- Use natural, simple and human-like wording.

RESPONSE STYLE:
- Reply in a clean, natural conversational style like modern ChatGPT.
- Keep paragraphs short (2–4 lines maximum).
- Break long answers into small, easy-to-read sections.
- Use bullet points only when explaining steps, lists, or comparisons.
- Do not over-format or use excessive markdown.
- Keep answers visually balanced and easy to scan.
- Default responses should be concise but complete.
- Expand only if the user asks for more detail.
- Avoid long unbroken paragraphs.
- When explaining concepts, structure the answer clearly for readability.
- Determine the complexity and intent of the question, not just its length.
- Provide simple conversational replies for casual questions.
- Provide clear, well-structured explanations for conceptual or educational questions.
- Adjust depth based on how much understanding the user likely needs.
- Use clean readable structure instead of visible markdown syntax.
- Use emojis naturally where helpful, but do not overuse them.
- Do not generate markdown formatting symbols like double asterisks for bold, hash headings, or backticks.
- Normal bullets, numbers, punctuation, and emojis are allowed when naturally appropriate.
GOAL:

Respond naturally and professionally, exactly like a normal ChatGPT conversation.
"""

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
               "temperature": 0.5,
               "max_tokens": 600,

                "top_p": 0.9,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                       "content": user_msg
                    }
                ]
            },
            timeout=30
        )

        res.raise_for_status()
        response_data = res.json()

        bot_reply = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not bot_reply:
            bot_reply = "Sorry, I couldn't generate a proper response. Please try again."

        save_chat(user_ip, "bot", bot_reply, username)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Chat error:", e)
        return jsonify({"reply": "Server error, please try again later."}), 500


# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register_user():
    if users_col is None:
        return jsonify({"success": False}), 500

    data = request.get_json(force=True)
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

# ---------------- USER LOGIN ----------------
@app.route("/login", methods=["POST"])
def login_user():
    if users_col is None:
        return jsonify({"success": False}), 500

    data = request.get_json(force=True)
    name = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = users_col.find_one({"username": name})

    if user and user.get("password") == hash_pw(password):
        return jsonify({"success": True, "username": name})

    return jsonify({"success": False}), 401

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

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin_dashboard.html")

# ---------------- ADMIN MESSAGES ----------------
@app.route("/admin/messages")
def admin_messages():
    if not session.get("admin"):
        return jsonify([])
    return jsonify(get_all_chats())

# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

# ---------------- EXPORT CSV ----------------
@app.route("/admin/export")
def export_csv():
    if not session.get("admin"):
        return redirect("/admin")

    chats = get_all_chats()
    csv_data = "IP,Username,Role,Message,Time\n"

    for c in chats:
        msg = c["message"].replace(",", " ")
        csv_data += f"{c['ip']},{c['username']},{c['role']},{msg},{c['time']}\n"

    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=chat_history.csv"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)








