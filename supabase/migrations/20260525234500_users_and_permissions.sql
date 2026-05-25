-- Módulo de usuários + permissões para protótipo Streamlit

create extension if not exists pgcrypto;

create table if not exists app_usuarios (
  id uuid primary key default gen_random_uuid(),
  usuario text not null unique,
  senha text not null,
  nome text,
  ativo boolean not null default true,
  created_at timestamptz not null default now()
);

insert into app_usuarios (usuario, senha, nome, ativo)
values ('admin', '1234', 'Administrador', true)
on conflict (usuario) do update
set senha = excluded.senha,
    nome = excluded.nome,
    ativo = true;

-- Permissões para uso via anon/authenticated no protótipo
grant usage on schema public to anon, authenticated;

grant select, insert, update, delete on table
  app_usuarios,
  clientes,
  orcamentos,
  orcamento_fases,
  orcamento_servicos
to anon, authenticated;

-- RLS desabilitado para simplificar o protótipo com chave anon/service
alter table if exists app_usuarios disable row level security;
alter table if exists clientes disable row level security;
alter table if exists orcamentos disable row level security;
alter table if exists orcamento_fases disable row level security;
alter table if exists orcamento_servicos disable row level security;
