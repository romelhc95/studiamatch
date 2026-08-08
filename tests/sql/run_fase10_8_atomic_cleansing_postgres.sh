#!/usr/bin/env bash
set -euo pipefail

if [ -z "${TEST_DATABASE_URL:-}" ]; then
  echo "TEST_DATABASE_URL is required" >&2
  exit 1
fi

if [ "${ALLOW_DESTRUCTIVE_LOCAL_TEST_DB:-}" != "F10_8_LOCAL_POSTGRES_ONLY" ]; then
  echo "ALLOW_DESTRUCTIVE_LOCAL_TEST_DB=F10_8_LOCAL_POSTGRES_ONLY is required" >&2
  exit 1
fi

case "$TEST_DATABASE_URL" in
  "postgresql://postgres:postgres@localhost:5432/studiamatch_f108") ;;
  "postgresql://postgres:postgres@127.0.0.1:5432/studiamatch_f108") ;;
  "postgresql://postgres:postgres@studiamatch-f108-postgres:5432/studiamatch_f108") ;;
  *)
    echo "TEST_DATABASE_URL must exactly target the local studiamatch_f108 test database" >&2
    exit 1
    ;;
esac

psql "$TEST_DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END $$;

CREATE TABLE public.staging_raw (
  id uuid PRIMARY KEY,
  institution_id uuid NOT NULL,
  url text NOT NULL,
  raw_html text,
  raw_name text,
  raw_description text,
  status text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE public.cleansed_programs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  staging_id uuid,
  institution_id uuid NOT NULL,
  url text NOT NULL UNIQUE,
  effective_url text,
  canonical_url text,
  clean_name text,
  clean_description text,
  modality text,
  location text,
  base_price numeric,
  currency text,
  status text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb
);
SQL

psql "$TEST_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql

psql "$TEST_DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO public.staging_raw (id, institution_id, url, status, metadata)
VALUES
  ('00000000-0000-0000-0000-000000000101', '10000000-0000-0000-0000-000000000001', 'https://example.edu/program-a', 'processing', '{}'::jsonb),
  ('00000000-0000-0000-0000-000000000102', '10000000-0000-0000-0000-000000000001', 'https://example.edu/program-b', 'pending', '{}'::jsonb);

INSERT INTO public.cleansed_programs (
  id, staging_id, institution_id, url, clean_name, clean_description,
  modality, location, base_price, currency, status, metadata
)
VALUES (
  '20000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  'https://example.edu/program-a',
  'Old name',
  'Old description',
  'old',
  'old',
  10,
  'PEN',
  'enriched',
  '{"historical":true,"f10_production_canary_run_id":"old-run"}'::jsonb
);

SELECT public.atomic_cleansing_promote(
  ARRAY[
    '00000000-0000-0000-0000-000000000101'::uuid,
    '00000000-0000-0000-0000-000000000102'::uuid
  ],
  '[
    {
      "staging_id":"00000000-0000-0000-0000-000000000101",
      "institution_id":"10000000-0000-0000-0000-000000000001",
      "url":"https://example.edu/program-a",
      "effective_url":"https://example.edu/program-a?canonical=1",
      "canonical_url":"https://example.edu/program-a",
      "clean_name":"New name",
      "clean_description":"New description",
      "modality":"online",
      "location":"Lima",
      "base_price":100,
      "currency":"PEN",
      "metadata":{"f10_production_canary_run_id":"new-run","raw_name":"New raw"}
    },
    {
      "staging_id":"00000000-0000-0000-0000-000000000102",
      "institution_id":"10000000-0000-0000-0000-000000000001",
      "url":"https://example.edu/program-b",
      "effective_url":"https://example.edu/program-b",
      "canonical_url":"https://example.edu/program-b",
      "clean_name":"Inserted name",
      "clean_description":"Inserted description",
      "modality":"presencial",
      "location":"Lima",
      "base_price":200,
      "currency":"PEN",
      "metadata":{"f10_production_canary_run_id":"new-run"}
    }
  ]'::jsonb
);

