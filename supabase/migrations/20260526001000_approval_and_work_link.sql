-- Aprovação e vínculo do orçamento à obra

create table if not exists obras (
  id uuid primary key default gen_random_uuid(),
  nome text not null unique,
  status text not null check (status in ('Planejamento','Em andamento','Concluida')) default 'Planejamento',
  created_at timestamptz not null default now()
);

alter table if exists orcamentos
  add column if not exists obra_id uuid references obras(id) on delete set null;

create index if not exists idx_orcamentos_obra_id on orcamentos(obra_id);

grant select, insert, update, delete on table obras to anon, authenticated;
alter table if exists obras disable row level security;
