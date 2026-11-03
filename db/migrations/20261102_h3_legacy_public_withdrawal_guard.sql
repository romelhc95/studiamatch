-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal
-- H3: explicit editorial withdrawal removes a legacy-only course from the
-- compatibility cohort without deleting the cohort, course, snapshot, or audit.
-- A later publication remains visible through the strict published-snapshot path.
-- Forward-only and idempotent; no operational rows are updated.
DO $$
BEGIN
  IF to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
    EXECUTE $view$
      CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort AS
      SELECT cohort.course_id
        FROM private.h2_legacy_public_course_cohort AS cohort
       WHERE NOT EXISTS (
         SELECT 1
           FROM public.course_editorial_audit AS editorial_event
          WHERE editorial_event.course_id = cohort.course_id
            AND editorial_event.action IN ('unpublish', 'archive')
       )
    $view$;
  ELSE
    EXECUTE $view$
      CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort AS
      SELECT NULL::UUID AS course_id WHERE false
    $view$;
  END IF;
END;
$$;

REVOKE ALL ON TABLE private.h3_legacy_public_course_cohort
  FROM PUBLIC, anon, authenticated, service_role;

COMMENT ON VIEW private.h3_legacy_public_course_cohort IS
  'H3 compatibility projection: legacy cohort remains visible unless append-only editorial audit records an explicit unpublish or archive; published snapshots remain handled by the strict public reader.';
