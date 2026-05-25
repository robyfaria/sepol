# SEPOL — Gestão de Obras de Pintura (Streamlit + Supabase)

Sistema web para gestão de obras de pintura com foco em operação diária: clientes, profissionais, obras, orçamentos por versão, agenda/alocação de equipe, financeiro (recebimentos e pagamentos), auditoria e exportação de PDFs.

---

## 1) Visão geral funcional

O app é dividido em páginas Streamlit:

- **Início / Login (`Inicio.py`)**
  - Autenticação por e-mail/senha via Supabase Auth.
  - Carregamento de perfil do usuário em `usuarios_app`.
  - Dashboard rápido com indicadores (obras, orçamentos, pessoas, clientes, recebimentos/pagamentos do mês, fases não concluídas).

- **Obras (`pages/1_🏠_Obras.py`)**
  - CRUD de obras.
  - Gestão de orçamentos por obra com versões.
  - Gestão de fases e serviços por fase.
  - Definição de tipo de preço do orçamento (`POR_FASE` / `POR_SERVICO`).
  - Atualização de desconto e validade de orçamento.
  - Geração de PDF de orçamento para download.
  - Agenda operacional da obra e apontamentos.

- **Clientes (`pages/2_👥_Clientes.py`)**
  - CRUD de clientes e ativação/inativação.

- **Pessoas (`pages/3_👷_Pessoas.py`)**
  - CRUD de profissionais (`PINTOR`, `AJUDANTE`, `TERCEIRO`) e controle de ativo.

- **Agenda (`pages/5_📅_Agenda.py`)**
  - Visualização de alocações por data/obra e confirmações.

- **Financeiro (`pages/6_💰_Financeiro.py`)** *(somente ADMIN)*
  - Recebimentos (aberto/vencido/pago/cancelado).
  - Pagamentos e itens de pagamento vinculados a apontamentos.
  - Relatório mensal com exportação de PDF.

- **Configurações (`pages/7_⚙️_Configuracoes.py`)** *(somente ADMIN)*
  - Gestão de usuários do app (`usuarios_app`).
  - Consulta de logs de auditoria.
  - Catálogo de serviços.

---

## 2) Stack e arquitetura

- **Frontend**: Streamlit multipage.
- **Backend de dados/autenticação**: Supabase (Postgres + Auth).
- **Acesso ao banco**: cliente Supabase via `utils/db.py`.
- **Regras de negócio no banco**: funções, triggers, policies e índices em SQL.
- **Auditoria de uso**: tabela `auditoria` + chamadas `utils/auditoria.py`.
- **PDFs**: geração local em memória com `fpdf2` (`utils/pdf.py`).

Fluxo resumido:
1. Usuário autentica via Supabase Auth.
2. App valida perfil em `public.usuarios_app`.
3. Páginas executam CRUD pela camada `utils/db.py`.
4. Triggers SQL recalculam campos derivados (totais/rateios etc.).
5. Logs de operação podem ser gravados na auditoria.
6. PDFs são gerados em memória e disponibilizados por download.

---

## 3) Pré-requisitos

- Python **3.11+**
- Projeto Supabase ativo
- Dependências do `requirements.txt`

Dependências principais:
- `streamlit`
- `supabase`
- `python-dotenv`
- `fpdf2`
- `pandas`

---

## 4) Instalação local

```bash
git clone <seu-repositorio>
cd sepol
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

---

## 5) Configuração de ambiente

Crie um arquivo `.env` na raiz (ou configure os mesmos valores em `st.secrets`):

```env
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<sua-anon-key>

