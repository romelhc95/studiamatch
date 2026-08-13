#!/usr/bin/env python3
"""Private, offline F10.10/M3 PUBLIC database ACL preflight.

The CLI can only print the read-only collector SQL or validate a synthetic/private
collector result.  Candidate SQL is deliberately available only as a pure Python
function so this module cannot publish an executable remote payload.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = ROOT / "local/f10_10/m3"
RESULT_SCHEMA = "f10.10-m3-public-db-acl-private-result-v1"
PRIVATE_SCHEMA = "f10.10-m3-public-db-acl-private-artifact-v1"
MANIFEST_SCHEMA = "f10.10-m3-public-db-acl-sanitized-manifest-v1"
CANDIDATE_SCHEMA = "f10.10-m3-public-db-acl-remediation-candidate-v1"
TARGET_ALIAS = "FREE_DB"
READER_ROLE = "studiamatch_m3_reader"
MAX_PRIVATE_BYTES = 4 * 1024 * 1024
PRIVILEGES = frozenset({"CONNECT", "TEMPORARY", "CREATE"})
CLASSES = ("TARGET", "OTHER_CONNECTABLE", "NON_CONNECTABLE")
APPLY_MIGRATION_ONLY = True
EXECUTE_SQL_FALLBACK_ALLOWED = False
TARGET_BINDING_DOMAIN = "physical-target-binding-v1"
EXECUTOR_DOMAIN = "database-executor-v1"
MANAGED_SERVICES = frozenset({
    "auth", "storage", "realtime", "postgrest", "studio_meta", "supavisor",
})


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def domain_digest(domain: str, value: Any) -> str:
    encoded = canonical_json({"domain": domain, "version": 1, "payload": value})
    digest = hashlib.sha256()
    digest.update(b"f10.10-m3-public-db-acl\0")
    digest.update(domain.encode("ascii"))
    digest.update(b"\0")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)
    return "sha256:" + digest.hexdigest()


# One repeatable-read/read-only transaction.  It reads only pg_catalog objects;
# pg_stat_activity is intentionally aggregated and never projects query text.
COLLECTOR_SQL = r"""BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL search_path = pg_catalog;
SET LOCAL statement_timeout = '30s';
SET LOCAL lock_timeout = '5s';
WITH db AS MATERIALIZED (
  SELECT d.oid, d.datname::text, d.datallowconn, d.datistemplate, d.datdba,
         owner.rolname::text AS owner_name, d.datacl,
         pg_catalog.encode(pg_catalog.sha256(
           pg_catalog.convert_to('database-owner-v1', 'UTF8')
           || pg_catalog.decode('00', 'hex')
           || pg_catalog.convert_to(d.datdba::text, 'UTF8')
           || pg_catalog.decode('00', 'hex')
           || pg_catalog.convert_to(owner.rolname::text, 'UTF8')
         ), 'hex') AS owner_domain_fingerprint
  FROM pg_catalog.pg_database AS d
  JOIN pg_catalog.pg_roles AS owner ON owner.oid = d.datdba
), acl AS MATERIALIZED (
  SELECT d.oid AS database_oid, x.grantee, grantee.rolname::text AS grantee_name,
         x.grantor, grantor.rolname::text AS grantor_name,
         x.privilege_type, x.is_grantable
  FROM db AS d
  CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x
  LEFT JOIN pg_catalog.pg_roles AS grantee ON grantee.oid = x.grantee
  LEFT JOIN pg_catalog.pg_roles AS grantor ON grantor.oid = x.grantor
), sessions AS MATERIALIZED (
  SELECT a.datid AS database_oid, a.usesysid AS role_oid, count(*)::integer AS session_count
  FROM pg_catalog.pg_stat_activity AS a
  WHERE a.datid IS NOT NULL AND a.usesysid IS NOT NULL
  GROUP BY a.datid, a.usesysid
), login_public_dependencies AS MATERIALIZED (
  SELECT d.oid AS database_oid, r.oid AS role_oid, p.privilege
  FROM db AS d
  CROSS JOIN pg_catalog.pg_roles AS r
  CROSS JOIN (VALUES ('CONNECT'::text), ('TEMPORARY'::text), ('CREATE'::text)) AS p(privilege)
  WHERE r.rolcanlogin
    AND pg_catalog.has_database_privilege(r.oid, d.oid, p.privilege)
    AND r.oid <> d.datdba
    AND EXISTS (SELECT 1 FROM acl AS a WHERE a.database_oid = d.oid
      AND a.grantee = 0 AND a.privilege_type = p.privilege)
), db_after AS MATERIALIZED (
  SELECT d.oid, d.datname::text, d.datallowconn, d.datistemplate, d.datdba, d.datacl::text AS datacl_text
  FROM pg_catalog.pg_database AS d
), payload AS (
  SELECT pg_catalog.jsonb_build_object(
    'schema', 'f10.10-m3-public-db-acl-private-result-v1',
    'target_alias', 'FREE_DB',
    'postgres_version_num', pg_catalog.current_setting('server_version_num')::integer,
    'current_database', pg_catalog.current_database(),
    'current_user', current_user::text,
    'session_user', session_user::text,
    'in_recovery', pg_catalog.pg_is_in_recovery(),
    'transaction_read_only', pg_catalog.current_setting('transaction_read_only'),
    'transaction_isolation', pg_catalog.current_setting('transaction_isolation'),
    'reader_present', EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'studiamatch_m3_reader'),
    'target_binding', NULL,
    'executor', pg_catalog.jsonb_build_object(
      'oid', (SELECT oid::bigint FROM pg_catalog.pg_roles WHERE rolname = current_user),
      'name', current_user::text,
      'domain_fingerprint', pg_catalog.encode(pg_catalog.sha256(
        pg_catalog.convert_to('database-executor-v1', 'UTF8') || pg_catalog.decode('00', 'hex') ||
        pg_catalog.convert_to((SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname = current_user), 'UTF8') ||
        pg_catalog.decode('00', 'hex') || pg_catalog.convert_to(current_user::text, 'UTF8')), 'hex'),
      'is_superuser', (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user),
      'can_revoke_all_observed', NOT EXISTS (SELECT 1 FROM db WHERE datdba <>
        (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_user))
        OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user)),
    'databases', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'name', d.datname, 'oid', d.oid::bigint, 'allowconn', d.datallowconn,
      'istemplate', d.datistemplate, 'owner_oid', d.datdba::bigint,
      'owner_name', d.owner_name, 'owner_domain_fingerprint', d.owner_domain_fingerprint,
      'owner_managed', (d.datdba = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_user)
        OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user)),
      'datacl_is_null', d.datacl IS NULL, 'datacl_text', d.datacl::text,
      'effective_acl', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
        'grantee_oid', a.grantee::bigint, 'grantee_name', CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE a.grantee_name END,
        'grantor_oid', a.grantor::bigint, 'grantor_name', a.grantor_name,
        'privilege', a.privilege_type, 'is_grantable', a.is_grantable,
        'grantor_managed', (a.grantor = d.datdba AND (d.datdba =
          (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_user)
          OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user))))
        ORDER BY a.grantee, a.grantor, a.privilege_type) FROM acl AS a WHERE a.database_oid = d.oid)
      ) ORDER BY d.oid) FROM db AS d),
    'sessions', (SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'database_oid', s.database_oid::bigint, 'role_oid', s.role_oid::bigint, 'count', s.session_count)
      ORDER BY s.database_oid, s.role_oid), '[]'::pg_catalog.jsonb) FROM sessions AS s),
    'login_public_dependencies', (SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
       'database_oid', l.database_oid::bigint, 'role_oid', l.role_oid::bigint, 'privilege', l.privilege)
       ORDER BY l.database_oid, l.role_oid, l.privilege),
       '[]'::pg_catalog.jsonb) FROM login_public_dependencies AS l),
    'managed_service_evaluation', NULL,
    'topology_digest_before', (SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
      pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid, d.datname, d.datallowconn,
        d.datistemplate, d.datdba, d.datacl::text) ORDER BY d.oid)::text, 'UTF8')), 'hex') FROM db AS d),
    'topology_digest_after', (SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
      pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid, d.datname, d.datallowconn,
        d.datistemplate, d.datdba, d.datacl_text) ORDER BY d.oid)::text, 'UTF8')), 'hex') FROM db_after AS d)
  ) AS value
)
SELECT value FROM payload;
COMMIT;"""


class PreflightError(ValueError):
    """Stable fail-closed error; private values never belong in its message."""


@dataclass(frozen=True)
class ValidatedSnapshot:
    private: dict[str, Any]
    manifest: dict[str, Any]
    snapshot_digest: str
    expected_target_binding_digest: str


def _sha256_digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _executor_fingerprint(oid: int, name: str) -> str:
    raw = f"{EXECUTOR_DOMAIN}\0{oid}\0{name}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _target_binding_core(project_ref_fingerprint: str, host_fingerprint: str) -> dict[str, str]:
    return {
        "alias": TARGET_ALIAS,
        "environment": "free",
        "project_ref_fingerprint": project_ref_fingerprint,
        "host_fingerprint": host_fingerprint,
    }


def build_target_attestation(project_ref_fingerprint: str, host_fingerprint: str) -> dict[str, str]:
    """Build a private physical-target envelope from already-redacted fingerprints."""
    core = _target_binding_core(project_ref_fingerprint, host_fingerprint)
    if not all(_sha256_digest(value) for value in (project_ref_fingerprint, host_fingerprint)):
        _stop("STOP_TARGET_BINDING")
    return {**core, "binding_digest": domain_digest(TARGET_BINDING_DOMAIN, core)}


def bind_private_attestations(
    collected: Any,
    target_attestation: Any,
    managed_evaluation: Any,
) -> dict[str, Any]:
    """Combine independent private inputs; this is not a remote attestation."""
    if not isinstance(collected, dict):
        _stop("STOP_PRIVATE_SCHEMA")
    result = copy.deepcopy(collected)
    if result.get("target_binding") is not None or result.get("managed_service_evaluation") is not None:
        _stop("STOP_ATTESTATION_ALREADY_BOUND")
    result["target_binding"] = copy.deepcopy(target_attestation)
    result["managed_service_evaluation"] = copy.deepcopy(managed_evaluation)
    return result


def _stop(reason: str) -> None:
    raise PreflightError(reason)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _fingerprint(owner_oid: int, owner_name: str) -> str:
    raw = f"database-owner-v1\0{owner_oid}\0{owner_name}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _acl_payload(entry: dict[str, Any]) -> list[Any]:
    return [entry[key] for key in (
        "grantee_oid", "grantee_name", "grantor_oid", "grantor_name",
        "privilege", "is_grantable",
    )]


def _database_class(database: dict[str, Any]) -> str:
    if database["name"] == "postgres":
        return "TARGET"
    return "OTHER_CONNECTABLE" if database["allowconn"] else "NON_CONNECTABLE"


def _snapshot_payload(databases: list[dict[str, Any]]) -> list[Any]:
    return [[
        db["oid"], db["name"], db["allowconn"], db["istemplate"],
        db["owner_oid"], db["owner_name"], db["datacl_is_null"],
        db["datacl_text"], [_acl_payload(a) for a in db["effective_acl"]],
    ] for db in databases]


def validate_private_result(value: Any, expected_target_binding_digest: str) -> ValidatedSnapshot:
    if not _sha256_digest(expected_target_binding_digest):
        _stop("STOP_EXPECTED_TARGET_BINDING_REQUIRED")
    if not isinstance(value, dict) or value.get("schema") != RESULT_SCHEMA:
        _stop("STOP_PRIVATE_SCHEMA")
    required = {
        "schema", "target_alias", "postgres_version_num", "current_database",
        "current_user", "session_user", "in_recovery", "transaction_read_only",
        "transaction_isolation", "reader_present", "executor", "databases",
        "sessions", "login_public_dependencies", "managed_service_evaluation",
        "target_binding", "topology_digest_before", "topology_digest_after",
    }
    if set(value) != required:
        _stop("STOP_PRIVATE_SCHEMA")
    if not _is_int(value["postgres_version_num"]):
        _stop("STOP_PRIVATE_SCHEMA")
    if not (170000 <= value["postgres_version_num"] <= 179999):
        _stop("STOP_POSTGRES_VERSION")
    if value["target_alias"] != TARGET_ALIAS or value["current_database"] != "postgres":
        _stop("STOP_TARGET_BINDING")
    if (
        not isinstance(value["current_user"], str)
        or value["current_user"] != value["session_user"]
    ):
        _stop("STOP_EXECUTOR_IDENTITY")
    if value["in_recovery"] is not False:
        _stop("STOP_RECOVERY")
    if value["transaction_read_only"] != "on" or value["transaction_isolation"] != "repeatable read":
        _stop("STOP_READONLY_CONTRACT")
    if value["reader_present"] is not False:
        _stop("STOP_READER_PRESENT")
    target = value["target_binding"]
    if not isinstance(target, dict) or set(target) != {
        "alias", "environment", "project_ref_fingerprint", "host_fingerprint", "binding_digest",
    }:
        _stop("STOP_TARGET_BINDING")
    target_core = _target_binding_core(
        target.get("project_ref_fingerprint"), target.get("host_fingerprint")
    )
    if (
        target.get("alias") != TARGET_ALIAS or target.get("environment") != "free"
        or not _sha256_digest(target.get("project_ref_fingerprint"))
        or not _sha256_digest(target.get("host_fingerprint"))
        or not _sha256_digest(target.get("binding_digest"))
        or not hmac.compare_digest(target["binding_digest"], domain_digest(TARGET_BINDING_DOMAIN, target_core))
        or not hmac.compare_digest(target["binding_digest"], expected_target_binding_digest)
    ):
        _stop("STOP_TARGET_BINDING")
    executor = value["executor"]
    if not isinstance(executor, dict) or set(executor) != {
        "oid", "name", "domain_fingerprint", "is_superuser", "can_revoke_all_observed",
    }:
        _stop("STOP_PRIVATE_SCHEMA")
    if (
        not _is_int(executor["oid"]) or executor["oid"] == 0
        or not isinstance(executor["name"], str) or not executor["name"]
        or executor["name"] != value["current_user"]
        or not isinstance(executor["is_superuser"], bool)
        or not isinstance(executor["can_revoke_all_observed"], bool)
        or not isinstance(executor["domain_fingerprint"], str)
        or not hmac.compare_digest(
            executor["domain_fingerprint"], _executor_fingerprint(executor["oid"], executor["name"])
        )
    ):
        _stop("STOP_EXECUTOR_IDENTITY")
    if executor["can_revoke_all_observed"] is not True:
        _stop("STOP_EXECUTOR_AUTHORITY")

    databases = value["databases"]
    if not isinstance(databases, list) or not databases:
        _stop("STOP_TOPOLOGY")
    names: set[str] = set()
    oids: set[int] = set()
    role_identity: dict[int, str] = {}
    unexpected_owner_grantor = 0
    grant_options = 0
    counts = {name: 0 for name in CLASSES}
    for db in databases:
        expected_db = {
            "name", "oid", "allowconn", "istemplate", "owner_oid", "owner_name",
            "owner_domain_fingerprint", "datacl_is_null", "datacl_text", "effective_acl",
            "owner_managed",
        }
        if not isinstance(db, dict) or set(db) != expected_db:
            _stop("STOP_PRIVATE_SCHEMA")
        if (
            not isinstance(db["name"], str) or not db["name"]
            or not _is_int(db["oid"]) or db["oid"] in oids or db["name"] in names
            or not isinstance(db["allowconn"], bool) or not isinstance(db["istemplate"], bool)
            or not _is_int(db["owner_oid"]) or not isinstance(db["owner_name"], str)
            or not isinstance(db["datacl_is_null"], bool)
            or (db["datacl_text"] is not None and not isinstance(db["datacl_text"], str))
            or db["datacl_is_null"] != (db["datacl_text"] is None)
            or not isinstance(db["effective_acl"], list)
        ):
            _stop("STOP_TOPOLOGY")
        if not hmac.compare_digest(db["owner_domain_fingerprint"], _fingerprint(db["owner_oid"], db["owner_name"])):
            _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
        if db["owner_managed"] is not True:
            unexpected_owner_grantor += 1
        prior = role_identity.setdefault(db["owner_oid"], db["owner_name"])
        if prior != db["owner_name"]:
            _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
        names.add(db["name"])
        oids.add(db["oid"])
        classification = _database_class(db)
        counts[classification] += 1
        seen_acl: set[tuple[Any, ...]] = set()
        public_privileges: set[str] = set()
        for acl in db["effective_acl"]:
            expected_acl = {
                "grantee_oid", "grantee_name", "grantor_oid", "grantor_name",
                "privilege", "is_grantable", "grantor_managed",
            }
            if not isinstance(acl, dict) or set(acl) != expected_acl:
                _stop("STOP_PRIVATE_SCHEMA")
            if (
                not _is_int(acl["grantee_oid"]) or not _is_int(acl["grantor_oid"])
                or not isinstance(acl["grantee_name"], str)
                or not isinstance(acl["grantor_name"], str)
                or acl["privilege"] not in PRIVILEGES
                or not isinstance(acl["is_grantable"], bool)
            ):
                _stop("STOP_ACL_SHAPE")
            if acl["grantee_oid"] == 0 and acl["grantee_name"] != "PUBLIC":
                _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
            if acl["grantee_oid"] != 0 and acl["grantee_name"] == "PUBLIC":
                _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
            identity = role_identity.setdefault(acl["grantor_oid"], acl["grantor_name"])
            if identity != acl["grantor_name"]:
                _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
            key = tuple(_acl_payload(acl))
            if key in seen_acl:
                _stop("STOP_ACL_SHAPE")
            seen_acl.add(key)
            grant_options += int(acl["is_grantable"])
            if acl["grantee_oid"] == 0:
                public_privileges.add(acl["privilege"])
                classification_for_acl = _database_class(db)
                removable_acl = (
                    acl["privilege"] in {"TEMPORARY", "CREATE"}
                    if classification_for_acl == "TARGET"
                    else classification_for_acl == "OTHER_CONNECTABLE"
                )
                if removable_acl:
                    if acl["grantor_managed"] is not True:
                        unexpected_owner_grantor += 1
                    if (
                        acl["grantor_oid"] != db["owner_oid"]
                        or not (executor["is_superuser"] is True or executor["oid"] == db["owner_oid"])
                    ):
                        _stop("STOP_EXECUTOR_AUTHORITY")
        if classification == "TARGET":
            if not db["allowconn"] or "CONNECT" not in public_privileges:
                _stop("STOP_TARGET_CONNECT")
        elif classification == "NON_CONNECTABLE" and public_privileges & {"TEMPORARY", "CREATE"}:
            _stop("STOP_NONCONNECTABLE_MUTATION")

    if counts["TARGET"] != 1:
        _stop("STOP_TARGET_COUNT")
    if grant_options:
        _stop("STOP_GRANT_OPTION")
    if unexpected_owner_grantor:
        _stop("STOP_OWNER_GRANTOR_AMBIGUITY")
    snapshot_payload = _snapshot_payload(databases)
    topology_digest = domain_digest("topology-v1", snapshot_payload)
    if (
        value["topology_digest_before"] != value["topology_digest_after"]
        or not isinstance(value["topology_digest_before"], str)
        or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", value["topology_digest_before"])
    ):
        _stop("STOP_TOPOLOGY_DRIFT")

    for session in value["sessions"]:
        if not isinstance(session, dict) or set(session) != {"database_oid", "role_oid", "count"}:
            _stop("STOP_PRIVATE_SCHEMA")
        if session["database_oid"] not in oids or not _is_int(session["role_oid"]) or not _is_int(session["count"]):
            _stop("STOP_SESSION_SHAPE")

    dependencies = value["login_public_dependencies"]
    if not isinstance(dependencies, list):
        _stop("STOP_PRIVATE_SCHEMA")
    dependency_keys: set[tuple[int, int, str]] = set()
    for dependency in dependencies:
        if not isinstance(dependency, dict) or set(dependency) != {"database_oid", "role_oid", "privilege"}:
            _stop("STOP_PRIVATE_SCHEMA")
        if (
            dependency["database_oid"] not in oids or not _is_int(dependency["role_oid"])
            or dependency["role_oid"] == 0 or dependency["privilege"] not in PRIVILEGES
        ):
            _stop("STOP_DEPENDENCY_SHAPE")
        key = (dependency["database_oid"], dependency["role_oid"], dependency["privilege"])
        if key in dependency_keys:
            _stop("STOP_DEPENDENCY_SHAPE")
        dependency_keys.add(key)
    managed = value["managed_service_evaluation"]
    if not isinstance(managed, dict) or set(managed) != {"schema", "entries"}:
        _stop("STOP_PRIVATE_SCHEMA")
    if managed["schema"] != "f10.10-m3-managed-dependency-attestation-v1" or not isinstance(managed["entries"], list):
        _stop("STOP_MANAGED_SERVICE_EVALUATION")
    evaluation_keys: set[tuple[int, int, str]] = set()
    evaluated_dependencies: list[dict[str, Any]] = []
    for entry in managed["entries"]:
        expected_entry = {
            "database_oid", "role_oid", "privilege", "service", "source_grantee_oid",
            "source_grantor_oid", "source_is_grantable", "membership",
        }
        if not isinstance(entry, dict) or set(entry) != expected_entry:
            _stop("STOP_MANAGED_SERVICE_EVALUATION")
        key = (entry.get("database_oid"), entry.get("role_oid"), entry.get("privilege"))
        if (
            key not in dependency_keys or key in evaluation_keys
            or entry.get("service") not in MANAGED_SERVICES
            or not _is_int(entry.get("source_grantee_oid")) or entry["source_grantee_oid"] == 0
            or not _is_int(entry.get("source_grantor_oid")) or entry["source_grantor_oid"] == 0
            or not isinstance(entry.get("source_is_grantable"), bool)
            or entry.get("membership") != "USAGE"
        ):
            _stop("STOP_MANAGED_SERVICE_EVALUATION")
        database = next(db for db in databases if db["oid"] == entry["database_oid"])
        if not any(
            acl["grantee_oid"] == entry["source_grantee_oid"]
            and acl["grantor_oid"] == entry["source_grantor_oid"]
            and acl["privilege"] == entry["privilege"]
            and acl["is_grantable"] is entry["source_is_grantable"]
            for acl in database["effective_acl"]
        ):
            _stop("STOP_UNRESOLVED_MANAGED_DEPENDENCY")
        evaluation_keys.add(key)
        evaluated_dependencies.append(entry)
    if evaluation_keys != dependency_keys:
        _stop("STOP_UNRESOLVED_MANAGED_DEPENDENCY")
    unresolved = 0

    snapshot_digest = domain_digest("private-snapshot-v1", value)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "decision": "PASS_OFFLINE_CANDIDATE_ELIGIBLE",
        "reasons": [],
        "unexpected_owner_grantor_count": unexpected_owner_grantor,
        "unresolved_managed_dependencies_count": unresolved,
        "grant_option_count": grant_options,
        "flags": {
            "engine_major_17": True, "target_connect_preserved": True,
            "reader_absent": True, "stable_topology": True,
            "executor_authorized": True, "managed_service_evaluated": True,
            "apply_migration_only": APPLY_MIGRATION_ONLY,
            "execute_sql_fallback_allowed": EXECUTE_SQL_FALLBACK_ALLOWED,
        },
        "digests": {
            "target_binding": target["binding_digest"],
            "executor": "sha256:" + executor["domain_fingerprint"],
            "collector_sql": domain_digest("collector-sql-v1", COLLECTOR_SQL),
        },
    }
    private = {
        "schema": PRIVATE_SCHEMA, "snapshot_digest": snapshot_digest,
        "target_binding_digest": target["binding_digest"], "result": value,
    }
    return ValidatedSnapshot(private, manifest, snapshot_digest, expected_target_binding_digest)


def _quote_literal(value: str) -> str:
    if "\x00" in value:
        _stop("STOP_UNSAFE_IDENTIFIER")
    return "'" + value.replace("'", "''") + "'"


def _quote_identifier(value: str) -> str:
    if not value or "\x00" in value:
        _stop("STOP_UNSAFE_IDENTIFIER")
    return '"' + value.replace('"', '""') + '"'


FORBIDDEN_SQL = (
    re.compile(r"\bREVOKE\s+ALL\b", re.I), re.compile(r"\bGRANT\b", re.I),
    re.compile(r"\bCASCADE\b", re.I),
    re.compile(r"\b(?:ALTER|CREATE|DROP)\s+DATABASE\b", re.I),
    re.compile(r"\b(?:ALTER|CREATE|DROP)\s+ROLE\b", re.I),
    re.compile(r"\b(?:SCHEMA|TABLE|POLICY|TRIGGER)\b", re.I),
    re.compile(r"\b(?:INSERT|UPDATE|DELETE|TRUNCATE|MERGE)\b", re.I),
    re.compile(r"REVOKE\s+CONNECT\s+ON\s+DATABASE\s+\"postgres\"", re.I),
)


def assert_candidate_sql_contract(sql: str) -> None:
    for forbidden in FORBIDDEN_SQL:
        if forbidden.search(sql):
            _stop("STOP_FORBIDDEN_SQL")
    if not sql.startswith("BEGIN;\n") or not sql.endswith("COMMIT;\n"):
        _stop("STOP_TRANSACTION_ENVELOPE")
    scrubbed = re.sub(r"DO \$f1010_[a-z]+\$.*?\$f1010_[a-z]+\$;", "", sql, flags=re.I | re.S)
    allowed_line = re.compile(
        r"^(?:BEGIN;|COMMIT;|SET LOCAL (?:search_path|lock_timeout|statement_timeout) = .+;|"
        r"SELECT pg_catalog\.pg_advisory_xact_lock\([0-9]+, [0-9]+\);|"
        r"REVOKE (?:CONNECT|TEMPORARY|CREATE)(?:, (?:CONNECT|TEMPORARY|CREATE))* "
        r"ON DATABASE \"(?:[^\"]|\"\")+\" FROM PUBLIC RESTRICT;)?$"
    )
    if any(not allowed_line.fullmatch(line) for line in scrubbed.splitlines()):
        _stop("STOP_SQL_SURFACE")


def generate_candidate_sql(validated: ValidatedSnapshot) -> str:
    """Return a deterministic candidate; callers must keep it private."""
    if not isinstance(validated, ValidatedSnapshot) or not _sha256_digest(
        validated.expected_target_binding_digest
    ):
        _stop("STOP_SNAPSHOT_BINDING")
    result = validated.private["result"]
    # Re-validation makes forged/mutated dataclass contents fail closed.
    checked = validate_private_result(result, validated.expected_target_binding_digest)
    if not hmac.compare_digest(checked.snapshot_digest, validated.snapshot_digest):
        _stop("STOP_SNAPSHOT_BINDING")
    if (
        not hmac.compare_digest(
            checked.private["target_binding_digest"], validated.expected_target_binding_digest
        )
        or not hmac.compare_digest(
            validated.private.get("target_binding_digest", ""),
            validated.expected_target_binding_digest,
        )
    ):
        _stop("STOP_TARGET_BINDING")
    databases = result["databases"]
    executor = result["executor"]
    preconditions: list[str] = []
    postconditions: list[str] = []
    revokes: list[str] = []
    for db in databases:
        name_lit = _quote_literal(db["name"])
        acl_lit = "NULL" if db["datacl_text"] is None else _quote_literal(db["datacl_text"]) + "::pg_catalog.aclitem[]"
        exact = (
            f"SELECT 1 FROM pg_catalog.pg_database AS d WHERE d.oid = {db['oid']} "
            f"AND d.datname = {name_lit} AND d.datallowconn IS {str(db['allowconn']).upper()} "
            f"AND d.datistemplate IS {str(db['istemplate']).upper()} AND d.datdba = {db['owner_oid']} "
            f"AND d.datacl IS NOT DISTINCT FROM {acl_lit}"
        )
        preconditions.append(f"EXISTS ({exact})")
        structural = (
            f"EXISTS (SELECT 1 FROM pg_catalog.pg_database AS d WHERE d.oid = {db['oid']} "
            f"AND d.datname = {name_lit} AND d.datallowconn IS {str(db['allowconn']).upper()} "
            f"AND d.datistemplate IS {str(db['istemplate']).upper()} AND d.datdba = {db['owner_oid']})"
        )
        non_public = [a for a in db["effective_acl"] if a["grantee_oid"] != 0]
        non_public_checks = [
            "EXISTS (SELECT 1 FROM pg_catalog.pg_database AS d CROSS JOIN LATERAL "
            "pg_catalog.aclexplode(COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x "
            f"WHERE d.oid = {db['oid']} AND x.grantee = {a['grantee_oid']} "
            f"AND x.grantor = {a['grantor_oid']} AND x.privilege_type = {_quote_literal(a['privilege'])} "
            f"AND x.is_grantable IS {str(a['is_grantable']).upper()})"
            for a in non_public
        ]
        non_public_checks.append(
            "(SELECT pg_catalog.count(*) FROM pg_catalog.pg_database AS d CROSS JOIN LATERAL "
            "pg_catalog.aclexplode(COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x "
            f"WHERE d.oid = {db['oid']} AND x.grantee <> 0) = {len(non_public)}"
        )
        postconditions.append("(" + " AND ".join([structural, *non_public_checks]) + ")")
        classification = _database_class(db)
        public = {a["privilege"] for a in db["effective_acl"] if a["grantee_oid"] == 0}
        removable = (
            public & {"TEMPORARY", "CREATE"} if classification == "TARGET"
            else public & PRIVILEGES if classification == "OTHER_CONNECTABLE"
            else set()
        )
        if removable:
            privileges = ", ".join(sorted(removable))
            revokes.append(
                f"REVOKE {privileges} ON DATABASE {_quote_identifier(db['name'])} FROM PUBLIC RESTRICT;"
            )
        expected_public = public - removable
        retained_public = [a for a in db["effective_acl"] if a["grantee_oid"] == 0 and a["privilege"] in expected_public]
        public_checks = [
            "EXISTS (SELECT 1 FROM pg_catalog.pg_database AS d CROSS JOIN LATERAL "
            "pg_catalog.aclexplode(COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x "
            f"WHERE d.oid = {db['oid']} AND x.grantee = 0 "
            f"AND x.grantor = {acl['grantor_oid']} AND x.privilege_type = {_quote_literal(acl['privilege'])} "
            f"AND x.is_grantable IS {str(acl['is_grantable']).upper()})"
            for acl in retained_public
        ]
        public_checks.append(
            "(SELECT pg_catalog.count(*) FROM pg_catalog.pg_database AS d CROSS JOIN LATERAL "
            "pg_catalog.aclexplode(COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x "
            f"WHERE d.oid = {db['oid']} AND x.grantee = 0) = {len(retained_public)}"
        )
        postconditions.append("(" + " AND ".join(public_checks) + ")")
        if classification == "NON_CONNECTABLE":
            postconditions.append(f"EXISTS ({exact})")
    precondition_sql = " AND\n      ".join(preconditions)
    postcondition_sql = " AND\n      ".join(postconditions) or "TRUE"
    dependency_checks = []
    dependency_postchecks = []
    managed_by_key = {
        (entry["database_oid"], entry["role_oid"], entry["privilege"]): entry
        for entry in result["managed_service_evaluation"]["entries"]
    }
    for dependency in result["login_public_dependencies"]:
        source = managed_by_key[(dependency["database_oid"], dependency["role_oid"], dependency["privilege"])]
        dependency_checks.append(
            "EXISTS (SELECT 1 FROM pg_catalog.pg_database AS d CROSS JOIN pg_catalog.pg_roles AS r "
            "CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x "
            f"WHERE d.oid = {dependency['database_oid']} AND r.oid = {dependency['role_oid']} "
            f"AND x.grantee = {source['source_grantee_oid']} AND x.grantor = {source['source_grantor_oid']} "
            f"AND x.privilege_type = {_quote_literal(dependency['privilege'])} "
            f"AND x.is_grantable IS {str(source['source_is_grantable']).upper()} "
            f"AND pg_catalog.pg_has_role(r.oid, {source['source_grantee_oid']}, 'USAGE'))"
        )
        dependency_postchecks.append(
            "EXISTS (SELECT 1 FROM pg_catalog.pg_database AS d CROSS JOIN pg_catalog.pg_roles AS r "
            f"WHERE d.oid = {dependency['database_oid']} AND r.oid = {dependency['role_oid']} "
            "AND r.rolcanlogin AND pg_catalog.has_database_privilege(r.oid, d.oid, "
            f"{_quote_literal(dependency['privilege'])}))"
        )
    dependency_precondition = " AND ".join(dependency_checks) or "TRUE"
    dependency_postcondition = " AND ".join(dependency_postchecks) or "TRUE"
    expected_count = len(databases)
    sql = f"""BEGIN;
