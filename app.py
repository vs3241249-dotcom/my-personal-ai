from flask import Flask, render_template, request, jsonify, redirect, session, send_file
import requests, os, datetime, json, csv, io

app = Flask(__name__)
app.secret_key = "supersecret123"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

DATA_FILE = "chat_logs.json"

def load_logs():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_logs(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def home():
    return render_template("inbox.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    user_ip = request.remote_addr
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logs = load_logs()
    logs.append({"ip": user_ip, "role": "user", "message": user_msg, "time": time})

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

        reply = res.json()["choices"][0]["message"]["content"]
        logs.append({"ip": user_ip, "role": "bot", "message": reply, "time": time})
        save_logs(logs)

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        save_logs(logs)
        return jsonify({"reply": "Server error, thoda baad try karo"}), 500


# ========= ADMIN SYSTEM =========

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
    logs = load_logs()[::-1]   # latest first
    return render_template("admin_dashboard.html", chats=logs)


@app.route("/admin/search")
@admin_required
def admin_search():
    q = request.args.get("q", "").lower()
    logs = load_logs()
    filtered = [c for c in logs if q in c["message"].lower() or q in c["ip"]]
    return jsonify(filtered[::-1])


@app.route("/admin/export")
@admin_required
def admin_export():
    logs = load_logs()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["IP", "Role", "Message", "Time"])
    for c in logs:
        writer.writerow([c["ip"], c["role"], c["message"], c["time"]])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="chat_history.csv")