DO $$
DECLARE
  conflict_row public.cleansed_programs%ROWTYPE;
  inserted_row public.cleansed_programs%ROWTYPE;
BEGIN
  SELECT * INTO STRICT conflict_row
  FROM public.cleansed_programs
  WHERE url = 'https://example.edu/program-a';

  IF conflict_row.id != '20000000-0000-0000-0000-000000000001'::uuid THEN
    RAISE EXCEPTION 'conflict row id changed';
  END IF;
  IF conflict_row.status != 'pending' THEN
    RAISE EXCEPTION 'conflict row was not requeued';
  END IF;
  IF conflict_row.metadata->>'historical' != 'true' THEN
    RAISE EXCEPTION 'historical metadata was not preserved';
  END IF;
  IF conflict_row.metadata->>'f10_production_canary_run_id' != 'new-run' THEN
    RAISE EXCEPTION 'canary provenance marker was not refreshed';
  END IF;
  IF conflict_row.clean_name != 'New name' OR conflict_row.base_price != 100 THEN
    RAISE EXCEPTION 'conflict row fields were not refreshed';
  END IF;

  SELECT * INTO STRICT inserted_row
  FROM public.cleansed_programs
  WHERE url = 'https://example.edu/program-b';
  IF inserted_row.metadata->>'f10_production_canary_run_id' != 'new-run' THEN
    RAISE EXCEPTION 'inserted row provenance marker missing';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.staging_raw WHERE status != 'processed'
  ) THEN
    RAISE EXCEPTION 'staging rows were not processed from pending/processing';
  END IF;
END $$;

SELECT public.atomic_cleansing_promote(
  ARRAY['00000000-0000-0000-0000-000000000101'::uuid],
  '[{
    "staging_id":"00000000-0000-0000-0000-000000000101",
    "institution_id":"10000000-0000-0000-0000-000000000001",
    "url":"https://example.edu/program-a",
    "clean_name":"Second run",
    "clean_description":"Second description",
    "metadata":{"f10_production_canary_run_id":"new-run-2"}
  }]'::jsonb
);

DO $$
DECLARE
  metadata jsonb;
BEGIN
  SELECT cp.metadata INTO STRICT metadata
  FROM public.cleansed_programs AS cp
  WHERE cp.url = 'https://example.edu/program-a';
  IF metadata->>'historical' != 'true' THEN
    RAISE EXCEPTION 'idempotent run lost historical metadata';
  END IF;
  IF metadata->>'f10_production_canary_run_id' != 'new-run-2' THEN
    RAISE EXCEPTION 'idempotent run did not refresh provenance marker';
  END IF;
END $$;

DO $$
DECLARE
  anon_has boolean;
  authenticated_has boolean;
  service_has boolean;
  search_path_value text;
BEGIN
  SELECT has_function_privilege('anon', 'public.atomic_cleansing_promote(uuid[], jsonb)', 'EXECUTE') INTO anon_has;
  SELECT has_function_privilege('authenticated', 'public.atomic_cleansing_promote(uuid[], jsonb)', 'EXECUTE') INTO authenticated_has;
  SELECT has_function_privilege('service_role', 'public.atomic_cleansing_promote(uuid[], jsonb)', 'EXECUTE') INTO service_has;
  SELECT array_to_string(proconfig, ',') INTO search_path_value
  FROM pg_proc
  WHERE oid = 'public.atomic_cleansing_promote(uuid[], jsonb)'::regprocedure;

  IF anon_has OR authenticated_has THEN
    RAISE EXCEPTION 'unexpected anon/authenticated execute privilege';
  END IF;
  IF NOT service_has THEN
    RAISE EXCEPTION 'service_role execute privilege missing';
  END IF;
  IF search_path_value != 'search_path=pg_catalog' THEN
    RAISE EXCEPTION 'unexpected search_path: %', search_path_value;
  END IF;
END $$;
SQL
