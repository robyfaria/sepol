"""Protótipo SEPOL 2.0 com login mínimo e fluxo de orçamento em 3 passos.

Execução:
    python app.py
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "sepol-prototipo-dev"

USUARIO_PADRAO = "admin"
SENHA_PADRAO = "1234"

HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SEPOL 2.0</title>
  <style>
    :root { --bg:#F8FAFC; --txt:#0F172A; --muted:#334155; --primary:#0EA5E9; --ok:#16A34A; --err:#DC2626; --border:#CBD5E1; }
    body { font-family: Arial, sans-serif; background:var(--bg); color:var(--txt); margin:0; font-size:18px; line-height:1.5; }
    .container { max-width:980px; margin: 0 auto; padding:24px; }
    .card { background:#fff; border:1px solid var(--border); border-radius:12px; padding:20px; margin:14px 0; }
    h1 { font-size:30px; margin:0 0 8px; }
    h2 { font-size:24px; margin:0 0 10px; }
    .muted { color:var(--muted); }
    label { display:block; font-weight:600; margin-top:10px; }
    input { width:100%; max-width:420px; min-height:44px; font-size:18px; border:1px solid var(--border); border-radius:8px; padding:8px 10px; }
    button, .btn { min-height:44px; font-size:18px; border:0; border-radius:8px; padding:8px 14px; background:var(--primary); color:#fff; font-weight:700; cursor:pointer; text-decoration:none; display:inline-block; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th, td { border-bottom:1px solid var(--border); text-align:left; padding:10px 6px; }
    .ok { color:var(--ok); font-weight:700; }
    .err { color:var(--err); font-weight:700; }
    .steps { display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; padding-left:18px; }
  </style>
</head>
<body>
  <main class="container">
    {% if login %}
      <section class="card">
        <h1>Entrar no SEPOL 2.0</h1>
        <p class="muted">Login mínimo para validar o fluxo do protótipo.</p>
        {% if erro %}<p class="err">{{ erro }}</p>{% endif %}
        <form method="post" action="{{ url_for('login') }}">
          <label>Usuário
            <input name="usuario" type="text" required placeholder="admin" />
          </label>
          <label>Senha
            <input name="senha" type="password" required placeholder="1234" />
          </label>
          <p><button type="submit">Entrar</button></p>
        </form>
      </section>
    {% else %}
      <header>
        <h1>Novo orçamento</h1>
        <p class="muted">Olá, {{ usuario }}. Fluxo guiado em 3 passos.</p>
      </header>
      <ol class="steps">
        <li>1. Dados</li>
        <li>2. Fases e serviços</li>
        <li>3. Revisão e emissão</li>
      </ol>

      <section class="card">
        <h2>Passo 1 — Dados do orçamento</h2>
        <form method="post" action="{{ url_for('salvar_orcamento') }}">
          <label>Número
            <input name="numero" value="{{ orc.numero }}" required />
          </label>
          <label>Descrição
            <input name="descricao" value="{{ orc.descricao }}" required />
          </label>
          <label>Cliente
            <input name="cliente" value="{{ orc.cliente }}" required />
          </label>
          <label>Data de emissão
            <input name="emissao" type="date" value="{{ orc.emissao }}" required />
          </label>
          <p><button type="submit">Salvar dados</button></p>
        </form>
      </section>

      <section class="card">
        <h2>Passo 2 — Fases e serviços</h2>
        <form method="post" action="{{ url_for('adicionar_servico') }}">
          <label>Fase
            <input name="fase" required />
          </label>
          <label>Serviço
            <input name="servico" required />
          </label>
          <label>Quantidade
            <input name="quantidade" type="number" step="0.01" min="0.01" value="1" required />
          </label>
          <label>Valor unitário (R$)
            <input name="valor_unitario" type="number" step="0.01" min="0.01" required />
          </label>
          <p><button type="submit">Adicionar serviço</button></p>
        </form>

        <table>
          <thead><tr><th>Fase</th><th>Serviço</th><th>Qtd</th><th>Unit.</th><th>Total</th></tr></thead>
          <tbody>
            {% for item in servicos %}
              <tr><td>{{ item.fase }}</td><td>{{ item.servico }}</td><td>{{ item.quantidade }}</td><td>R$ {{ "%.2f"|format(item.valor_unitario) }}</td><td>R$ {{ "%.2f"|format(item.total) }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </section>

      <section class="card">
        <h2>Passo 3 — Revisão e emissão</h2>
        <p>Total mão de obra: <strong>R$ {{ "%.2f"|format(total) }}</strong></p>
        {% if msg %}<p class="ok">{{ msg }}</p>{% endif %}
        {% if erro %}<p class="err">{{ erro }}</p>{% endif %}
        <form method="post" action="{{ url_for('emitir') }}">
          <button type="submit">Emitir orçamento</button>
          <a class="btn" href="{{ url_for('logout') }}">Sair</a>
        </form>
      </section>
    {% endif %}
  </main>
</body>
</html>
"""


