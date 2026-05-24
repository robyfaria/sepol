"""Página de Orçamentos - fluxo independente de Obras"""

from datetime import datetime
import streamlit as st
from utils.auth import require_auth
from utils.layout import render_sidebar, render_top_logo
from utils.db import (
    get_orcamentos,
    create_orcamento_por_cliente,
    update_orcamento_status,
    get_clientes,
    create_cliente,
    get_orcamento,
    get_fases_por_orcamento,
    get_servicos_fase,
    marcar_orcamento_pdf_emitido,
)
from utils.auditoria import audit_insert, audit_update
from utils.pdf import gerar_pdf_orcamento

profile = require_auth()
render_sidebar(profile)
render_top_logo()

st.title("💼 Orçamentos")
st.caption("Cadastre e aprove orçamentos sem depender de uma obra.")

if "orc_pdf_cache" not in st.session_state:
    st.session_state["orc_pdf_cache"] = {}

clientes = get_clientes(ativo=True)
clientes_map = {c["id"]: c for c in clientes}

with st.container():
    st.markdown("### 🔎 Busca simples")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        busca = st.text_input("Buscar por cliente, número, versão ou status", placeholder="Ex: Maria, 125, APROVADO")
    with c2:
        status = st.selectbox("Status", options=[None, "RASCUNHO", "EMITIDO", "APROVADO", "REPROVADO", "CANCELADO"], format_func=lambda x: "Todos" if x is None else x)
    with c3:
        cliente_filter = st.selectbox("Cliente", options=[None] + [c["id"] for c in clientes], format_func=lambda x: "Todos" if x is None else clientes_map.get(x, {}).get("nome", "-"))

st.markdown("---")

st.subheader("➕ Novo orçamento")
modo = st.radio("Como criar", ["Cliente já cadastrado", "Novo cliente rápido"], horizontal=True)

if modo == "Cliente já cadastrado":
    if clientes:
        col1, col2 = st.columns([3, 1])
        with col1:
            cliente_novo = st.selectbox("Cliente", options=[c["id"] for c in clientes], format_func=lambda x: clientes_map.get(x, {}).get("nome", "-"), key="orc_novo_cliente_id")
        with col2:
            if st.button("Criar orçamento", type="primary", use_container_width=True):
                ok, msg, novo = create_orcamento_por_cliente(cliente_novo)
                if ok:
                    audit_insert("orcamentos", novo)
                    st.success(msg)
                    st.rerun()
                st.error(msg) if not ok else None
    else:
        st.warning("Nenhum cliente ativo cadastrado. Use 'Novo cliente rápido'.")
else:
    with st.form("form_cliente_rapido_orc"):
        n1, n2, n3 = st.columns(3)
        with n1:
            nome = st.text_input("Nome do cliente *")
        with n2:
            telefone = st.text_input("Telefone")
        with n3:
            endereco = st.text_input("Endereço")
        submit = st.form_submit_button("Salvar cliente e criar orçamento", type="primary")
        if submit:
            if not nome.strip():
                st.error("Informe o nome do cliente.")
            else:
                ok_c, msg_c, cliente = create_cliente(nome.strip(), telefone.strip(), endereco.strip())
                if ok_c:
                    audit_insert("clientes", cliente)
                    ok_o, msg_o, novo = create_orcamento_por_cliente(cliente["id"])
                    if ok_o:
                        audit_insert("orcamentos", novo)
                        st.success(f"{msg_c} {msg_o}")
                        st.rerun()
                    else:
                        st.error(msg_o)
                else:
                    st.error(msg_c)

st.markdown("---")
st.subheader("📋 Lista de orçamentos")
orcamentos = get_orcamentos(busca=busca, status=status, cliente_id=cliente_filter)

if not orcamentos:
    st.info("Nenhum orçamento encontrado com os filtros atuais.")
else:
    for orc in orcamentos:
        cliente_nome = (orc.get("clientes") or {}).get("nome", "-")
        c1, c2, c3 = st.columns([4, 2, 4])
        with c1:
            st.markdown(f"**Cliente:** {cliente_nome}")
            st.caption(f"Orçamento #{orc['id']} • v{orc.get('versao', '-')} • {orc.get('status', '-')}")
        with c2:
            st.markdown(f"**Valor final**")
            st.markdown(f"R$ {float(orc.get('valor_total_final', 0) or 0):,.2f}")
        with c3:
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                if orc.get("status") in ["RASCUNHO", "EMITIDO"] and st.button("✅ Aprovar", key=f"ap_{orc['id']}"):
                    ok, msg = update_orcamento_status(orc["id"], "APROVADO")
                    if ok:
                        audit_update("orcamentos", orc["id"], {"status": orc.get("status")}, {"status": "APROVADO"})
                        st.success(msg)
                        st.rerun()
                    st.error(msg) if not ok else None
            with a2:
                if orc.get("status") != "CANCELADO" and st.button("❌ Cancelar", key=f"ca_{orc['id']}"):
                    ok, msg = update_orcamento_status(orc["id"], "CANCELADO")
                    if ok:
                        audit_update("orcamentos", orc["id"], {"status": orc.get("status")}, {"status": "CANCELADO"})
                        st.success(msg)
                        st.rerun()
                    st.error(msg) if not ok else None
            with a3:
                if st.button("📄 Emitir PDF", key=f"pdf_{orc['id']}"):
                    dados = get_orcamento(orc["id"]) or dict(orc)
                    dados["pdf_emitido_em"] = datetime.now().isoformat()
                    fases = get_fases_por_orcamento(orc["id"])
                    servicos = {f["id"]: get_servicos_fase(f["id"]) for f in fases}
                    pdf_bytes = gerar_pdf_orcamento(dados, fases, servicos)
                    st.session_state["orc_pdf_cache"][orc["id"]] = pdf_bytes
                    marcar_orcamento_pdf_emitido(orc["id"], dados["pdf_emitido_em"])
                    st.success("PDF emitido com sucesso.")
            with a4:
                pdf_cache = st.session_state["orc_pdf_cache"].get(orc["id"])
                if pdf_cache:
                    st.download_button("⬇️ Baixar PDF", data=pdf_cache, file_name=f"Orcamento_{orc['id']}_v{orc.get('versao', 1)}.pdf", mime="application/pdf", key=f"down_{orc['id']}")

        if st.session_state["orc_pdf_cache"].get(orc["id"]):
            with st.expander(f"👁️ Visualizar PDF do orçamento #{orc['id']}"):
                st.info("PDF pronto para download no botão 'Baixar PDF'.")

        st.markdown("---")
