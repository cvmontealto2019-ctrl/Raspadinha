import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# -------------------------
# BANCO
# -------------------------
def db():
    return sqlite3.connect("database.sqlite3")


def init_db():
    conn = db()
    c = conn.cursor()

    # cria tabela se não existir
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            whatsapp TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)

    # garante colunas (caso banco antigo exista)
    try:
        c.execute("ALTER TABLE clients ADD COLUMN name TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE clients ADD COLUMN whatsapp TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE clients ADD COLUMN password TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE clients ADD COLUMN created_at TEXT")
    except:
        pass

    conn.commit()
    conn.close()


# -------------------------
# ROTAS
# -------------------------

@app.route('/')
def home():
    return render_template('client_auth.html')


# -------------------------
# CADASTRO
# -------------------------
@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    whatsapp = request.form.get('whatsapp')

    if not name or not whatsapp:
        return "Preencha todos os campos"

    password = whatsapp[-4:]

    conn = db()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO clients (name, whatsapp, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, whatsapp, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

    except sqlite3.IntegrityError:
        return "Este número já está cadastrado"

    except Exception as e:
        return f"Erro: {e}"

    finally:
        conn.close()

    return redirect('/')


# -------------------------
# LOGIN
# -------------------------
@app.route('/login', methods=['POST'])
def login():
    whatsapp = request.form.get('whatsapp')
    password = request.form.get('password')

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM clients
        WHERE whatsapp=? AND password=?
    """, (whatsapp, password))

    user = c.fetchone()
    conn.close()

    if user:
        return "Login realizado com sucesso 🎉"
    else:
        return "Usuário ou senha inválidos"


# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