SET LOCAL search_path = pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
SELECT pg_catalog.pg_advisory_xact_lock(101010, 300312);
DO $f1010_preconditions$
BEGIN
  IF pg_catalog.current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999
     OR pg_catalog.current_database() IS DISTINCT FROM 'postgres'
     OR current_user IS DISTINCT FROM session_user
     OR (SELECT r.oid FROM pg_catalog.pg_roles AS r WHERE r.rolname = current_user) <> {executor['oid']}
     OR current_user IS DISTINCT FROM {_quote_literal(executor['name'])}
     OR pg_catalog.encode(pg_catalog.sha256(
          pg_catalog.convert_to('{EXECUTOR_DOMAIN}', 'UTF8') || pg_catalog.decode('00', 'hex') ||
          pg_catalog.convert_to({executor['oid']}::text, 'UTF8') || pg_catalog.decode('00', 'hex') ||
          pg_catalog.convert_to(current_user::text, 'UTF8')), 'hex')
        IS DISTINCT FROM {_quote_literal(executor['domain_fingerprint'])}
     OR (SELECT r.rolsuper FROM pg_catalog.pg_roles AS r WHERE r.oid = {executor['oid']})
        IS DISTINCT FROM {str(executor['is_superuser']).upper()}
     OR pg_catalog.pg_is_in_recovery()
     OR EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = '{READER_ROLE}')
     OR (SELECT pg_catalog.count(*) FROM pg_catalog.pg_database) <> {expected_count}
     OR NOT ({dependency_precondition})
     OR NOT (
      {precondition_sql}
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 PUBLIC database ACL snapshot precondition failed [{validated.snapshot_digest}]';
  END IF;
END
$f1010_preconditions$;
{os.linesep.join(revokes)}
DO $f1010_postconditions$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = '{READER_ROLE}')
     OR NOT EXISTS (
       SELECT 1
       FROM pg_catalog.pg_database AS d
       CROSS JOIN LATERAL pg_catalog.aclexplode(
         COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x
       WHERE d.datname = 'postgres'
         AND x.grantee = 0
         AND x.privilege_type = 'CONNECT'
         AND NOT x.is_grantable
     )
     OR (SELECT pg_catalog.count(*) FROM pg_catalog.pg_database) <> {expected_count}
      OR NOT (
       {postcondition_sql}
     ) OR NOT (
       {dependency_postcondition}
      ) THEN
    RAISE EXCEPTION 'F10.10 M3 PUBLIC database ACL postcondition failed [{validated.snapshot_digest}]';
  END IF;
END
$f1010_postconditions$;
COMMIT;
""".replace("\r\n", "\n")
    assert_candidate_sql_contract(sql)
    return sql


def project_apply_migration_candidate(validated: ValidatedSnapshot) -> str:
    """Regenerate a bound candidate and remove only its outer transaction."""
    if not isinstance(validated, ValidatedSnapshot):
        _stop("STOP_SNAPSHOT_BINDING")
    sql = generate_candidate_sql(validated)
    lines = sql.splitlines(keepends=True)
    if lines[0] != "BEGIN;\n" or lines[-1] != "COMMIT;\n":
        _stop("STOP_TRANSACTION_ENVELOPE")
    projected = "".join(lines[1:-1])
    if re.search(r"\b(?:BEGIN|COMMIT|ROLLBACK)\s*;", projected, re.I):
        _stop("STOP_TRANSACTION_ENVELOPE")
    return projected


def _open_private_root() -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        _stop("STOP_UNSUPPORTED_PLATFORM")
    try:
        fd = os.open(PRIVATE_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        metadata = os.fstat(fd)
        if (
            not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            os.close(fd)
            _stop("STOP_PRIVATE_ROOT")
        return fd
    except OSError as exc:
        raise PreflightError("STOP_PRIVATE_ROOT") from exc


def _private_name(path: Path) -> str:
    if path.parent.resolve() != PRIVATE_ROOT.resolve() or path.name in {"", ".", ".."}:
        _stop("STOP_PRIVATE_INPUT")
    return path.name


def _read_private(path: Path) -> Any:
    directory_fd = _open_private_root()
    fd = -1
    try:
        fd = os.open(_private_name(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd)
        metadata = os.fstat(fd)
        if (
            not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1
            or metadata.st_size <= 0 or metadata.st_size > MAX_PRIVATE_BYTES
        ):
            _stop("STOP_PRIVATE_INPUT")
        raw = os.read(fd, MAX_PRIVATE_BYTES + 1)
        if len(raw) != metadata.st_size or os.read(fd, 1):
            _stop("STOP_PRIVATE_INPUT")
        return json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError("STOP_PRIVATE_INPUT") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory_fd)


def write_private_artifact(path: Path, contents: bytes) -> None:
    if path.parent.resolve() != PRIVATE_ROOT.resolve():
        _stop("STOP_OUTPUT_PATH")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if not hasattr(os, "O_NOFOLLOW"):
        _stop("STOP_UNSUPPORTED_PLATFORM")
    flags |= os.O_NOFOLLOW
    directory_fd = _open_private_root()
    fd = -1
    try:
        fd = os.open(_private_name(path), flags, 0o600, dir_fd=directory_fd)
        os.fchmod(fd, 0o600)
        remaining = memoryview(contents)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("short write")
            remaining = remaining[written:]
        os.fsync(fd)
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1:
            raise OSError("unsafe artifact")
        os.fsync(directory_fd)
    except BaseException:
        if fd >= 0:
            try:
                os.unlink(path.name, dir_fd=directory_fd)
            except OSError:
                pass
        raise
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory_fd)


def run(argv: Sequence[str]) -> tuple[int, dict[str, Any]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("sql", "validate"), required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--target-attestation", type=Path)
    parser.add_argument("--dependency-attestation", type=Path)
    parser.add_argument("--expected-target-binding-digest")
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "sql":
        if (
            args.input or args.target_attestation or args.dependency_attestation
            or args.expected_target_binding_digest or args.private_output
        ):
            _stop("STOP_CLI_INVALID")
        return 0, {
            "schema": RESULT_SCHEMA,
            "collector_sql_digest": domain_digest("collector-sql-v1", COLLECTOR_SQL),
            "sql": COLLECTOR_SQL,
        }
    if any(value is None for value in (
        args.input, args.target_attestation, args.dependency_attestation,
        args.expected_target_binding_digest, args.private_output,
    )):
        _stop("STOP_CLI_INVALID")
    collected = _read_private(args.input)
    bound = bind_private_attestations(
        collected, _read_private(args.target_attestation), _read_private(args.dependency_attestation)
    )
    validated = validate_private_result(bound, args.expected_target_binding_digest)
    write_private_artifact(args.private_output, canonical_json(validated.private) + b"\n")
    return 0, validated.manifest


def main(argv: Sequence[str] | None = None) -> int:
    try:
        code, output = run(sys.argv[1:] if argv is None else argv)
    except (OSError, PreflightError) as exc:
        reason = str(exc) if isinstance(exc, PreflightError) else "STOP_LOCAL_IO"
        code, output = 2, {"schema": MANIFEST_SCHEMA, "decision": "STOP", "reasons": [reason]}
    sys.stdout.buffer.write(canonical_json(output) + b"\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
