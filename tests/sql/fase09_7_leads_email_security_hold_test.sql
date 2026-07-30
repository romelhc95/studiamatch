\set ON_ERROR_STOP on

BEGIN;

CREATE FUNCTION pg_temp.assert_true(condition boolean, message text)
RETURNS void
LANGUAGE plpgsql
AS $function$
BEGIN
    IF condition IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.7 security hold assertion failed: %', message;
    END IF;
END;
$function$;

SET ROLE service_role;
SELECT public.verify_fase09_7_leads_email_security_hold() AS hold_verifier \gset
SELECT public.verify_fase09_7_public_access_closure() AS old_access_verifier \gset
SELECT public.verify_fase09_7_notify_new_lead_retirement() AS old_retirement_verifier \gset
RESET ROLE;

SELECT pg_catalog.count(*) AS postgres_lead_count FROM public.leads \gset
SELECT pg_catalog.count(*) AS postgres_email_count FROM public.email_log \gset
SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(leads) ORDER BY leads.id)::text, '[]'),
    'UTF8'
)), 'hex') AS postgres_leads_digest
FROM public.leads AS leads \gset
SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(email_log) ORDER BY email_log.id)::text, '[]'),
    'UTF8'
)), 'hex') AS postgres_email_log_digest
FROM public.email_log AS email_log \gset

SELECT pg_temp.assert_true(:'hold_verifier'::boolean, 'terminal verifier');
SELECT pg_temp.assert_true(
    NOT :'old_access_verifier'::boolean,
    'superseded public access verifier false'
);
SELECT pg_temp.assert_true(
    NOT :'old_retirement_verifier'::boolean,
    'superseded trigger retirement verifier false'
);
SELECT pg_temp.assert_true(:'postgres_lead_count'::integer = 1, 'existing lead row count');
SELECT pg_temp.assert_true(:'postgres_email_count'::integer = 1, 'existing email row count');
SELECT pg_temp.assert_true(pg_catalog.length(:'postgres_leads_digest') = 64, 'legacy lead digest');
SELECT pg_temp.assert_true(pg_catalog.length(:'postgres_email_log_digest') = 64, 'legacy email digest');

SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.count(*) = 0
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('leads', 'email_log')
    ),
    'no policies on held tables'
);
SELECT pg_temp.assert_true(
    pg_catalog.to_regprocedure('public.notify_new_lead()') IS NULL,
    'notify function absent'
);
SELECT pg_temp.assert_true(
    NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_record
        WHERE NOT trigger_record.tgisinternal
          AND trigger_record.tgname = 'trg_notify_new_lead'
    ),
    'notify trigger absent'
);

SELECT pg_temp.assert_true(
    (
        SELECT pg_catalog.count(*) = 2
        FROM pg_catalog.pg_constraint AS constraint_record
        WHERE (constraint_record.conrelid, constraint_record.conname) IN (
            (
                'public.leads'::pg_catalog.regclass,
                'chk_fase09_7_leads_security_hold_no_insert_update'
            ),
            (
                'public.email_log'::pg_catalog.regclass,
                'chk_fase09_7_email_log_security_hold_no_insert_update'
            )
        )
          AND constraint_record.contype = 'c'
          AND NOT constraint_record.convalidated
          AND pg_catalog.pg_get_constraintdef(constraint_record.oid, true) =
              'CHECK (false) NOT VALID'
    ),
    'not valid check false constraints'
);

SELECT pg_temp.assert_true(
    NOT EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'anon', 'authenticated', 'authenticator', 'service_role'
        ]::text[]) AS denied_role(role_name)
        CROSS JOIN pg_catalog.unnest(ARRAY[
            'public.leads', 'public.email_log'
        ]::text[]) AS held_table(table_name)
        CROSS JOIN pg_catalog.unnest(ARRAY[
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
            'REFERENCES', 'TRIGGER', 'MAINTAIN'
        ]::text[]) AS denied(privilege_name)
        WHERE pg_catalog.has_table_privilege(
            denied_role.role_name, held_table.table_name, denied.privilege_name
        )
    ),
    'application table privileges denied'
);

SELECT pg_temp.assert_true(
    NOT EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY['anon', 'authenticated', 'authenticator', 'service_role']::text[]) AS denied_role(role_name)
        CROSS JOIN pg_catalog.pg_attribute AS attribute
        WHERE attribute.attrelid = ANY(ARRAY[
            'public.leads', 'public.email_log'
        ]::pg_catalog.regclass[])
          AND attribute.attnum > 0
          AND NOT attribute.attisdropped
          AND (
              pg_catalog.has_column_privilege(
                  denied_role.role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              )
              OR pg_catalog.has_column_privilege(
                  denied_role.role_name, attribute.attrelid, attribute.attnum, 'INSERT'
              )
              OR pg_catalog.has_column_privilege(
                  denied_role.role_name, attribute.attrelid, attribute.attnum, 'UPDATE'
              )
              OR pg_catalog.has_column_privilege(
                  denied_role.role_name, attribute.attrelid, attribute.attnum, 'REFERENCES'
              )
          )
    ),
    'application column privileges denied'
);

SAVEPOINT denied_anon_select;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT email FROM public.leads LIMIT 1;
\set denied_anon_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_anon_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_anon_select_state' = '42501', 'anon select denied');

