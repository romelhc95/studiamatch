-- H2 Pro security remediation: protect the private compatibility cohort.
-- Scope: Production DDL only after explicit JIT, backup/PITR and manifest approval.
-- The table remains private and has no public grants or policies.

ALTER TABLE private.h2_legacy_public_course_cohort ENABLE ROW LEVEL SECURITY;
