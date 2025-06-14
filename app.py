from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import psycopg2
import os
import traceback
# Carregar configurações via variáveis de ambiente
config = {
    "admin_user": os.environ.get("ADMIN_USER", "NELSONBSEBASTIAO0"),
    "admin_pass": os.environ.get("ADMIN_PASS", "123456789"),
    "empresa": os.environ.get("EMPRESA", "Corte & Estilo")
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersegura")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def inicializar_db():
    try:
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
        print("✅ Tabela verificada ou criada.")
    except Exception as e:
        print("❌ Erro ao inicializar DB:", e)
        traceback.print_exc()

inicializar_db()

@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        print("❌ Erro ao renderizar index.html:", e)
        traceback.print_exc()
        return "Erro ao carregar página inicial", 500

@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            user = request.form["username"]
            password = request.form["password"]
            if user == config["admin_user"] and password == config["admin_pass"]:
                session["logado"] = True
                return redirect("/admin")
            else:
                return render_template("login.html", error="Credenciais inválidas.")
        return render_template("login.html")
    except Exception as e:
        print("❌ Erro no login:", e)
        traceback.print_exc()
        return "Erro no login", 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin")
def admin():
    try:
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
    except Exception as e:
        print("❌ Erro na página admin:", e)
        traceback.print_exc()
        return "Erro ao carregar painel admin", 500

@app.route("/agendar", methods=["POST"])
def agendar():
    try:
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

        # Verificar se já há agendamento para este barbeiro, data e hora
        cur.execute(
            "SELECT COUNT(*) FROM agendamentos WHERE barbeiro = %s AND data = %s AND hora = %s",
            (dados["barbeiro"], dados["data"], dados["hora"])
        )
        conflito = cur.fetchone()[0]

        if conflito > 0:
            cur.close()
            conn.close()
            return render_template("erro.html", mensagem=f"O barbeiro {dados['barbeiro']} já está agendado para {dados['hora']} no dia {dados['data']}. Por favor, escolha outro horário.")

        # Se não houver conflito, guardar no banco
        cur.execute(
            "INSERT INTO agendamentos (nome, telefone, servico, barbeiro, data, hora) VALUES (%s, %s, %s, %s, %s, %s)",
            (dados["nome"], dados["telefone"], dados["servico"], dados["barbeiro"], dados["data"], dados["hora"])
        )
        conn.commit()
        cur.close()
        conn.close()

        return render_template("confirmacao.html", dados=dados)

    except Exception as e:
        print("❌ Erro no agendamento:", e)
        traceback.print_exc()
        return "Erro no agendamento", 500

@app.route("/healthz")
def health_check():
    return "ok", 200

# Testar a ligação ao banco
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Conexão com o banco estabelecida!")
    conn.close()
except Exception as e:
    print(f"❌ Falha na conexão: {e}")
    traceback.print_exc()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
