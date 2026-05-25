# SEPOL 2.0 (Recomeço do Zero)

Este repositório foi reiniciado do absoluto zero para construir um novo sistema:

- Responsivo, intuitivo e amigável para público 60+.
- Focado em criar orçamentos de forma rápida e simples.
- Fluxo obrigatório: **aprovar orçamento** antes de **vincular à obra**.
- Gestão flexível de obras com fases, serviços, alocação de pintores/terceiros,
  recebimentos, pagamentos e relatório financeiro de lucro.

## Estado atual

- Banco: zerado (novo esquema inicial em `db/schema.sql`).
- Aplicação: zerada (novo app base em `app/`).
- Repositório: histórico preservado no Git, mas código reiniciado.

## Próximos passos

1. Definir protótipo de UX 60+ (tipografia, contraste, fluxo guiado).
2. Implementar módulo de orçamento em fluxo de 3 passos.
3. Implementar aprovação e trava de edição.
4. Implementar vínculo com obra e gestão de fases/serviços.
5. Implementar financeiro (receitas, custos, lucro por obra e consolidado).


## Testar fluxo do Supabase Action localmente

1. Instale o Supabase CLI:
   - `npm i -g supabase`
2. Exporte os segredos usados no workflow:
   - `export SUPABASE_ACCESS_TOKEN=...`
   - `export SUPABASE_PROJECT_REF=...`
   - `export SUPABASE_DB_PASSWORD=...`
3. Rode apenas validação (sem alterar remoto):
   - `./scripts/test_supabase_action.sh --check-only`
4. Rode o fluxo completo (link + push):
   - `./scripts/test_supabase_action.sh`

Dica: se o ambiente já estiver autenticado no CLI, use `--skip-login`.