def _estado_inicial() -> dict:
    return {
        "numero": f"{date.today().year}-001",
        "descricao": "",
        "cliente": "",
        "emissao": str(date.today()),
    }


def _servicos() -> list[dict]:
    return session.setdefault("servicos", [])


@app.get("/")
def home():
    if "usuario" not in session:
        return render_template_string(HTML, login=True, erro=session.pop("erro", None))

    orc = session.setdefault("orcamento", _estado_inicial())
    servicos = _servicos()
    total = sum(item["total"] for item in servicos)
    return render_template_string(
        HTML,
        login=False,
        usuario=session["usuario"],
        orc=orc,
        servicos=servicos,
        total=total,
        msg=session.pop("msg", None),
        erro=session.pop("erro", None),
    )


@app.post("/login")
def login():
    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "").strip()

    if usuario == USUARIO_PADRAO and senha == SENHA_PADRAO:
        session.clear()
        session["usuario"] = usuario
        session["orcamento"] = _estado_inicial()
        session["servicos"] = []
        return redirect(url_for("home"))

    session["erro"] = "Usuário ou senha inválidos."
    return redirect(url_for("home"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.post("/orcamento")
def salvar_orcamento():
    if "usuario" not in session:
        return redirect(url_for("home"))

    session["orcamento"] = {
        "numero": request.form.get("numero", "").strip(),
        "descricao": request.form.get("descricao", "").strip(),
        "cliente": request.form.get("cliente", "").strip(),
        "emissao": request.form.get("emissao", "").strip(),
    }
    session["msg"] = "Dados do orçamento salvos."
    return redirect(url_for("home"))


@app.post("/servicos")
def adicionar_servico():
    if "usuario" not in session:
        return redirect(url_for("home"))

    fase = request.form.get("fase", "").strip()
    servico = request.form.get("servico", "").strip()

    try:
        quantidade = float(request.form.get("quantidade", "0"))
        valor_unitario = float(request.form.get("valor_unitario", "0"))
    except ValueError:
        quantidade, valor_unitario = 0, 0

    if not fase or not servico or quantidade <= 0 or valor_unitario <= 0:
        session["erro"] = "Preencha fase, serviço, quantidade e valor unitário válidos."
        return redirect(url_for("home"))

    _servicos().append(
        {
            "id": str(uuid4()),
            "fase": fase,
            "servico": servico,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "total": quantidade * valor_unitario,
        }
    )
    session["msg"] = "Serviço adicionado com sucesso."
    return redirect(url_for("home"))


@app.post("/emitir")
def emitir():
    if "usuario" not in session:
        return redirect(url_for("home"))

    orc = session.get("orcamento", _estado_inicial())
    servicos = _servicos()

    if not all([orc.get("numero"), orc.get("descricao"), orc.get("cliente"), orc.get("emissao")]):
        session["erro"] = "Preencha todos os dados do orçamento antes de emitir."
        return redirect(url_for("home"))

    if len(servicos) == 0:
        session["erro"] = "Adicione pelo menos 1 serviço antes de emitir."
        return redirect(url_for("home"))

    session["msg"] = "Orçamento emitido com sucesso (protótipo)."
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
