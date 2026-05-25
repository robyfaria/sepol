#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Validando pré-requisitos..."
command -v supabase >/dev/null 2>&1 || {
  echo "Supabase CLI não encontrado. Instale com: npm i -g supabase"
  exit 2
}

: "${SUPABASE_ACCESS_TOKEN:?Missing SUPABASE_ACCESS_TOKEN}"
: "${SUPABASE_PROJECT_REF:?Missing SUPABASE_PROJECT_REF}"
: "${SUPABASE_DB_PASSWORD:?Missing SUPABASE_DB_PASSWORD}"

echo "[2/4] Autenticando CLI..."
supabase login --token "$SUPABASE_ACCESS_TOKEN"

echo "[3/4] Linkando projeto..."
supabase link --project-ref "$SUPABASE_PROJECT_REF" --password "$SUPABASE_DB_PASSWORD"

echo "[4/4] Executando db push..."
supabase db push

echo "OK: fluxo equivalente ao GitHub Action executado com sucesso."
