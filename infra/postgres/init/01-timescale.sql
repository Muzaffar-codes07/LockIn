-- Loaded once on container init via /docker-entrypoint-initdb.d.
-- Idempotent so re-init or post-restore is safe.
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
-- gen_random_uuid() is core in PG13+; no pgcrypto required.
