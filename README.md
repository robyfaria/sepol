# Gestão de Obras de Pintura - Streamlit App

App de gestão de obras de pintura com interface amigável para usuários 60+.

## Requisitos

- Python 3.11+
- Conta Supabase com o banco de dados já configurado

## Configuração Local

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd streamlit-obras
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-anon-key-aqui
```

**IMPORTANTE:** Nunca use a `service_role` key no frontend!

### 5. Execute o app

```bash
streamlit run app.py
```

O app abrirá em `http://localhost:8501`

## Deploy no Streamlit Community Cloud

### 1. Suba o código para o GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Acesse [share.streamlit.io](https://share.streamlit.io)

1. Faça login com sua conta GitHub
2. Clique em "New app"
3. Selecione o repositório e branch
4. Defina o arquivo principal: `app.py`

### 3. Configure os Secrets

No painel do Streamlit Cloud, vá em **Settings > Secrets** e adicione:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-anon-key-aqui"
```

### 4. Deploy!

Clique em "Deploy" e aguarde. Seu app estará disponível em uma URL pública.

## Estrutura do Projeto

```
streamlit-obras/
├── app.py                 # Página principal e login
├── pages/
│   ├── 1_🏠_Obras.py
│   ├── 2_👥_Clientes.py
│   ├── 3_👷_Pessoas.py
│   ├── 4_📋_Orcamentos.py
│   ├── 5_📅_Agenda.py
│   ├── 6_💰_Financeiro.py
│   └── 7_⚙️_Configuracoes.py
├── utils/
│   ├── __init__.py
│   ├── auth.py            # Autenticação Supabase
│   ├── db.py              # Consultas ao banco
│   ├── auditoria.py       # Logs de auditoria
│   └── pdf.py             # Geração de PDF
├── sql/
│   └── schema_reference.sql
├── requirements.txt
├── README.md
└── .env.example
```

## Perfis de Usuário

- **ADMIN**: Acesso total (incluindo Financeiro e Configurações)
- **OPERACAO**: Acesso operacional (sem Financeiro/Configurações)

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório.
