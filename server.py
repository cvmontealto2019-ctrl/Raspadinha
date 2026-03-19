import os
import re
import json
import random
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.sqlite3"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "biruta_secret_2026")

ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "17717592000160")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Biruta2026")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5516997913686")

PRIZES = [
    "10 CONVIDADOS ADICIONAIS",
    "15 CRIANÇAS DE 6 A 10 ANOS",
    "30 CRIANÇAS DE 0 A 8 ANOS",
    "DESCONTO DE R$350,00",
]

LOSE_TEXT = "TENTE NOVAMENTE"

EGGS = [
    {"name": "OVO DOURADO", "theme": "gold"},
    {"name": "OVO ROSÉ", "theme": "rose"},
    {"name": "OVO CÉU", "theme": "sky"},
    {"name": "OVO LAVANDA", "theme": "lavender"},
    {"name": "OVO MENTA", "theme": "mint"},
    {"name": "OVO SUNSET", "theme": "sunset"},
]


# -------------------------
# UTIL
# -------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def digits_only(value):
    return re.sub(r"\D+", "", value or "")


def upper(value):
    return (value or "").strip().upper()


def last4(value):
    d = digits_only(value)
    return d[-4:] if len(d) >= 4 else d


def format_whatsapp(value):
    d = digits_only(value)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d


def valid_full_name(name):
    return len([p for p in (name or "").strip().split() if p]) >= 2


def remaining_plays(client_row):
    return max(0, int(client_row["plays_total"]) - int(client_row["plays_used"]))


# -------------------------
# BANCO
# -------------------------
def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            plays_total INTEGER NOT NULL DEFAULT 1,
            plays_used INTEGER NOT NULL DEFAULT 0,
            first_access_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            played_at TEXT NOT NULL,
            outcome TEXT NOT NULL,
            prize TEXT NOT NULL,
            board_json TEXT NOT NULL
        )
    """)

    # Corrige bancos antigos sem apagar dados
    client_cols = [row["name"] for row in c.execute("PRAGMA table_info(clients)").fetchall()]
    if "name" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN name TEXT")
    if "whatsapp" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN whatsapp TEXT")
    if "password" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN password TEXT")
    if "plays_total" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN plays_total INTEGER NOT NULL DEFAULT 1")
    if "plays_used" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN plays_used INTEGER NOT NULL DEFAULT 0")
    if "first_access_done" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN first_access_done INTEGER NOT NULL DEFAULT 0")
    if "created_at" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN created_at TEXT")

    play_cols = [row["name"] for row in c.execute("PRAGMA table_info(plays)").fetchall()]
    if "client_id" not in play_cols:
        pass
    if "played_at" not in play_cols:
        pass
    if "outcome" not in play_cols:
        pass
    if "prize" not in play_cols:
        pass
    if "board_json" not in play_cols:
        pass

    conn.commit()
    conn.close()


# -------------------------
# LÓGICA DO JOGO
# -------------------------
def build_board():
    winning_prize = random.choice(PRIZES)
    others = [p for p in PRIZES if p != winning_prize]
    random.shuffle(others)

    # 3 iguais para ganhar, 2 tente novamente, 1 prêmio aleatório extra
    values = [
        winning_prize,
        winning_prize,
        winning_prize,
        LOSE_TEXT,
        LOSE_TEXT,
        others[0],
    ]
    random.shuffle(values)

    board = []
    for i, egg in enumerate(EGGS):
        board.append({
            "name": egg["name"],
            "theme": egg["theme"],
            "value": values[i],
        })

    return board


# -------------------------
# CLIENTE
# -------------------------
@app.route("/")
def home():
    return render_template("client_auth.html")


@app.route("/register", methods=["POST"])
def register():
    name = upper(request.form.get("name"))
    whatsapp = digits_only(request.form.get("whatsapp"))

    if not valid_full_name(name):
        return render_template(
            "message.html",
            title="NOME INCOMPLETO",
            message="DIGITE SEU NOME COMPLETO COM PELO MENOS NOME E 1 SOBRENOME.",
            back="/",
        )

    if len(whatsapp) < 10:
        return render_template(
            "message.html",
            title="WHATSAPP INVÁLIDO",
            message="DIGITE UM NÚMERO DE WHATSAPP VÁLIDO.",
            back="/",
        )

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM clients WHERE whatsapp = ?", (whatsapp,))
    exists = c.fetchone()

    if exists:
        conn.close()
        return render_template(
            "message.html",
            title="WHATSAPP JÁ CADASTRADO",
            message="ESSE WHATSAPP JÁ FOI CADASTRADO. ENTRE COM SUA SENHA.",
            back="/",
        )

    password = last4(whatsapp)
    c.execute("""
        INSERT INTO clients (name, whatsapp, password, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        whatsapp,
        password,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))
    conn.commit()
    session["client_id"] = c.lastrowid
    session["welcome"] = True
    conn.close()

    return redirect(url_for("welcome"))


