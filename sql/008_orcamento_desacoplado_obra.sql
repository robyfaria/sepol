-- Migração incremental: desacoplar orçamento de obra e inverter vínculo
-- Objetivo:
-- 1) orçamento deixa de depender de obra
-- 2) obra passa a poder vincular um orçamento aprovado
-- 3) manter compatibilidade com dados legados

begin;

-- 1) Preparar orçamentos para existir sem obra
alter table public.orcamentos
  alter column obra_id drop not null;

-- remover unicidade de versão por obra e trocar para cliente
alter table public.orcamentos
  add column if not exists cliente_id bigint references public.clientes(id) on update cascade on delete restrict;

update public.orcamentos o
set cliente_id = ob.cliente_id
from public.obras ob
where o.obra_id = ob.id
  and o.cliente_id is null;

alter table public.orcamentos
  alter column cliente_id set not null;

alter table public.orcamentos
  drop constraint if exists orcamentos_obra_id_versao_key;

-- normalizar versões por cliente para evitar colisões legadas em (cliente_id, versao)
with versoes_normalizadas as (
  select
    o.id,
    row_number() over (
      partition by o.cliente_id
      order by
        coalesce(o.aprovado_em, o.criado_em) asc,
        o.id asc
    ) as nova_versao
  from public.orcamentos o
)
update public.orcamentos o
set versao = vn.nova_versao
from versoes_normalizadas vn
where o.id = vn.id
  and o.versao is distinct from vn.nova_versao;

alter table public.orcamentos
  add constraint orcamentos_cliente_id_versao_key unique (cliente_id, versao);

-- remover índice legado de aprovado por obra
DROP INDEX IF EXISTS public.ux_orcamento_aprovado_por_obra;

-- 2) obra passa a apontar para orçamento aprovado
alter table public.obras
  add column if not exists orcamento_id bigint references public.orcamentos(id) on update cascade on delete set null;

-- migrar vínculo atual: se há aprovado para a obra, vincula
update public.obras ob
set orcamento_id = ap.id
from (
  select distinct on (obra_id) id, obra_id
  from public.orcamentos
  where status = 'APROVADO' and obra_id is not null
  order by obra_id, aprovado_em desc nulls last, id desc
) ap
where ob.id = ap.obra_id
  and ob.orcamento_id is null;

create index if not exists idx_obras_orcamento on public.obras(orcamento_id);
create index if not exists idx_orcamentos_cliente on public.orcamentos(cliente_id);

-- 3) Trigger de integridade: obra só pode vincular orçamento aprovado e do mesmo cliente
create or replace function public.fn_validar_vinculo_obra_orcamento()
returns trigger
language plpgsql
as $$
declare
  v_status text;
  v_cliente_id bigint;
begin
  if new.orcamento_id is null then
    return new;
  end if;

  select status, cliente_id
    into v_status, v_cliente_id
  from public.orcamentos
  where id = new.orcamento_id;

  if v_status is null then
    raise exception 'Orçamento % não encontrado.', new.orcamento_id;
  end if;

  if v_status <> 'APROVADO' then
    raise exception 'Somente orçamento APROVADO pode ser vinculado à obra. Status atual: %', v_status;
  end if;

  if new.cliente_id is distinct from v_cliente_id then
    raise exception 'Cliente da obra (%) difere do cliente do orçamento (%).', new.cliente_id, v_cliente_id;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_validar_vinculo_obra_orcamento on public.obras;
create trigger trg_validar_vinculo_obra_orcamento
before insert or update of orcamento_id, cliente_id
on public.obras
for each row
execute function public.fn_validar_vinculo_obra_orcamento();

commit;
