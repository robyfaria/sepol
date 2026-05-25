# App base (conceito antigo: app.py + Python + Streamlit + Supabase)

Protótipo refeito mantendo o conceito anterior solicitado:

- `app.py` como ponto de entrada único.
- Streamlit para UI.
- Supabase para persistência.
- Login mínimo para acesso ao fluxo.

## Funcionalidades atuais

- Login local mínimo (`admin` / `1234`).
- Fluxo de orçamento em 3 passos:
  1. Dados do orçamento e cliente.
  2. Fases e serviços.
  3. Revisão e emissão.
- Persistência no Supabase em tabelas normalizadas.
- Consulta de orçamentos com filtro por número e status.

## Executar

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SUPABASE_URL="https://<seu-projeto>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<sua-service-role-key>"
streamlit run app.py
```

## Banco de dados

As tabelas deste protótipo ficam na migration:

- `supabase/migrations/20260525233000_budget_module_init.sql`


## Usuário inicial gravado no banco

A migration de usuários cria automaticamente:

- Usuário: `admin`
- Senha: `1234`

Migration: `supabase/migrations/20260525234500_users_and_permissions.sql`