@app.route("/login", methods=["POST"])
def login():
    whatsapp = digits_only(request.form.get("whatsapp"))
    password = upper(request.form.get("password"))

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE whatsapp = ?", (whatsapp,))
    client = c.fetchone()
    conn.close()

    if not client:
        return render_template(
            "message.html",
            title="ACESSO NÃO ENCONTRADO",
            message="WHATSAPP NÃO CADASTRADO.",
            back="/",
        )

    if password != client["password"]:
        return render_template(
            "message.html",
            title="SENHA INCORRETA",
            message="CONFIRA SUA SENHA E TENTE NOVAMENTE.",
            back="/",
        )

    session["client_id"] = int(client["id"])

    if int(client["first_access_done"]) == 0:
        session["welcome"] = True
        return redirect(url_for("welcome"))

    return redirect(url_for("game"))


@app.route("/logout")
def logout():
    session.pop("client_id", None)
    session.pop("welcome", None)
    session.pop("active_play", None)
    return redirect(url_for("home"))


@app.route("/welcome")
def welcome():
    cid = session.get("client_id")
    if not cid or not session.get("welcome"):
        return redirect(url_for("home"))

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()
    conn.close()

    if not client:
        session.clear()
        return redirect(url_for("home"))

    return render_template(
        "welcome.html",
        name=client["name"],
        whatsapp=format_whatsapp(client["whatsapp"]),
        password=last4(client["whatsapp"]),
        rem=remaining_plays(client),
    )


@app.route("/continue_first_access", methods=["POST"])
def continue_first_access():
    cid = session.get("client_id")
    if not cid:
        return redirect(url_for("home"))

    conn = db()
    c = conn.cursor()
    c.execute("UPDATE clients SET first_access_done = 1 WHERE id = ?", (cid,))
    conn.commit()
    conn.close()

    session.pop("welcome", None)
    return redirect(url_for("game"))


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    cid = session.get("client_id")
    if not cid:
        return redirect(url_for("home"))

    if request.method == "POST":
        new_password = upper(request.form.get("new_password"))

        if len(new_password) < 4:
            return render_template(
                "change_password.html",
                error="A SENHA PRECISA TER PELO MENOS 4 CARACTERES.",
            )

        conn = db()
        c = conn.cursor()
        c.execute("UPDATE clients SET password = ? WHERE id = ?", (new_password, cid))
        conn.commit()
        conn.close()

        return render_template(
            "message.html",
            title="SENHA ALTERADA",
            message="SUA SENHA FOI ATUALIZADA COM SUCESSO.",
            back="/game",
        )

    return render_template("change_password.html", error=None)


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

    if not client:
        session.clear()
        return redirect(url_for("home"))

    return render_template(
        "game.html",
        name=client["name"],
        rem=remaining_plays(client),
    )


