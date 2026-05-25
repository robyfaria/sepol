-- Suporte a edição de orçamento emitido, desconto e previsão na obra

alter table if exists orcamentos
  add column if not exists desconto_tipo text not null default 'valor' check (desconto_tipo in ('valor','percentual')),
  add column if not exists desconto_valor numeric(14,2) not null default 0,
  add column if not exists subtotal_mao_obra numeric(14,2) not null default 0;

alter table if exists obras
  add column if not exists previsao_inicio date,
  add column if not exists previsao_termino date;
