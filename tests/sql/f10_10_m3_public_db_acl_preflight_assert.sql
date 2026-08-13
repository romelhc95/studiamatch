WITH acl AS (
  SELECT d.datname, x.grantee, x.privilege_type
  FROM pg_catalog.pg_database AS d
  CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x
)
SELECT
  count(*) FILTER (WHERE datname='postgres' AND grantee=0 AND privilege_type='CONNECT') || '|' ||
  count(*) FILTER (WHERE datname='postgres' AND grantee=0 AND privilege_type IN ('TEMPORARY','CREATE')) || '|' ||
  count(*) FILTER (WHERE datname='other_nonconformant' AND grantee=0) || '|' ||
  count(*) FILTER (WHERE datname='other_conformant' AND grantee=0) || '|' ||
  count(*) FILTER (WHERE datname='nonconnectable_empty' AND grantee=0) || '|' ||
  count(*) FILTER (WHERE datname='nonconnectable_connect' AND grantee=0 AND privilege_type='CONNECT') || '|' ||
  count(*) FILTER (WHERE datname IN ('postgres','other_nonconformant') AND grantee=(SELECT oid FROM pg_roles WHERE rolname='explicit_reader'))
FROM acl;