@app.route("/start_play", methods=["POST"])
def start_play():
    cid = session.get("client_id")
    if not cid:
        return jsonify(ok=False, error="not_logged_in"), 401

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()
    conn.close()

    if not client:
        return jsonify(ok=False, error="client_not_found"), 404

    if remaining_plays(client) <= 0:
        return jsonify(ok=False, error="no_plays"), 403

    board = build_board()
    session["active_play"] = {"board": board}

    return jsonify(
        ok=True,
        board=board,
        remaining=remaining_plays(client),
    )


@app.route("/finish_play", methods=["POST"])
def finish_play():
    cid = session.get("client_id")
    active_play = session.get("active_play")

    if not cid or not active_play:
        return jsonify(ok=False, error="no_play"), 400

    payload = request.get_json(silent=True) or {}
    outcome = payload.get("outcome", "LOSE")
    prize = payload.get("prize", LOSE_TEXT)

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM clients WHERE id = ?", (cid,))
    client = c.fetchone()

    if not client:
        conn.close()
        session.clear()
        return jsonify(ok=False, error="client_not_found"), 404

    used = int(client["plays_used"]) + 1

    c.execute(
        "UPDATE clients SET plays_used = ? WHERE id = ?",
        (used, cid)
    )

    c.execute("""
        INSERT INTO plays (client_id, played_at, outcome, prize, board_json)
        VALUES (?, ?, ?, ?, ?)
    """, (
        cid,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        outcome,
        prize,
        json.dumps(active_play["board"], ensure_ascii=False),
    ))

    conn.commit()
    conn.close()

    session.pop("active_play", None)

    whatsapp_text = (
        f'OLÁ! GANHEI "{prize}" NA PROMOÇÃO DE PÁSCOA DO BIRUTA PARK 🐰🥚. '
        f'SEI QUE O PRÊMIO É VÁLIDO APENAS PARA OS PACOTES GOURMET, CHEFF, '
        f'BIRUTA OU BIRUTINHA. GOSTARIA DE SOLICITAR UM ORÇAMENTO.'
    )

    return jsonify(
        ok=True,
        outcome=outcome,
        prize=prize,
        remaining=max(0, int(client["plays_total"]) - used),
        whatsapp_text=whatsapp_text,
        whatsapp_number=WHATSAPP_NUMBER,
    )


# -------------------------
# ADMIN
# -------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        user = upper(request.form.get("user"))
        password = upper(request.form.get("password"))

        if user == upper(ADMIN_LOGIN) and password == upper(ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("dashboard"))

        return render_template(
            "admin_login.html",
            error="LOGIN OU SENHA INVÁLIDOS."
        )

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

    c.execute("""
        SELECT *
        FROM clients
        ORDER BY created_at DESC
    """)
    clients = c.fetchall()

    c.execute("""
        SELECT plays.*, clients.name, clients.whatsapp
        FROM plays
        JOIN clients ON clients.id = plays.client_id
        ORDER BY plays.played_at DESC
    """)
    plays = c.fetchall()

    c.execute("SELECT COUNT(*) AS total FROM clients")
    total_clients = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) AS total FROM plays")
    total_plays = c.fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        clients=clients,
        plays=plays,
        total_clients=total_clients,
        total_plays=total_plays,
        format_whatsapp=format_whatsapp,
    )


@app.route("/admin/client/<int:client_id>/update_plays", methods=["POST"])
def admin_update_plays(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))

    plays_total = request.form.get("plays_total", "1").strip()

    try:
        plays_total = int(plays_total)
    except Exception:
        plays_total = 1

    if plays_total < 0:
        plays_total = 0

    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE clients SET plays_total = ? WHERE id = ?",
        (plays_total, client_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/admin/client/<int:client_id>/delete", methods=["POST"])
def admin_delete_client(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))

    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM plays WHERE client_id = ?", (client_id,))
    c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/admin/client/<int:client_id>/reset_usage", methods=["POST"])
def admin_reset_usage(client_id):
    if not session.get("admin"):
        return redirect(url_for("admin"))

    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE clients SET plays_used = 0 WHERE id = ?",
        (client_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
