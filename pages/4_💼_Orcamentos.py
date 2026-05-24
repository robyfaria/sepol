"""Página de Orçamentos - fluxo independente de Obras"""

import streamlit as st
from utils.auth import require_auth
from utils.layout import render_sidebar, render_top_logo
from utils.db import (
    get_orcamentos,
    create_orcamento_por_cliente,
    update_orcamento_status,
    get_clientes,
)
from utils.auditoria import audit_insert, audit_update

profile = require_auth()
render_sidebar(profile)
render_top_logo()

st.title("💼 Orçamentos")
st.caption("Cadastre e aprove orçamentos sem depender de uma obra.")

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    busca = st.text_input("🔍 Buscar", placeholder="Cliente ou observação")
with col_b:
    status = st.selectbox(
        "Status",
        options=[None, "RASCUNHO", "EMITIDO", "APROVADO", "REPROVADO", "CANCELADO"],
        format_func=lambda x: "Todos" if x is None else x,
    )
with col_c:
    clientes = get_clientes(ativo=True)
    cliente_filter = st.selectbox(
        "Cliente",
        options=[None] + [c["id"] for c in clientes],
        format_func=lambda x: "Todos" if x is None else next((c["nome"] for c in clientes if c["id"] == x), "-"),
    )

st.markdown("---")

st.subheader("➕ Novo orçamento")
if clientes:
    col1, col2 = st.columns([3, 1])
    with col1:
        cliente_novo = st.selectbox(
            "Cliente para novo orçamento",
            options=[c["id"] for c in clientes],
            format_func=lambda x: next((c["nome"] for c in clientes if c["id"] == x), "-"),
            key="orc_novo_cliente_id",
        )
    with col2:
        if st.button("Criar orçamento", type="primary", use_container_width=True):
            ok, msg, novo = create_orcamento_por_cliente(cliente_novo)
            if ok:
                audit_insert("orcamentos", novo)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
else:
    st.warning("Cadastre um cliente antes de criar orçamentos.")

st.markdown("---")
st.subheader("📋 Lista de orçamentos")

orcamentos = get_orcamentos(busca=busca, status=status, cliente_id=cliente_filter)
if not orcamentos:
    st.info("Nenhum orçamento encontrado.")
else:
    for orc in orcamentos:
        cliente_nome = (orc.get("clientes") or {}).get("nome", "-")
        obra_info = orc.get("obras")
        obra_label = obra_info.get("titulo") if obra_info else "Não vinculado"

        c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
        with c1:
            st.markdown(f"**Cliente:** {cliente_nome}")
            st.caption(f"Orçamento #{orc['id']} • v{orc.get('versao', '-')}")
        with c2:
            st.markdown(f"**Status:** {orc.get('status', '-')}")
            st.caption(f"Tipo: {orc.get('tipo_preco', '-')}")
        with c3:
            st.markdown(f"**Valor final:** R$ {float(orc.get('valor_total_final', 0) or 0):,.2f}")
            st.caption(f"Obra: {obra_label}")
        with c4:
            b1, b2 = st.columns(2)
            with b1:
                if orc.get("status") in ["RASCUNHO", "EMITIDO"] and st.button("✅ Aprovar", key=f"aprovar_{orc['id']}", use_container_width=True):
                    antes = {"status": orc.get("status")}
                    ok, msg = update_orcamento_status(orc["id"], "APROVADO")
                    if ok:
                        audit_update("orcamentos", orc["id"], antes, {"status": "APROVADO"})
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with b2:
                if orc.get("status") != "CANCELADO" and st.button("❌ Cancelar", key=f"cancel_{orc['id']}", use_container_width=True):
                    antes = {"status": orc.get("status")}
                    ok, msg = update_orcamento_status(orc["id"], "CANCELADO")
                    if ok:
                        audit_update("orcamentos", orc["id"], antes, {"status": "CANCELADO"})
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        st.markdown("---")
