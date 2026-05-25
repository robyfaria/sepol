-- Banco reiniciado do zero
-- Estrutura mínima inicial (placeholder)

CREATE TABLE IF NOT EXISTS healthcheck (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
