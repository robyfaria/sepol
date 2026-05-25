#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/test_supabase_action.sh [--check-only] [--skip-login]

Opções:
  --check-only  Apenas valida pré-requisitos (CLI + variáveis), sem executar comandos remotos.
  --skip-login  Pula `supabase login` (útil quando já autenticado no ambiente).
  -h, --help    Exibe esta ajuda.
USAGE
}

CHECK_ONLY=false
SKIP_LOGIN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=true
      shift
      ;;
    --skip-login)
      SKIP_LOGIN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opção inválida: $1"
      usage
      exit 1
      ;;
  esac
done

echo "[1/4] Validando pré-requisitos..."
command -v supabase >/dev/null 2>&1 || {
  echo "Supabase CLI não encontrado. Instale com: npm i -g supabase"
  exit 2
}

: "${SUPABASE_ACCESS_TOKEN:?Missing SUPABASE_ACCESS_TOKEN}"
: "${SUPABASE_PROJECT_REF:?Missing SUPABASE_PROJECT_REF}"
: "${SUPABASE_DB_PASSWORD:?Missing SUPABASE_DB_PASSWORD}"

echo "Pré-requisitos OK."

if [[ "$CHECK_ONLY" == true ]]; then
  echo "Modo --check-only: validação finalizada sem executar link/push."
  exit 0
fi

if [[ "$SKIP_LOGIN" == false ]]; then
  echo "[2/4] Autenticando CLI..."
  supabase login --token "$SUPABASE_ACCESS_TOKEN"
else
  echo "[2/4] Pulando login (--skip-login)."
fi

echo "[3/4] Linkando projeto..."
supabase link --project-ref "$SUPABASE_PROJECT_REF" --password "$SUPABASE_DB_PASSWORD"

echo "[4/4] Executando db push..."
supabase db push

echo "OK: fluxo equivalente ao GitHub Action executado com sucesso."
