import os
import re
import json
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, url_for, jsonify

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.sqlite3"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "biruta-park-magic-secret")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Biruta2026")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5516997913686")

PRIZES = [
    "10 CONVIDADOS ADICIONAIS",
    "15 CRIANÇAS DE 6 A 10 ANOS",
    "30 CRIANÇAS DE 0 A 8 ANOS",
    "DESCONTO DE R$350,00",
]

TRY_AGAIN = "TENTE NOVAMENTE"
ROTTEN = "OVO CHOCO"

MAGIC_POSITIONS = [
    {"x": 8, "y": 70, "size": "md"},
    {"x": 18, "y": 42, "size": "sm"},
    {"x": 30, "y": 78, "size": "lg"},
    {"x": 42, "y": 32, "size": "md"},
    {"x": 55, "y": 60, "size": "sm"},
    {"x": 68, "y": 26, "size": "md"},
    {"x": 80, "y": 73, "size": "lg"},
    {"x": 92, "y": 44, "size": "md"},
]

THEMES = ["gold", "rose", "sky", "lavender", "mint", "sunset", "peach", "violet"]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def digits_only(value):
    return re.sub(r"\D+", "", value or "")

def normalize_name(name):
    cleaned = " ".join((name or "").strip().split())
    return " ".join(word.capitalize() for word in cleaned.split())

def valid_full_name(name):
    parts = [p for p in (name or "").strip().split() if p]
    return len(parts) >= 2

def format_phone(phone):
    d = digits_only(phone)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            current_prize TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            rounds_played INTEGER NOT NULL DEFAULT 0,
            rounds_won INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            played_at TEXT NOT NULL,
            outcome TEXT NOT NULL,
            prize TEXT,
            lives_lost INTEGER NOT NULL DEFAULT 0,
            board_json TEXT NOT NULL,
            found_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def round_profile(rounds_played: int):
    # Primeira rodada sempre perde com ovos chocos
    if rounds_played == 0:
        return "first_forced_lose"
    return "normal"

def build_board(rounds_played: int):
    profile = round_profile(rounds_played)
    positions = MAGIC_POSITIONS[:]
    random.shuffle(positions)

    if profile == "first_forced_lose":
        values = [ROTTEN, ROTTEN, ROTTEN, TRY_AGAIN, TRY_AGAIN]
        values += random.sample(PRIZES, 3)
        random.shuffle(values)
    else:
        winning_prize = random.choice(PRIZES)
        decoy_prizes = [p for p in PRIZES if p != winning_prize]
        random.shuffle(decoy_prizes)
        values = [
            winning_prize, winning_prize, winning_prize,
            ROTTEN, ROTTEN,
            TRY_AGAIN,
            decoy_prizes[0],
            decoy_prizes[1],
        ]
        random.shuffle(values)

    board = []
    for idx, value in enumerate(values):
        pos = positions[idx]
        board.append({
            "id": idx + 1,
            "value": value,
            "theme": THEMES[idx % len(THEMES)],
            "x": pos["x"],
            "y": pos["y"],
            "size": pos["size"],
            "profile": profile,
        })
    return board

@app.route("/")
def home():
    return render_template("client_auth.html")

@app.route("/enter", methods=["POST"])
def enter():
    name = normalize_name(request.form.get("name", ""))
    phone = digits_only(request.form.get("phone", ""))

    if not valid_full_name(name):
        return render_template(
            "message.html",
            title="NOME INCOMPLETO",
            message="Digite seu nome completo com pelo menos nome e sobrenome.",
            back=url_for("home")
        )

    if len(phone) < 10:
        return render_template(
            "message.html",
            title="WHATSAPP INVÁLIDO",
            message="Digite um WhatsApp válido com DDD.",
            back=url_for("home")
        )

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE phone = ?", (phone,))
    client = c.fetchone()

    if client:
        c.execute(
            "UPDATE clients SET name = ?, is_active = 1, updated_at = ? WHERE id = ?",
            (name, now_str(), client["id"])
        )
        client_id = client["id"]
    else:
        c.execute("""
            INSERT INTO clients (name, phone, current_prize, is_active, rounds_played, rounds_won, created_at, updated_at)
            VALUES (?, ?, NULL, 1, 0, 0, ?, ?)
        """, (name, phone, now_str(), now_str()))
        client_id = c.lastrowid

    conn.commit()
    conn.close()

    session["client_id"] = client_id
    session.pop("active_round", None)
    return redirect(url_for("game"))

@app.route("/game")
def game():
    cid = session.get("client_id")
    if not cid:
        return redirect(url_for("home"))

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()
    conn.close()

    if not client or int(client["is_active"]) != 1:
        session.clear()
        return render_template(
            "message.html",
            title="ACESSO INDISPONÍVEL",
            message="Seu acesso não está disponível no momento. Entre em contato com o Biruta Park.",
            back=url_for("home")
        )

    return render_template(
        "game.html",
        name=client["name"],
        current_prize=client["current_prize"] or ""
    )

