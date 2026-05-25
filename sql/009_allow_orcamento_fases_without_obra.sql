begin;

-- Permite fases de orçamento independentes de obra
alter table public.obra_fases
  alter column obra_id drop not null;

commit;
