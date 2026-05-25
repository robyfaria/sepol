-- Módulo de orçamento (protótipo Streamlit + Supabase)

create extension if not exists pgcrypto;

create table if not exists clientes (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  endereco text,
  indicacao text,
  created_at timestamptz not null default now()
);

create table if not exists orcamentos (
  id uuid primary key default gen_random_uuid(),
  numero text not null unique,
  descricao text not null,
  cliente_id uuid not null references clientes(id) on delete restrict,
  data_emissao date not null,
  previsao_inicio date,
  previsao_termino date,
  status text not null check (status in ('Rascunho','Emitido','Aprovado','Cancelado')) default 'Rascunho',
  versao integer not null default 1,
  total_mao_obra numeric(14,2) not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists orcamento_fases (
  id uuid primary key default gen_random_uuid(),
  orcamento_id uuid not null references orcamentos(id) on delete cascade,
  descricao text not null,
  subtotal numeric(14,2) not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists orcamento_servicos (
  id uuid primary key default gen_random_uuid(),
  fase_id uuid not null references orcamento_fases(id) on delete cascade,
  descricao text not null,
  quantidade numeric(12,2) not null default 1,
  valor_unitario numeric(14,2) not null,
  valor_total numeric(14,2) not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_orcamentos_status on orcamentos(status);
create index if not exists idx_orcamentos_numero on orcamentos(numero);
create index if not exists idx_fases_orcamento_id on orcamento_fases(orcamento_id);
create index if not exists idx_servicos_fase_id on orcamento_servicos(fase_id);
