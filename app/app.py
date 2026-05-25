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
from fpdf import FPDF
from fpdf.errors import FPDFException
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


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def inject_theme() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #F8FAFC; color: #0F172A; }
          h1, h2, h3, p, label, div { color: #0F172A; }
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


def login_view() -> None:
    st.title("Entrar no SEPOL 2.0")
    with st.form("login"):
        usuario = st.text_input("Usuário", value="")
        senha = st.text_input("Senha", type="password", value="")
        if st.form_submit_button("Entrar"):
            resp = (
                get_supabase().table("app_usuarios").select("usuario").eq("usuario", usuario.strip()).eq("senha", senha.strip()).eq("ativo", True).limit(1).execute()
            )
            if resp.data:
                st.session_state.auth = True
                st.session_state.user = resp.data[0]["usuario"]
                st.rerun()
            st.error("Usuário ou senha inválidos.")


def validar_ambiente_supabase(sb: Client) -> tuple[bool, str]:
    try:
        for table in ["app_usuarios", "clientes", "orcamentos", "orcamento_fases", "orcamento_servicos", "obras"]:
            sb.table(table).select("id").limit(1).execute()
        return True, ""
    except APIError as exc:
        return False, str(exc)


def calcular_totais(servicos: list[dict], desconto_tipo: str, desconto_valor: float) -> tuple[float, float, float]:
    subtotal = float(sum(float(s["total"]) for s in servicos))
    desconto_aplicado = desconto_valor if desconto_tipo == "valor" else subtotal * (desconto_valor / 100.0)
    desconto_aplicado = min(desconto_aplicado, subtotal)
    return subtotal, desconto_aplicado, subtotal - desconto_aplicado


def salvar_orcamento_db(sb: Client, payload: dict, servicos: list[dict]) -> str:
    cliente = sb.table("clientes").insert({
        "nome": payload["cliente_nome"],
        "endereco": payload.get("cliente_endereco") or None,
        "indicacao": payload.get("cliente_indicacao") or None,
    }).execute().data[0]

    subtotal, desconto_total, total_final = calcular_totais(servicos, payload["desconto_tipo"], payload["desconto_valor"])
    orc = sb.table("orcamentos").insert({
        "numero": payload["numero"], "descricao": payload["descricao"], "cliente_id": cliente["id"],
        "data_emissao": payload["data_emissao"], "previsao_inicio": _to_iso_or_none(payload.get("previsao_inicio")),
        "previsao_termino": _to_iso_or_none(payload.get("previsao_termino")), "status": "Emitido", "versao": 1,
        "total_mao_obra": total_final, "desconto_tipo": payload["desconto_tipo"], "desconto_valor": payload["desconto_valor"],
        "subtotal_mao_obra": subtotal,
    }).execute().data[0]

    fase_map: dict[str, str] = {}
    for s in servicos:
        if s["fase"] not in fase_map:
            fase = sb.table("orcamento_fases").insert({"orcamento_id": orc["id"], "descricao": s["fase"], "subtotal": 0}).execute().data[0]
            fase_map[s["fase"]] = fase["id"]
        sb.table("orcamento_servicos").insert({
            "fase_id": fase_map[s["fase"]], "descricao": s["servico"], "quantidade": s["quantidade"],
            "valor_unitario": s["valor_unitario"], "valor_total": s["total"],
        }).execute()

    for fase_nome, fase_id in fase_map.items():
        fase_total = sum(s["total"] for s in servicos if s["fase"] == fase_nome)
        sb.table("orcamento_fases").update({"subtotal": fase_total}).eq("id", fase_id).execute()
    return orc["id"]


def carregar_orcamento_detalhado(sb: Client, orc_id: str) -> tuple[dict, list[dict]]:
    orc = sb.table("orcamentos").select("*,cliente:clientes(*)").eq("id", orc_id).limit(1).execute().data[0]
    fases = sb.table("orcamento_fases").select("id,descricao").eq("orcamento_id", orc_id).execute().data
    servicos: list[dict] = []
    for f in fases:
        itens = sb.table("orcamento_servicos").select("id,descricao,quantidade,valor_unitario,valor_total").eq("fase_id", f["id"]).execute().data
        for i in itens:
            servicos.append({"id": i["id"], "fase": f["descricao"], "servico": i["descricao"], "quantidade": float(i["quantidade"]), "valor_unitario": float(i["valor_unitario"]), "total": float(i["valor_total"])})
    return orc, servicos


def atualizar_orcamento_emitido(sb: Client, orc_id: str, payload: dict, servicos: list[dict]) -> None:
    orc, _ = carregar_orcamento_detalhado(sb, orc_id)
    if orc["status"] == "Cancelado":
        raise ValueError("Orçamento cancelado não pode ser editado.")

    subtotal, desconto_total, total_final = calcular_totais(servicos, payload["desconto_tipo"], payload["desconto_valor"])
    nova_versao = int(orc.get("versao") or 1) + 1
    hoje = str(date.today())

    sb.table("clientes").update({"nome": payload["cliente_nome"], "endereco": payload.get("cliente_endereco") or None, "indicacao": payload.get("cliente_indicacao") or None}).eq("id", orc["cliente_id"]).execute()
    sb.table("orcamentos").update({
        "numero": payload["numero"], "descricao": payload["descricao"], "data_emissao": hoje,
        "previsao_inicio": _to_iso_or_none(payload.get("previsao_inicio")), "previsao_termino": _to_iso_or_none(payload.get("previsao_termino")),
        "versao": nova_versao, "subtotal_mao_obra": subtotal, "desconto_tipo": payload["desconto_tipo"], "desconto_valor": payload["desconto_valor"], "total_mao_obra": total_final,
    }).eq("id", orc_id).execute()

    fases = sb.table("orcamento_fases").select("id").eq("orcamento_id", orc_id).execute().data
    for f in fases:
        sb.table("orcamento_servicos").delete().eq("fase_id", f["id"]).execute()
    sb.table("orcamento_fases").delete().eq("orcamento_id", orc_id).execute()

    fase_map: dict[str, str] = {}
    for s in servicos:
        if s["fase"] not in fase_map:
            fase = sb.table("orcamento_fases").insert({"orcamento_id": orc_id, "descricao": s["fase"], "subtotal": 0}).execute().data[0]
            fase_map[s["fase"]] = fase["id"]
        sb.table("orcamento_servicos").insert({"fase_id": fase_map[s["fase"]], "descricao": s["servico"], "quantidade": s["quantidade"], "valor_unitario": s["valor_unitario"], "valor_total": s["total"]}).execute()

    for fase_nome, fase_id in fase_map.items():
        sb.table("orcamento_fases").update({"subtotal": sum(s["total"] for s in servicos if s["fase"] == fase_nome)}).eq("id", fase_id).execute()

    if orc.get("obra_id"):
        sb.table("obras").update({"previsao_inicio": _to_iso_or_none(payload.get("previsao_inicio")), "previsao_termino": _to_iso_or_none(payload.get("previsao_termino"))}).eq("id", orc["obra_id"]).execute()


def gerar_pdf_orcamento(orcamento: dict, servicos: list[dict]) -> bytes:
    def _safe_text(value: object) -> str:
        return str(value or "").replace("\n", " ").replace("\r", " ").strip()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Orçamento {orcamento['numero']} - v{orcamento.get('versao', 1)}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, f"Cliente: {_safe_text(orcamento['cliente']['nome'])}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Emissão: {_safe_text(orcamento['data_emissao'])}", new_x="LMARGIN", new_y="NEXT")
    if orcamento.get("previsao_inicio"):
        pdf.cell(0, 8, f"Previsão início: {_safe_text(orcamento['previsao_inicio'])}", new_x="LMARGIN", new_y="NEXT")
    if orcamento.get("previsao_termino"):
        pdf.cell(0, 8, f"Previsão término: {_safe_text(orcamento['previsao_termino'])}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    text_w = pdf.w - pdf.l_margin - pdf.r_margin
    for s in servicos:
        linha = (
            f"Fase: {_safe_text(s['fase'])} | Serviço: {_safe_text(s['servico'])} | "
            f"Qtd: {_safe_text(s['quantidade'])} | Unit: {money(float(s['valor_unitario']))} | "
            f"Total: {money(float(s['total']))}"
        )
        pdf.set_x(pdf.l_margin)
        try:
            pdf.multi_cell(text_w, 7, linha, new_x="LMARGIN", new_y="NEXT")
        except FPDFException:
            # Fallback defensivo para textos extremos/inesperados
            pdf.multi_cell(text_w, 7, f"Fase: {_safe_text(s['fase'])}", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(text_w, 7, f"Serviço: {_safe_text(s['servico'])}", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(text_w, 7, f"Qtd: {_safe_text(s['quantidade'])} | Unit: {money(float(s['valor_unitario']))}", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(text_w, 7, f"Total: {money(float(s['total']))}", new_x="LMARGIN", new_y="NEXT")

    subtotal = float(orcamento.get("subtotal_mao_obra") or orcamento.get("total_mao_obra") or 0)
    desconto = float(orcamento.get("desconto_valor") or 0)
    pdf.ln(2)
    pdf.cell(0, 8, f"Subtotal: {money(subtotal)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Desconto ({orcamento.get('desconto_tipo','valor')}): {desconto}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total final: {money(float(orcamento.get('total_mao_obra') or 0))}", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output(dest="S").encode("latin-1", errors="replace"))


def aprovar_orcamento(sb: Client, orcamento_id: str) -> None:
    sb.table("orcamentos").update({"status": "Aprovado"}).eq("id", orcamento_id).eq("status", "Emitido").execute()


def cancelar_orcamento(sb: Client, orcamento_id: str) -> None:
    sb.table("orcamentos").update({"status": "Cancelado"}).eq("id", orcamento_id).neq("status", "Aprovado").execute()


def garantir_obra(sb: Client, nome_obra: str, previsao_inicio: str | None, previsao_termino: str | None) -> str:
    nome = nome_obra.strip()
    if not nome:
        raise ValueError("Informe o nome da obra.")
    existente = sb.table("obras").select("id").eq("nome", nome).limit(1).execute().data
    if existente:
        return existente[0]["id"]
    obra = sb.table("obras").insert({"nome": nome, "status": "Planejamento", "previsao_inicio": previsao_inicio, "previsao_termino": previsao_termino}).execute().data[0]
    return obra["id"]


def vincular_orcamento_obra(sb: Client, orcamento_id: str, obra_nome: str) -> None:
    orc = sb.table("orcamentos").select("id,status,previsao_inicio,previsao_termino").eq("id", orcamento_id).limit(1).execute().data[0]
    obra_id = garantir_obra(sb, obra_nome, orc.get("previsao_inicio"), orc.get("previsao_termino"))
    sb.table("obras").update({"previsao_inicio": orc.get("previsao_inicio"), "previsao_termino": orc.get("previsao_termino")}).eq("id", obra_id).execute()
    sb.table("orcamentos").update({"obra_id": obra_id}).eq("id", orcamento_id).eq("status", "Aprovado").execute()


def app_view(sb: Client) -> None:
    st.title("Orçamentos")

    with st.expander("Novo orçamento", expanded=True):
        o = {"numero": f"{date.today().year}-{uuid4().hex[:6]}", "descricao": "", "cliente_nome": "", "cliente_endereco": "", "cliente_indicacao": "", "data_emissao": str(date.today()), "previsao_inicio": None, "previsao_termino": None, "desconto_tipo": "valor", "desconto_valor": 0.0}
        c1, c2 = st.columns(2)
        o["numero"] = c1.text_input("Número", value=o["numero"], key="novo_num")
        o["descricao"] = c2.text_input("Descrição", key="novo_desc")
        o["cliente_nome"] = c1.text_input("Cliente", key="novo_cli")
        o["cliente_endereco"] = c2.text_input("Endereço", key="novo_end")
        o["cliente_indicacao"] = c1.text_input("Indicação", key="novo_ind")
        o["previsao_inicio"] = _to_iso_or_none(c1.date_input("Previsão início", value=None, key="novo_pi"))
        o["previsao_termino"] = _to_iso_or_none(c2.date_input("Previsão término", value=None, key="novo_pt"))
        o["desconto_tipo"] = c1.selectbox("Tipo de desconto", ["valor", "percentual"], key="novo_desc_tipo")
        o["desconto_valor"] = float(c2.number_input("Desconto", min_value=0.0, step=10.0, key="novo_desc_val"))

        st.session_state.setdefault("novo_servicos", [])
        with st.form("novo_servico", clear_on_submit=True):
            s1, s2, s3, s4 = st.columns([2, 2, 1, 1])
            fase = s1.text_input("Fase")
            servico = s2.text_input("Serviço")
            qtd = s3.number_input("Qtd", min_value=0.01, step=1.0, value=1.0)
            unit = s4.number_input("Unit.", min_value=0.01, step=10.0, value=100.0)
            if st.form_submit_button("Adicionar"):
                st.session_state.novo_servicos.append({"id": str(uuid4()), "fase": fase.strip(), "servico": servico.strip(), "quantidade": float(qtd), "valor_unitario": float(unit), "total": float(qtd * unit)})

        for s in list(st.session_state.novo_servicos):
            cols = st.columns([2, 3, 2, 2, 1])
            cols[0].write(s["fase"])
            cols[1].write(s["servico"])
            cols[2].write(s["quantidade"])
            cols[3].write(money(s["total"]))
            if cols[4].button("Excluir", key=f"del_new_{s['id']}"):
                st.session_state.novo_servicos = [x for x in st.session_state.novo_servicos if x["id"] != s["id"]]
                st.rerun()

        subtotal, desconto_aplicado, total_final = calcular_totais(st.session_state.novo_servicos, o["desconto_tipo"], o["desconto_valor"])
        st.caption(f"Subtotal: {money(subtotal)} | Desconto: {money(desconto_aplicado)} | Total final: {money(total_final)}")

        if st.button("Emitir orçamento"):
            if not o["numero"] or not o["descricao"] or not o["cliente_nome"] or not st.session_state.novo_servicos:
                st.error("Preencha dados obrigatórios e adicione ao menos 1 serviço.")
            else:
                salvar_orcamento_db(sb, o, st.session_state.novo_servicos)
                st.session_state.novo_servicos = []
                st.success("Orçamento emitido.")
                st.rerun()

    st.divider()
    data = sb.table("orcamentos").select("id,numero,descricao,status,versao,total_mao_obra,data_emissao").order("created_at", desc=True).limit(30).execute().data
    for item in data:
        with st.container(border=True):
            st.write(f"**{item['numero']}** • {item['descricao']}")
            st.caption(f"Status: {item['status']} | Versão: {item.get('versao', 1)} | Emissão: {item['data_emissao']} | Total: {money(float(item.get('total_mao_obra') or 0))}")
            c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
            if item["status"] == "Emitido":
                if c1.button("Aprovar", key=f"apr_{item['id']}"):
                    aprovar_orcamento(sb, item["id"])
                    st.rerun()
                if c2.button("Cancelar", key=f"can_{item['id']}"):
                    cancelar_orcamento(sb, item["id"])
                    st.rerun()
            if item["status"] == "Aprovado":
                nome_obra = c3.text_input("Obra", key=f"obra_{item['id']}")
                if c4.button("Vincular obra", key=f"vin_{item['id']}"):
                    vincular_orcamento_obra(sb, item["id"], nome_obra)
                    st.rerun()

            if item["status"] in ["Emitido", "Aprovado"]:
                with st.expander(f"Editar orçamento {item['numero']}"):
                    orc, servicos = carregar_orcamento_detalhado(sb, item["id"])
                    ed = {
                        "numero": st.text_input("Número", value=orc["numero"], key=f"ed_num_{item['id']}"),
                        "descricao": st.text_input("Descrição", value=orc["descricao"], key=f"ed_desc_{item['id']}"),
                        "cliente_nome": st.text_input("Cliente", value=orc["cliente"]["nome"], key=f"ed_cli_{item['id']}"),
                        "cliente_endereco": st.text_input("Endereço", value=orc["cliente"].get("endereco") or "", key=f"ed_end_{item['id']}"),
                        "cliente_indicacao": st.text_input("Indicação", value=orc["cliente"].get("indicacao") or "", key=f"ed_ind_{item['id']}"),
                        "previsao_inicio": _to_iso_or_none(st.date_input("Prev. início", value=date.fromisoformat(orc["previsao_inicio"]) if orc.get("previsao_inicio") else None, key=f"ed_pi_{item['id']}")),
                        "previsao_termino": _to_iso_or_none(st.date_input("Prev. término", value=date.fromisoformat(orc["previsao_termino"]) if orc.get("previsao_termino") else None, key=f"ed_pt_{item['id']}")),
                        "desconto_tipo": st.selectbox("Tipo desconto", ["valor", "percentual"], index=0 if (orc.get("desconto_tipo") or "valor") == "valor" else 1, key=f"ed_dt_{item['id']}"),
                        "desconto_valor": float(st.number_input("Desconto", min_value=0.0, value=float(orc.get("desconto_valor") or 0), key=f"ed_dv_{item['id']}")),
                    }
                    temp_key = f"temp_serv_{item['id']}"
                    if temp_key not in st.session_state:
                        st.session_state[temp_key] = servicos
                    for s in list(st.session_state[temp_key]):
                        cols = st.columns([2, 3, 2, 2, 1])
                        cols[0].write(s["fase"])
                        cols[1].write(s["servico"])
                        cols[2].write(s["quantidade"])
                        cols[3].write(money(s["total"]))
                        if cols[4].button("Excluir", key=f"del_ed_{item['id']}_{s['id']}"):
                            st.session_state[temp_key] = [x for x in st.session_state[temp_key] if x["id"] != s["id"]]
                            st.rerun()
                    with st.form(f"add_ed_{item['id']}", clear_on_submit=True):
                        s1, s2, s3, s4 = st.columns([2, 2, 1, 1])
                        fase = s1.text_input("Nova fase")
                        servico = s2.text_input("Novo serviço")
                        qtd = s3.number_input("Qtd", min_value=0.01, step=1.0, value=1.0)
                        unit = s4.number_input("Unit", min_value=0.01, step=10.0, value=100.0)
                        if st.form_submit_button("Adicionar serviço"):
                            st.session_state[temp_key].append({"id": str(uuid4()), "fase": fase.strip(), "servico": servico.strip(), "quantidade": float(qtd), "valor_unitario": float(unit), "total": float(qtd * unit)})
                            st.rerun()
                    subt, desc_apl, tot = calcular_totais(st.session_state[temp_key], ed["desconto_tipo"], ed["desconto_valor"])
                    st.caption(f"Subtotal: {money(subt)} | Desconto: {money(desc_apl)} | Total final: {money(tot)}")
                    if st.button("Salvar edição", key=f"save_{item['id']}"):
                        atualizar_orcamento_emitido(sb, item["id"], ed, st.session_state[temp_key])
                        del st.session_state[temp_key]
                        st.success("Orçamento atualizado: versão incrementada e emissão atualizada para hoje.")
                        st.rerun()

            if item["status"] != "Cancelado":
                orc_pdf, srv_pdf = carregar_orcamento_detalhado(sb, item["id"])
                pdf_bytes = gerar_pdf_orcamento(orc_pdf, srv_pdf)
                st.download_button("Baixar PDF", data=pdf_bytes, file_name=f"orcamento_{item['numero']}.pdf", mime="application/pdf", key=f"pdf_{item['id']}")

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
    sb = get_supabase()
    ok, detalhe = validar_ambiente_supabase(sb)
    if not ok:
        st.error("Supabase indisponível")
        st.code(detalhe, language="text")
        return
    app_view(sb)


if __name__ == "__main__":
    main()
