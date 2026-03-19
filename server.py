from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3, random, json, re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.sqlite3"
app = Flask(__name__)
app.secret_key = "biruta_ovos_raspaveis_v1"

ADMIN_LOGIN = "17717592000160"
ADMIN_PASSWORD = "Biruta2026"
WHATSAPP_NUMBER = "5516997913686"

PRIZES = [
    "10 CONVIDADOS ADICIONAIS",
    "15 CRIANÇAS DE 6 A 10 ANOS",
    "30 CRIANÇAS DE 0 A 8 ANOS",
    "DESCONTO DE R$350,00",
]
LOSE_TEXT = "TENTE NOVAMENTE"
EGGS = [
    {"name":"OVO DOURADO","theme":"gold"},
    {"name":"OVO ROSÉ","theme":"rose"},
    {"name":"OVO CÉU","theme":"sky"},
    {"name":"OVO LAVANDA","theme":"lavender"},
    {"name":"OVO MENTA","theme":"mint"},
    {"name":"OVO SUNSET","theme":"sunset"},
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

import sqlite3

def init_db():
    conn = sqlite3.connect('database.sqlite3')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        whatsapp TEXT,
        senha TEXT,
        premio TEXT,
        horario TEXT
    )
    ''')

    conn.commit()
    conn.close()

def digits_only(s): return re.sub(r"\D+", "", s or "")
def upper(s): return (s or "").strip().upper()
def last4(v):
    d = digits_only(v)
    return d[-4:] if len(d) >= 4 else d
def format_whatsapp(v):
    d = digits_only(v)
    if len(d) == 11: return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10: return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d
def valid_full_name(name): return len([p for p in (name or "").strip().split() if p]) >= 2
def remaining_plays(client): return max(0, int(client["plays_total"]) - int(client["plays_used"]))

def build_board():
    winning_prize = random.choice(PRIZES)
    others = [p for p in PRIZES if p != winning_prize]
    random.shuffle(others)
    values = [winning_prize, winning_prize, winning_prize, LOSE_TEXT, LOSE_TEXT, others[0]]
    random.shuffle(values)
    board = []
    for i, egg in enumerate(EGGS):
        board.append({"name": egg["name"], "theme": egg["theme"], "value": values[i]})
    return board

@app.route("/")
def home(): return render_template("client_auth.html")

@app.route("/register", methods=["POST"])
def register():
    name = upper(request.form.get("name"))
    whatsapp = digits_only(request.form.get("whatsapp"))
    if not valid_full_name(name):
        return render_template("message.html", title="NOME INCOMPLETO", message="DIGITE SEU NOME COMPLETO COM PELO MENOS NOME E 1 SOBRENOME.", back="/")
    if len(whatsapp) < 10:
        return render_template("message.html", title="WHATSAPP INVÁLIDO", message="DIGITE UM NÚMERO DE WHATSAPP VÁLIDO.", back="/")
    conn = db(); c = conn.cursor(); c.execute("SELECT id FROM clients WHERE whatsapp=?", (whatsapp,))
    if c.fetchone():
        conn.close()
        return render_template("message.html", title="WHATSAPP JÁ CADASTRADO", message="ESSE WHATSAPP JÁ FOI CADASTRADO. ENTRE COM SUA SENHA.", back="/")
    c.execute("INSERT INTO clients (name,whatsapp,password,created_at) VALUES (?,?,?,?)", (name, whatsapp, last4(whatsapp), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); session["client_id"] = c.lastrowid; session["welcome"] = True; conn.close()
    return redirect(url_for("welcome"))

@app.route("/login", methods=["POST"])
def login():
    whatsapp = digits_only(request.form.get("whatsapp"))
    password = upper(request.form.get("password"))
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM clients WHERE whatsapp=?", (whatsapp,)); client = c.fetchone(); conn.close()
    if not client:
        return render_template("message.html", title="ACESSO NÃO ENCONTRADO", message="WHATSAPP NÃO CADASTRADO.", back="/")
    if password != client["password"]:
        return render_template("message.html", title="SENHA INCORRETA", message="CONFIRA SUA SENHA E TENTE NOVAMENTE.", back="/")
    session["client_id"] = int(client["id"])
    if int(client["first_access_done"]) == 0:
        session["welcome"] = True
        return redirect(url_for("welcome"))
    return redirect(url_for("game"))

@app.route("/welcome")
def welcome():
    cid = session.get("client_id")
    if not cid or not session.get("welcome"): return redirect(url_for("home"))
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM clients WHERE id=?", (cid,)); client = c.fetchone(); conn.close()
    if not client:
        session.clear(); return redirect(url_for("home"))
    return render_template("welcome.html", name=client["name"], whatsapp=format_whatsapp(client["whatsapp"]), password=last4(client["whatsapp"]), rem=remaining_plays(client))

@app.route("/continue_first_access", methods=["POST"])
def continue_first_access():
    cid = session.get("client_id")
    if not cid: return redirect(url_for("home"))
    conn = db(); c = conn.cursor(); c.execute("UPDATE clients SET first_access_done=1 WHERE id=?", (cid,)); conn.commit(); conn.close()
    session.pop("welcome", None)
    return redirect(url_for("game"))

@app.route("/change_password", methods=["GET","POST"])
def change_password():
    cid = session.get("client_id")
    if not cid: return redirect(url_for("home"))
    if request.method == "POST":
        new = upper(request.form.get("new_password"))
        if len(new) < 4:
            return render_template("change_password.html", error="A SENHA PRECISA TER PELO MENOS 4 CARACTERES.")
        conn = db(); c = conn.cursor(); c.execute("UPDATE clients SET password=? WHERE id=?", (new, cid)); conn.commit(); conn.close()
        return render_template("message.html", title="SENHA ALTERADA", message="SUA SENHA FOI ATUALIZADA COM SUCESSO.", back="/game")
    return render_template("change_password.html", error=None)

@app.route("/game")
def game():
    cid = session.get("client_id")
    if not cid: return redirect(url_for("home"))
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM clients WHERE id=?", (cid,)); client = c.fetchone(); conn.close()
    if not client:
        session.clear(); return redirect(url_for("home"))
    return render_template("game.html", name=client["name"], rem=remaining_plays(client))

@app.route("/start_play", methods=["POST"])
def start_play():
    cid = session.get("client_id")
    if not cid: return jsonify(ok=False, error="not_logged_in"), 401
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM clients WHERE id=?", (cid,)); client = c.fetchone(); conn.close()
    if not client or remaining_plays(client) <= 0:
        return jsonify(ok=False, error="no_plays"), 403
    board = build_board()
    session["active_play"] = {"board": board}
    return jsonify(ok=True, board=board, remaining=remaining_plays(client))

@app.route("/finish_play", methods=["POST"])
def finish_play():
    cid = session.get("client_id")
    play = session.get("active_play")
    if not cid or not play: return jsonify(ok=False, error="no_play"), 400
    payload = request.get_json(silent=True) or {}
    outcome = payload.get("outcome", "LOSE")
    prize = payload.get("prize", LOSE_TEXT)
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM clients WHERE id=?", (cid,)); client = c.fetchone()
    if not client:
        conn.close(); session.clear(); return jsonify(ok=False, error="not_found"), 404
    used = int(client["plays_used"]) + 1
    c.execute("UPDATE clients SET plays_used=? WHERE id=?", (used, cid))
    c.execute("INSERT INTO plays (client_id,played_at,outcome,prize,board_json) VALUES (?,?,?,?,?)",
              (cid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), outcome, prize, json.dumps(play["board"], ensure_ascii=False)))
    conn.commit(); conn.close(); session.pop("active_play", None)
    whatsapp_text = f'OLÁ! GANHEI "{prize}" NA PROMOÇÃO DE PÁSCOA DO BIRUTA PARK 🐰🥚. SEI QUE O PRÊMIO É VÁLIDO APENAS PARA OS PACOTES GOURMET, CHEFF, BIRUTA OU BIRUTINHA. GOSTARIA DE SOLICITAR UM ORÇAMENTO.'
    return jsonify(ok=True, outcome=outcome, prize=prize, remaining=max(0, int(client["plays_total"]) - used), whatsapp_text=whatsapp_text, whatsapp_number=WHATSAPP_NUMBER)

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if upper(request.form.get("login")) == ADMIN_LOGIN and upper(request.form.get("password")) == ADMIN_PASSWORD.upper():
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return render_template("admin_login.html", error="LOGIN OU SENHA INVÁLIDOS.")
    return render_template("admin_login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"): return redirect(url_for("admin"))
    conn = db(); c = conn.cursor()
    c.execute("SELECT cl.name, cl.whatsapp, p.outcome, p.prize, p.played_at FROM plays p JOIN clients cl ON cl.id=p.client_id ORDER BY p.played_at DESC")
    rows = c.fetchall()
    c.execute("SELECT COUNT(*) n FROM clients"); total_clients = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) n FROM plays"); total_plays = c.fetchone()["n"]
    conn.close()
    return render_template("dashboard.html", rows=rows, total_clients=total_clients, total_plays=total_plays, format_whatsapp=format_whatsapp)

import os
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