SAVEPOINT denied_auth_select;
\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT email FROM public.leads LIMIT 1;
\set denied_auth_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_auth_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_auth_select_state' = '42501', 'authenticated select denied');

SAVEPOINT denied_service_select;
\set ON_ERROR_STOP off
SET ROLE service_role;
SELECT email FROM public.leads LIMIT 1;
\set denied_service_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_service_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_service_select_state' = '42501', 'service_role select denied');

SAVEPOINT denied_authenticator_select;
\set ON_ERROR_STOP off
SET ROLE authenticator;
SELECT email FROM public.leads LIMIT 1;
\set denied_authenticator_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_authenticator_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_authenticator_select_state' = '42501', 'authenticator select denied');

SAVEPOINT denied_anon_email_select;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT recipient_email FROM public.email_log LIMIT 1;
\set denied_anon_email_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_anon_email_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_anon_email_select_state' = '42501', 'anon email_log select denied');

SAVEPOINT denied_auth_email_select;
\set ON_ERROR_STOP off
SET ROLE authenticated;
SELECT recipient_email FROM public.email_log LIMIT 1;
\set denied_auth_email_select_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_auth_email_select;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_auth_email_select_state' = '42501', 'authenticated email_log select denied');

SAVEPOINT denied_anon_insert;
\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.leads (first_name, email, whatsapp) VALUES (
    'Blocked', 'blocked-anon@example.test', '+51000000002'
);
\set denied_anon_insert_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_anon_insert;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_anon_insert_state' = '42501', 'anon insert denied');

SAVEPOINT denied_auth_insert;
\set ON_ERROR_STOP off
SET ROLE authenticated;
INSERT INTO public.leads (first_name, email, whatsapp) VALUES (
    'Blocked', 'blocked@example.test', '+51000000000'
);
\set denied_auth_insert_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_auth_insert;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_auth_insert_state' = '42501',
    'authenticated insert denied'
);

SAVEPOINT denied_anon_email_insert;
\set ON_ERROR_STOP off
SET ROLE anon;
INSERT INTO public.email_log (lead_id, recipient_type, recipient_email, status) VALUES (
    '94000000-0000-0000-0000-000000000001', 'audit', 'blocked-anon@example.test', 'pending'
);
\set denied_anon_email_insert_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_anon_email_insert;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_anon_email_insert_state' = '42501', 'anon email_log insert denied');

SAVEPOINT denied_auth_email_insert;
\set ON_ERROR_STOP off
SET ROLE authenticated;
INSERT INTO public.email_log (lead_id, recipient_type, recipient_email, status) VALUES (
    '94000000-0000-0000-0000-000000000001', 'audit', 'blocked-auth@example.test', 'pending'
);
\set denied_auth_email_insert_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_auth_email_insert;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(:'denied_auth_email_insert_state' = '42501', 'authenticated email_log insert denied');

SAVEPOINT service_insert_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
INSERT INTO public.leads (first_name, email, whatsapp) VALUES (
    'Blocked', 'blocked-service@example.test', '+51000000001'
);
\set service_insert_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_insert_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_insert_denied_state' = '42501',
    'service insert denied'
);

SAVEPOINT service_update_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
UPDATE public.leads SET first_name = 'Blocked';
\set service_update_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_update_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_update_denied_state' = '42501',
    'service update denied'
);

SAVEPOINT service_email_insert_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
INSERT INTO public.email_log (lead_id, recipient_type, recipient_email, status) VALUES (
    '94000000-0000-0000-0000-000000000001', 'audit', 'blocked-service@example.test', 'pending'
);
\set service_email_insert_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_email_insert_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_email_insert_denied_state' = '42501',
    'service email_log insert denied'
);

SAVEPOINT service_email_update_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
UPDATE public.email_log SET status = 'blocked';
\set service_email_update_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_email_update_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_email_update_denied_state' = '42501',
    'service email_log update denied'
);

SAVEPOINT service_delete_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
DELETE FROM public.leads;
\set service_delete_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_delete_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_delete_denied_state' = '42501',
    'service delete denied'
);

SAVEPOINT service_email_delete_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
DELETE FROM public.email_log;
\set service_email_delete_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_email_delete_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_email_delete_denied_state' = '42501',
    'service email_log delete denied'
);

SAVEPOINT service_truncate_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
TRUNCATE public.leads;
\set service_truncate_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_truncate_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_truncate_denied_state' = '42501',
    'service truncate denied'
);

SAVEPOINT service_email_truncate_denied;
\set ON_ERROR_STOP off
SET ROLE service_role;
TRUNCATE public.email_log;
\set service_email_truncate_denied_state :SQLSTATE
ROLLBACK TO SAVEPOINT service_email_truncate_denied;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'service_email_truncate_denied_state' = '42501',
    'service email_log truncate denied'
);

SAVEPOINT denied_terminal_verifier;
\set ON_ERROR_STOP off
SET ROLE anon;
SELECT public.verify_fase09_7_leads_email_security_hold();
\set denied_terminal_verifier_state :SQLSTATE
ROLLBACK TO SAVEPOINT denied_terminal_verifier;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT pg_temp.assert_true(
    :'denied_terminal_verifier_state' = '42501',
    'terminal verifier service-only'
);

ROLLBACK;
