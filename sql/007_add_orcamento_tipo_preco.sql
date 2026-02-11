-- Adiciona tipo de precificação do orçamento
alter table public.orcamentos
add column if not exists tipo_preco varchar(20)
  not null default 'POR_FASE'
  check (tipo_preco in ('POR_FASE', 'POR_SERVICO'));

update public.orcamentos
set tipo_preco = 'POR_FASE'
where tipo_preco is null;
