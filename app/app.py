"""SEPOL 2.0 - Protótipo Streamlit + Supabase.

Execução:
    streamlit run app.py
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from uuid import uuid4

import streamlit as st
from postgrest.exceptions import APIError
from supabase import Client, create_client

st.set_page_config(page_title="SEPOL 2.0", page_icon="🧱", layout="wide")


def _to_iso_or_none(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, str) and value.strip() == "":
        return None
    return str(value)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #F8FAFC; color: #0F172A; }
          h1, h2, h3, p, label, div { color: #0F172A; }
          .card { border:1px solid #CBD5E1; border-radius:12px; padding:18px; background:#ffffff; margin-bottom:14px; }
          .step-chip { display:inline-block; background:#e2e8f0; color:#0F172A; border-radius:999px; padding:6px 14px; margin-right:8px; font-weight:600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY (ou SUPABASE_ANON_KEY).")
    return create_client(url, key)


def init_state() -> None:
    st.session_state.setdefault("auth", False)
    st.session_state.setdefault("user", "")
    st.session_state.setdefault("orcamento", {
        "numero": f"{date.today().year}-001",
        "descricao": "",
        "cliente_nome": "",
        "cliente_endereco": "",
        "cliente_indicacao": "",
        "data_emissao": str(date.today()),
        "previsao_inicio": None,
        "previsao_termino": None,
    })
    st.session_state.setdefault("servicos", [])
    st.session_state.setdefault("orcamento_id", None)


def _reset_orcamento_form() -> None:
    st.session_state.orcamento = {
        "numero": f"{date.today().year}-001",
        "descricao": "",
        "cliente_nome": "",
        "cliente_endereco": "",
        "cliente_indicacao": "",
        "data_emissao": str(date.today()),
        "previsao_inicio": None,
        "previsao_termino": None,
    }
    st.session_state.servicos = []


def login_view() -> None:
    st.title("Entrar no SEPOL 2.0")
    st.caption("Login mínimo para protótipo (usuário gravado no Supabase).")
    with st.form("login"):
        usuario = st.text_input("Usuário", value="")
        senha = st.text_input("Senha", type="password", value="")
        ok = st.form_submit_button("Entrar")
        if ok:
            try:
                sb = get_supabase()
                resp = (
                    sb.table("app_usuarios")
                    .select("usuario,ativo")
                    .eq("usuario", usuario.strip())
                    .eq("senha", senha.strip())
                    .eq("ativo", True)
                    .limit(1)
                    .execute()
                )
                if resp.data:
                    st.session_state.auth = True
                    st.session_state.user = resp.data[0]["usuario"]
                    st.success("Login realizado com sucesso.")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
            except APIError as exc:
                st.error("Não foi possível validar login no Supabase.")
                st.code(str(exc), language="text")
            except Exception as exc:
                st.error(f"Erro de configuração: {exc}")


def validar_ambiente_supabase(sb: Client) -> tuple[bool, str]:
    """Valida se tabelas mínimas estão acessíveis no PostgREST."""
    try:
        sb.table("app_usuarios").select("id").limit(1).execute()
        sb.table("clientes").select("id").limit(1).execute()
        sb.table("orcamentos").select("id").limit(1).execute()
        sb.table("orcamento_fases").select("id").limit(1).execute()
        sb.table("orcamento_servicos").select("id").limit(1).execute()
        return True, ""
    except APIError as exc:
        return False, str(exc)



def salvar_orcamento_db(sb: Client) -> str:
    o = st.session_state.orcamento

    cliente_payload = {
        "nome": o["cliente_nome"],
        "endereco": o["cliente_endereco"] or None,
        "indicacao": o["cliente_indicacao"] or None,
    }
    cliente = sb.table("clientes").insert(cliente_payload).execute().data[0]

    orc_payload = {
        "numero": o["numero"],
        "descricao": o["descricao"],
        "cliente_id": cliente["id"],
        "data_emissao": o["data_emissao"],
        "previsao_inicio": _to_iso_or_none(o["previsao_inicio"]),
        "previsao_termino": _to_iso_or_none(o["previsao_termino"]),
        "status": "Rascunho",
        "versao": 1,
        "total_mao_obra": float(sum(Decimal(str(s["total"])) for s in st.session_state.servicos)),
    }
    orcamento = sb.table("orcamentos").insert(orc_payload).execute().data[0]

    fase_map: dict[str, str] = {}
    for s in st.session_state.servicos:
        if s["fase"] not in fase_map:
            fase = sb.table("orcamento_fases").insert({
                "orcamento_id": orcamento["id"],
                "descricao": s["fase"],
                "subtotal": 0,
            }).execute().data[0]
            fase_map[s["fase"]] = fase["id"]

        sb.table("orcamento_servicos").insert({
            "fase_id": fase_map[s["fase"]],
            "descricao": s["servico"],
            "quantidade": s["quantidade"],
            "valor_unitario": s["valor_unitario"],
            "valor_total": s["total"],
        }).execute()

    for nome_fase, fase_id in fase_map.items():
        subtotal = sum(s["total"] for s in st.session_state.servicos if s["fase"] == nome_fase)
        sb.table("orcamento_fases").update({"subtotal": subtotal}).eq("id", fase_id).execute()

    st.session_state.orcamento_id = orcamento["id"]
    return orcamento["id"]


def app_view(sb: Client) -> None:
    st.title("Novo orçamento")
    st.caption(f"Olá, {st.session_state.user}. Fluxo guiado em 3 passos (layout 60+).")
    st.markdown('<span class="step-chip">1. Dados</span><span class="step-chip">2. Fases e serviços</span><span class="step-chip">3. Revisão e emissão</span>', unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("Passo 1 — Dados do orçamento")
        o = st.session_state.orcamento
        col1, col2 = st.columns(2)
        o["numero"] = col1.text_input("Número", value=o["numero"])
        o["descricao"] = col2.text_input("Descrição", value=o["descricao"])
        o["cliente_nome"] = col1.text_input("Cliente", value=o["cliente_nome"])
        o["cliente_endereco"] = col2.text_input("Endereço", value=o["cliente_endereco"])
        o["cliente_indicacao"] = col1.text_input("Indicação", value=o["cliente_indicacao"])
        o["data_emissao"] = str(col2.date_input("Data de emissão", value=date.fromisoformat(o["data_emissao"])))
        previsao_inicio = col1.date_input("Previsão de início (opcional)", value=None)
        previsao_termino = col2.date_input("Previsão de término (opcional)", value=None)
        o["previsao_inicio"] = _to_iso_or_none(previsao_inicio)
        o["previsao_termino"] = _to_iso_or_none(previsao_termino)

    with st.container(border=True):
        st.subheader("Passo 2 — Fases e serviços")
        with st.form("novo_servico", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            fase = c1.text_input("Fase")
            servico = c2.text_input("Serviço")
            quantidade = c3.number_input("Quantidade", min_value=0.01, step=1.0, value=1.0)
            valor_unitario = c4.number_input("Valor unitário (R$)", min_value=0.01, step=10.0, value=100.0)
            add = st.form_submit_button("Adicionar serviço")
            if add:
                st.session_state.servicos.append({
                    "id": str(uuid4()),
                    "fase": fase.strip(),
                    "servico": servico.strip(),
                    "quantidade": float(quantidade),
                    "valor_unitario": float(valor_unitario),
                    "total": float(quantidade * valor_unitario),
                })
                st.success("Serviço adicionado com sucesso.")

        if st.session_state.servicos:
            st.dataframe(st.session_state.servicos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum serviço adicionado.")

    with st.container(border=True):
        st.subheader("Passo 3 — Revisão e emissão")
        total = float(sum(s["total"] for s in st.session_state.servicos))
        st.metric("Total mão-de-obra", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        emitir = st.button("Emitir orçamento")
        if emitir:
            if not st.session_state.orcamento["numero"] or not st.session_state.orcamento["descricao"] or not st.session_state.orcamento["cliente_nome"]:
                st.error("Preencha número, descrição e cliente antes de emitir.")
                return
            if not st.session_state.servicos:
                st.error("Adicione pelo menos 1 serviço antes de emitir.")
                return

            try:
                oid = salvar_orcamento_db(sb)
                sb.table("orcamentos").update({"status": "Emitido"}).eq("id", oid).execute()
                st.success(f"Orçamento emitido com sucesso. ID: {oid}")
                _reset_orcamento_form()
                st.rerun()
            except APIError as exc:
                st.error("Não foi possível emitir o orçamento no Supabase.")
                st.caption("Verifique se as migrations foram aplicadas e se a chave usada possui permissão de INSERT/UPDATE.")
                st.code(str(exc), language="text")
                return

    st.divider()
    st.subheader("Consulta de orçamentos")
    q_numero = st.text_input("Filtro por número")
    q_status = st.selectbox("Status", ["Todos", "Rascunho", "Emitido", "Aprovado", "Cancelado"])

    try:
        query = sb.table("orcamentos").select(
            "id,numero,descricao,status,total_mao_obra,data_emissao,cliente:clientes(nome)"
        ).order("created_at", desc=True).limit(50)
        if q_numero:
            query = query.ilike("numero", f"%{q_numero}%")
        if q_status != "Todos":
            query = query.eq("status", q_status)

        data = query.execute().data
        rows = []
        for item in data:
            cliente = item.get("cliente")
            if isinstance(cliente, dict):
                cliente_nome = cliente.get("nome", "")
            else:
                cliente_nome = ""

            rows.append({
                "id": item.get("id"),
                "numero": item.get("numero"),
                "descricao": item.get("descricao"),
                "status": item.get("status"),
                "total_mao_obra": item.get("total_mao_obra"),
                "data_emissao": item.get("data_emissao"),
                "cliente": cliente_nome,
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)
    except APIError as exc:
        st.warning("Não foi possível carregar a consulta de orçamentos no Supabase.")
        st.caption(
            "Confira se as migrations foram aplicadas e se as tabelas "
            "clientes/orcamentos/orcamento_fases/orcamento_servicos existem."
        )
        st.code(str(exc), language="text")

    if st.button("Sair"):
        st.session_state.auth = False
        st.session_state.user = ""
        st.rerun()


def main() -> None:
    inject_theme()
    init_state()

    if not st.session_state.auth:
        login_view()
        return

    try:
        sb = get_supabase()
    except Exception as exc:
        st.error(f"Erro de configuração Supabase: {exc}")
        return

    ok, detalhe = validar_ambiente_supabase(sb)
    if not ok:
        st.error("Supabase indisponível para o módulo de orçamento.")
        st.caption("Aplique as migrations e confirme permissões da chave (service role recomendada para protótipo).")
        st.code(detalhe, language="text")
        return

    app_view(sb)


if __name__ == "__main__":
    main()