# opcionais (uso específico de storage compatível S3)
SUPABASE_STORAGE_URL=
SUPABASE_STORAGE_REGION=
```

### Variáveis suportadas

| Variável | Obrigatória | Descrição |
|---|---:|---|
| `SUPABASE_URL` | Sim | URL do projeto Supabase |
| `SUPABASE_ANON_KEY` | Sim | Chave pública `anon` |
| `SUPABASE_STORAGE_URL` | Não | Override do endpoint de storage |
| `SUPABASE_STORAGE_REGION` | Não | Região para headers S3 |

> **Segurança:** nunca use `service_role` no frontend Streamlit.

---

## 6) Banco de dados (SQL)

A pasta `sql/` contém scripts versionados de estrutura e ajustes.

### Scripts disponíveis

- `sql/001_core.sql` — schema base completo (tabelas, funções, triggers, RLS/policies e grants centrais).
- `sql/002_add_scripts.sql` — ajustes de alocação/apontamento/rateio.
- `sql/003_add_scripts.sql` — ajustes adicionais de triggers de apontamento.
- `sql/004_add_pdf_url.sql` — coluna `orcamentos.pdf_url`.
- `sql/005_add_orcamento_validade.sql` — colunas `pdf_emitido_em` e `valido_ate`.
- `sql/006_grant_sequence_permissions.sql` — grants para uso de sequences por `authenticated`.
- `sql/007_add_orcamento_tipo_preco.sql` — coluna `tipo_preco` (`POR_FASE`/`POR_SERVICO`).
- `sql/008_orcamento_desacoplado_obra.sql` — migração incremental para desacoplar orçamentos de obras e inverter o vínculo (obra referencia orçamento aprovado).
- `sql/002_add_pagamentos_pessoa.sql` — coluna `pessoa_id` em `pagamentos`.
- `sql/009_allow_orcamento_fases_without_obra.sql` — permite fases de orçamento sem vínculo obrigatório com obra.
- `sql/000_schema_reference.sql` — referência histórica de schema (não executar como migração principal).

### Ordem sugerida para ambiente novo

1. `001_core.sql`
2. `002_add_scripts.sql`
3. `003_add_scripts.sql`
4. `004_add_pdf_url.sql`
5. `005_add_orcamento_validade.sql`
6. `006_grant_sequence_permissions.sql`
7. `007_add_orcamento_tipo_preco.sql`
8. `008_orcamento_desacoplado_obra.sql`
9. `002_add_pagamentos_pessoa.sql`
10. `009_allow_orcamento_fases_without_obra.sql`

> Execute via SQL Editor do Supabase, validando cada script antes de seguir.

---

## 7) Execução

```bash
streamlit run Inicio.py
```

Aplicação local padrão: `http://localhost:8501`

---

## 8) Regras de acesso

Perfis esperados em `public.usuarios_app`:

- `ADMIN`
  - acesso total, incluindo **Financeiro** e **Configurações**.
- `OPERACAO`
  - acesso operacional sem rotas administrativas.

As páginas usam `require_auth()` ou `require_admin()` para proteção.

---

## 9) Estrutura do repositório

```text
sepol/
├── Inicio.py
├── home.py
├── pages/
│   ├── 1_🏠_Obras.py
│   ├── 2_👥_Clientes.py
│   ├── 3_👷_Pessoas.py
│   ├── 5_📅_Agenda.py
│   ├── 6_💰_Financeiro.py
│   └── 7_⚙️_Configuracoes.py
├── utils/
│   ├── __init__.py
│   ├── auth.py
│   ├── auditoria.py
│   ├── db.py
│   ├── layout.py
│   └── pdf.py
├── sql/
│   ├── 000_schema_reference.sql
│   ├── 001_core.sql
│   ├── 002_add_pagamentos_pessoa.sql
│   ├── 002_add_scripts.sql
│   ├── 003_add_scripts.sql
│   ├── 004_add_pdf_url.sql
│   ├── 005_add_orcamento_validade.sql
│   ├── 006_grant_sequence_permissions.sql
│   └── 007_add_orcamento_tipo_preco.sql
├── assets/
│   ├── icon.ico
│   └── logo.png
├── requirements.txt
├── .env.example
└── README.md
```

---

## 10) PDFs gerados pelo sistema

- **Orçamento** (`pages/1_🏠_Obras.py` + `utils/pdf.py`)
  - nome do arquivo segue o padrão:
  - `Orcamento_{numero do orcamento}_{versão do orcamento}_{nome da obra}.pdf`

- **Extrato financeiro mensal** (`pages/6_💰_Financeiro.py` + `utils/pdf.py`)
  - nome do arquivo:
  - `extrato_financeiro_{MM}_{AAAA}.pdf`

---

## 11) Boas práticas operacionais

- Mantenha scripts SQL versionados (não altere histórico já aplicado em produção sem controle).
- Cadastre usuários no Supabase Auth e também em `usuarios_app`.
- Valide permissões de perfil antes de homologar telas administrativas.
- Não exponha credenciais sensíveis em código/README.

---

## 12) Troubleshooting rápido

- **Mensagem de configuração ausente no login**
  - conferir `SUPABASE_URL` e `SUPABASE_ANON_KEY` no `.env`/secrets.

- **Usuário autenticou, mas não entra no sistema**
  - verificar se existe registro ativo em `public.usuarios_app` com `auth_user_id` correspondente.

- **Erro de insert com `bigserial`/sequence**
  - garantir execução de `sql/006_grant_sequence_permissions.sql`.

- **Campos de orçamento não aparecem como esperado**
  - confirmar execução de `sql/004`, `sql/005` e `sql/007`.

---

## 13) Licença e suporte

Uso interno do projeto. Para evolução funcional, abra issue/PR com contexto da regra de negócio e impacto no banco.
