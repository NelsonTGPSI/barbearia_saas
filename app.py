
from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
import psycopg2
import json
import os

# Carregar configurações
with open("config.json") as f:
    config = json.load(f)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersegura")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Conexão com a base de dados PostgreSQL (Render fornece URI em variável de ambiente DATABASE_URL)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Criar tabela se não existir
def inicializar_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            telefone TEXT,
            servico TEXT,
            barbeiro TEXT,
            data TEXT,
            hora TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

inicializar_db()

@app.route("/")
def index():
    return "O sistema está ativo. A zona de agendamento funciona via POST para /agendar."

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]
        if user == config["admin_user"] and password == config["admin_pass"]:
            session["logado"] = True
            return redirect("/admin")
        else:
            return render_template("login.html", error="Credenciais inválidas.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin")
def admin():
    if not session.get("logado"):
        return redirect("/login")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nome, telefone, servico, barbeiro, data, hora FROM agendamentos ORDER BY data, hora")
    agendamentos = [
        dict(nome=r[0], telefone=r[1], servico=r[2], barbeiro=r[3], data=r[4], hora=r[5])
        for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template("admin.html", agendamentos=agendamentos, empresa=config["empresa"])

@app.route("/agendar", methods=["POST"])
def agendar():
    dados = {
        "nome": request.form["name"],
        "telefone": request.form["phone"],
        "servico": request.form["service"],
        "barbeiro": request.form.get("barber", ""),
        "data": request.form["date"],
        "hora": request.form["time"]
    }
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO agendamentos (nome, telefone, servico, barbeiro, data, hora) VALUES (%s, %s, %s, %s, %s, %s)",
        (dados["nome"], dados["telefone"], dados["servico"], dados["barbeiro"], dados["data"], dados["hora"])
    )
    conn.commit()
    cur.close()
    conn.close()
    return "Agendamento recebido com sucesso!"
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