@app.route("/start_round", methods=["POST"])
def start_round():
    cid = session.get("client_id")
    if not cid:
        return jsonify(ok=False, error="not_logged_in"), 401

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()
    conn.close()

    if not client or int(client["is_active"]) != 1:
        return jsonify(ok=False, error="client_not_found"), 404

    rounds_played = int(client["rounds_played"])
    board = build_board(rounds_played)
    session["active_round"] = {"board": board}
    return jsonify(ok=True, board=board, forced_first_loss=(rounds_played == 0))

@app.route("/finish_round", methods=["POST"])
def finish_round():
    cid = session.get("client_id")
    active_round = session.get("active_round")
    if not cid or not active_round:
        return jsonify(ok=False, error="no_round"), 400

    payload = request.get_json(silent=True) or {}
    outcome = payload.get("outcome", "LOSE")
    prize = payload.get("prize")
    lives_lost = int(payload.get("lives_lost", 0))
    found = payload.get("found", {})

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()

    if not client:
        conn.close()
        session.clear()
        return jsonify(ok=False, error="client_not_found"), 404

    new_rounds_played = int(client["rounds_played"]) + 1
    new_rounds_won = int(client["rounds_won"]) + (1 if outcome == "WIN" else 0)
    new_current_prize = prize if outcome == "WIN" else client["current_prize"]

    c.execute("""
        UPDATE clients
        SET current_prize = ?, rounds_played = ?, rounds_won = ?, updated_at = ?
        WHERE id = ?
    """, (new_current_prize, new_rounds_played, new_rounds_won, now_str(), cid))

    c.execute("""
        INSERT INTO rounds (client_id, played_at, outcome, prize, lives_lost, board_json, found_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        now_str(),
        outcome,
        prize,
        lives_lost,
        json.dumps(active_round["board"], ensure_ascii=False),
        json.dumps(found, ensure_ascii=False),
    ))

    conn.commit()
    conn.close()
    session.pop("active_round", None)

    whatsapp_text = ""
    if prize:
        whatsapp_text = (
            f'OLÁ! ACABEI DE GANHAR A CORTESIA "{prize}" NA CAÇA AOS OVOS MÁGICA DO BIRUTA PARK 🐰✨. '
            f'SEI QUE ESSA CORTESIA ESPECIAL É PARA O FECHAMENTO DE UM NOVO CONTRATO. '
            f'GOSTARIA DE RECEBER O ORÇAMENTO COM ESSA CONDIÇÃO.'
        )

    return jsonify(
        ok=True,
        current_prize=new_current_prize or "",
        whatsapp_number=WHATSAPP_NUMBER,
        whatsapp_text=whatsapp_text
    )

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        user = request.form.get("user", "")
        password = request.form.get("password", "")
        if user == ADMIN_USER and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return render_template("admin_login.html", error="Login ou senha inválidos.")
    return render_template("admin_login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin"))

    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) total FROM clients")
    total_clients = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) total FROM rounds")
    total_rounds = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) total FROM rounds WHERE outcome = 'WIN'")
    total_wins = c.fetchone()["total"]

    c.execute("SELECT * FROM clients ORDER BY updated_at DESC")
    clients = c.fetchall()

    c.execute("""
        SELECT rounds.*, clients.name, clients.phone
        FROM rounds
        JOIN clients ON clients.id = rounds.client_id
        ORDER BY rounds.played_at DESC
        LIMIT 200
    """)
    rounds = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_rounds=total_rounds,
        total_wins=total_wins,
        clients=clients,
        rounds=rounds,
        format_phone=format_phone,
    )

@app.route("/admin/client/<int:client_id>/edit", methods=["GET", "POST"])
def admin_edit_client(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = c.fetchone()

    if not client:
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = normalize_name(request.form.get("name", ""))
        phone = digits_only(request.form.get("phone", ""))
        current_prize = request.form.get("current_prize", "").strip() or None
        is_active = 1 if request.form.get("is_active") == "1" else 0

        if valid_full_name(name) and len(phone) >= 10:
            c.execute("""
                UPDATE clients
                SET name = ?, phone = ?, current_prize = ?, is_active = ?, updated_at = ?
                WHERE id = ?
            """, (name, phone, current_prize, is_active, now_str(), client_id))
            conn.commit()
            conn.close()
            return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_client.html", client=client, format_phone=format_phone)

@app.route("/admin/client/<int:client_id>/delete", methods=["POST"])
def admin_delete_client(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM rounds WHERE client_id = ?", (client_id,))
    c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/admin/client/<int:client_id>/clear_prize", methods=["POST"])
def admin_clear_prize(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE clients SET current_prize = NULL, updated_at = ? WHERE id = ?", (now_str(), client_id))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
