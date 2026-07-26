#!/usr/bin/env python3
"""Pure local validators for the immutable F9.3 Free preflight contract."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import stat
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = "db/manifests/f9_3_free_preflight_contract.json"
CONTRACT_ID = "F9.3-FREE-PREFLIGHT-CONTRACT-20260725"
SOURCE_COMMIT_SHA = "f21b5e1e35885ea1c13894c67be7d7d8dbd04182"
SOURCE_TREE_SHA = "794f5d97a2f8f56908caa878683f1510c7e7c9b6"
F8_MANIFEST_SHA256 = "db1c61e9baf8d3927669bf33c5a8f4a708c11d87b81a41c9454dd91b63ebe4cb"
F10_DESCRIPTOR_SHA256 = "190cc10b023ce78509efe709e6edf509664a3d49d919f6a26b970bff93265f2f"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ORIGIN_RE = re.compile(r"^https://(?P<ref>[a-z0-9]{20})\.supabase\.co$")
_KEY_RE = re.compile(r"^sb_publishable_[A-Za-z0-9_-]+$")
_MIGRATION_RE = re.compile(r"^[0-9]{8}_[a-z0-9_]+$")
_MARKER_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROVIDER = "SUPA" + "BASE"
_NEXT_PUBLISHABLE = "NEXT_" + _PROVIDER + "_PUBLISHABLE_KEY"
_FREE_ORIGIN_NAME = "FREE_" + _PROVIDER + "_URL"
_FREE_KEY_NAME = "FREE_" + _NEXT_PUBLISHABLE
_PRO_ORIGIN_NAME = "PRO_" + _PROVIDER + "_URL"
_PRO_KEY_NAME = "PRO_" + _NEXT_PUBLISHABLE
_REST_V1 = "/" + "rest" + "/v1"
_API_KEY_HEADER = "api" + "key"


class PreflightContractError(RuntimeError):
    """Raised when a local preflight object fails closed."""


@dataclass(frozen=True)
class LocalFileProof:
    contract_sha256: str
    source_inventory_sha256: str
    implementation_sha256: str


@dataclass(frozen=True)
class GitBindingProof:
    source_commit_sha: str
    source_tree_sha: str
    candidate_commit_sha: str
    candidate_tree_sha: str
    entries_sha256: str
    proof_sha256: str


@dataclass(frozen=True)
class TargetValidation:
    free_fingerprint_sha256: str
    pro_fingerprint_sha256: str
    provenance_sha256: str
    validation_sha256: str


@dataclass(frozen=True)
class PreparedCatalogQuery:
    query_id: str
    sql: str
    parameters: tuple[Any, ...]
    sql_sha256: str


@dataclass(frozen=True)
class AdapterCommand:
    sequence: int
    kind: str
    value: str


@dataclass(frozen=True)
class QueryReplaySummary:
    query_id: str
    page_count: int
    row_count: int
    classification: str
    observation_sha256: str
    timeout_policy_sha256: str


@dataclass(frozen=True)
class HttpObservationSummary:
    operation_id: str
    page_count: int
    item_count: int
    observation_sha256: str


@dataclass(frozen=True)
class ToolObservationSummary:
    tool_id: str
    item_count: int
    observation_sha256: str


@dataclass(frozen=True)
class LocalCapabilitySummary:
    capability_id: str
    classification: str
    observation_sha256: str


def _fail(message: str) -> None:
    raise PreflightContractError(message)


def _reject_float(value: str) -> None:
    _fail("project-JCS-v1 forbids floating-point values")


def _reject_constant(value: str) -> None:
    _fail("project-JCS-v1 forbids non-finite values")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("project JSON contains a duplicate key")
        result[key] = value
    return result


def _validate_json(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            _fail(f"project JSON text is not NFC at {location}")
        value.encode("utf-8")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail("project JSON object key is not text")
            _validate_json(key, f"{location}.key")
            _validate_json(item, f"{location}.{key}")
        return
    _fail(f"project JSON contains unsupported {type(value).__name__}")


def strict_json_loads(payload: str | bytes) -> Any:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            _fail("project JSON is not UTF-8")
    if not isinstance(payload, str):
        _fail("project JSON input is not text")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except PreflightContractError:
        raise
    except (json.JSONDecodeError, UnicodeError):
        _fail("project JSON is invalid")
    _validate_json(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        _fail(f"{label} is not a closed object")
    return value


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{label} is not an integer in range")
    return value


def _digest(value: Any, label: str, sha1: bool = False) -> str:
    pattern = _SHA1_RE if sha1 else _SHA256_RE
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        _fail(f"{label} is not a lowercase digest")
    return value


def _lf(payload: bytes) -> bytes:
    normalized = payload.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        _fail("bound file has non-canonical line endings")
    return normalized


def _blob_sha1(payload: bytes) -> str:
    framed = f"blob {len(payload)}\0".encode("ascii") + payload
    return hashlib.sha1(framed, usedforsecurity=False).hexdigest()


def _git_object_sha1(object_type: str, payload: bytes) -> str:
    framed = f"{object_type} {len(payload)}\0".encode("ascii") + payload
    return hashlib.sha1(framed, usedforsecurity=False).hexdigest()


def _git_tree_sha1(entries: Sequence[Mapping[str, Any]]) -> str:
    """Rebuild a recursive Git tree from a complete, flat ls-tree inventory."""
    root: dict[str, Any] = {}
    for entry in entries:
        value = _exact_keys(entry, {"path", "mode", "object_type", "object_sha1"}, "Git tree entry")
        path = value["path"]
        mode = value["mode"]
        object_type = value["object_type"]
        object_sha = _digest(value["object_sha1"], "Git tree object", sha1=True)
        if (
            not isinstance(path, str) or not path or path.startswith("/") or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or "\0" in path or unicodedata.normalize("NFC", path) != path
            or (mode, object_type) not in {
                ("100644", "blob"), ("100755", "blob"), ("120000", "blob"), ("160000", "commit")
            }
        ):
            _fail("Git tree entry is non-canonical")
        node = root
        parts = path.split("/")
        for part in parts[:-1]:
            current = node.setdefault(part, {})
            if not isinstance(current, dict) or "_leaf" in current:
                _fail("Git tree inventory contains a path conflict")
            node = current
        name = parts[-1]
        if name in node:
            _fail("Git tree inventory contains a duplicate or path conflict")
        node[name] = {"_leaf": (mode, object_sha)}

    def build(node: Mapping[str, Any]) -> str:
        records: list[tuple[bytes, bytes]] = []
        for name, child in node.items():
            name_bytes = name.encode("utf-8")
            if "_leaf" in child:
                mode, object_sha = child["_leaf"]
                sort_key = name_bytes
            else:
                mode, object_sha = "40000", build(child)
                sort_key = name_bytes + b"/"
            record = mode.encode("ascii") + b" " + name_bytes + b"\0" + bytes.fromhex(object_sha)
            records.append((sort_key, record))
        payload = b"".join(record for _, record in sorted(records, key=lambda item: item[0]))
        return _git_object_sha1("tree", payload)

    return build(root)


def _validate_raw_commit(commit_sha: Any, tree_sha: Any, raw_commit_hex: Any, label: str) -> None:
    commit = _digest(commit_sha, f"{label} commit", sha1=True)
    tree = _digest(tree_sha, f"{label} tree", sha1=True)
    if not isinstance(raw_commit_hex, str) or re.fullmatch(r"(?:[0-9a-f]{2})+", raw_commit_hex) is None:
        _fail(f"{label} raw commit is not lowercase hexadecimal bytes")
    raw = bytes.fromhex(raw_commit_hex)
    if _git_object_sha1("commit", raw) != commit:
        _fail(f"{label} raw commit does not reconstruct its object id")
    first_line = raw.split(b"\n", 1)[0]
    if first_line != b"tree " + tree.encode("ascii"):
        _fail(f"{label} commit does not bind the reconstructed tree")


def _read_regular(path: Path, root: Path) -> bytes:
    root = root.absolute()
    path = path.absolute()
    try:
        relative = path.relative_to(root)
    except ValueError:
        _fail("bound path escapes repository root")
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError:
            _fail("bound path cannot be inspected")
        if stat.S_ISLNK(metadata.st_mode):
            _fail("bound path contains a symlink")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        _fail("bound path is not a regular file")
    payload = path.read_bytes()
    after = path.lstat()
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        _fail("bound file changed during read")
    if len(payload) != before.st_size:
        _fail("bound file read was incomplete")
    return payload


def _shape(*columns: tuple[str, str]) -> list[dict[str, Any]]:
    return [
        {"name": name, "type": value_type, "nullable": value_type.startswith("nullable_")}
        for name, value_type in columns
    ]


_QUERY_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "migration_ledger",
        "sql": "SELECT sm.name AS migration_name, sm.statements AS checksum_marker FROM public.supabase_migrations AS sm WHERE ($1::text IS NULL OR sm.name > $1::text) ORDER BY sm.name ASC LIMIT $2::integer",
        "shape": _shape(("migration_name", "text"), ("checksum_marker", "text")),
        "order": ["migration_name"],
        "pagination": "keyset",
        "predicate": "package_absent_or_exact_prefix",
    },
    {
        "id": "catalog_relations",
        "sql": "SELECT n.nspname AS schema_name, c.relname AS relation_name, c.relkind::text AS relation_kind, c.relrowsecurity AS row_security, c.relforcerowsecurity AS force_row_security, pg_catalog.pg_get_userbyid(c.relowner) AS owner_name FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace WHERE n.nspname IN ('public', 'auth', 'storage') AND c.relkind IN ('r', 'p', 'v', 'm', 'S') ORDER BY n.nspname ASC, c.relname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("relation_kind", "text"), ("row_security", "boolean"), ("force_row_security", "boolean"), ("owner_name", "text")),
        "order": ["schema_name", "relation_name"],
        "pagination": "offset",
        "predicate": "owner_and_rls_classified",
    },
    {
        "id": "catalog_columns",
        "sql": "SELECT c.table_schema AS schema_name, c.table_name AS relation_name, c.ordinal_position::integer AS ordinal_position, c.column_name AS column_name, c.data_type AS data_type, c.is_nullable AS is_nullable, COALESCE(c.column_default, '') AS column_default FROM information_schema.columns AS c WHERE c.table_schema IN ('public', 'auth', 'storage') ORDER BY c.table_schema ASC, c.table_name ASC, c.ordinal_position ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("ordinal_position", "integer"), ("column_name", "text"), ("data_type", "text"), ("is_nullable", "text"), ("column_default", "text")),
        "order": ["schema_name", "relation_name", "ordinal_position"],
        "pagination": "offset",
        "predicate": "catalog_identifiers_unique",
    },
    {
        "id": "catalog_constraints",
        "sql": "SELECT n.nspname AS schema_name, r.relname AS relation_name, c.conname AS constraint_name, c.contype::text AS constraint_type, c.convalidated AS validated, pg_catalog.pg_get_constraintdef(c.oid, true) AS definition FROM pg_catalog.pg_constraint AS c JOIN pg_catalog.pg_class AS r ON r.oid = c.conrelid JOIN pg_catalog.pg_namespace AS n ON n.oid = r.relnamespace WHERE n.nspname IN ('public', 'auth', 'storage') ORDER BY n.nspname ASC, r.relname ASC, c.conname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("constraint_name", "text"), ("constraint_type", "text"), ("validated", "boolean"), ("definition", "text")),
        "order": ["schema_name", "relation_name", "constraint_name"],
        "pagination": "offset",
        "predicate": "all_constraints_validated",
    },
    {
        "id": "catalog_indexes",
        "sql": "SELECT i.schemaname AS schema_name, i.tablename AS relation_name, i.indexname AS index_name, i.indexdef AS definition FROM pg_catalog.pg_indexes AS i WHERE i.schemaname IN ('public', 'auth', 'storage') ORDER BY i.schemaname ASC, i.tablename ASC, i.indexname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("index_name", "text"), ("definition", "text")),
        "order": ["schema_name", "relation_name", "index_name"],
        "pagination": "offset",
        "predicate": "catalog_identifiers_unique",
    },
    {
        "id": "catalog_policies",
        "sql": "SELECT p.schemaname AS schema_name, p.tablename AS relation_name, p.policyname AS policy_name, p.permissive AS permissive, p.roles::text AS roles, p.cmd AS command, COALESCE(p.qual, '') AS using_expression, COALESCE(p.with_check, '') AS check_expression FROM pg_catalog.pg_policies AS p WHERE p.schemaname IN ('public', 'auth', 'storage') ORDER BY p.schemaname ASC, p.tablename ASC, p.policyname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("policy_name", "text"), ("permissive", "text"), ("roles", "text"), ("command", "text"), ("using_expression", "text"), ("check_expression", "text")),
        "order": ["schema_name", "relation_name", "policy_name"],
        "pagination": "offset",
        "predicate": "policy_roles_classified",
    },
    {
        "id": "catalog_schema_acl",
        "sql": "SELECT n.nspname AS schema_name, pg_catalog.pg_get_userbyid(n.nspowner) AS owner_name, COALESCE(r.rolname, 'PUBLIC') AS grantee, x.privilege_type::text AS privilege_type, x.is_grantable AS is_grantable FROM pg_catalog.pg_namespace AS n CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) AS x LEFT JOIN pg_catalog.pg_roles AS r ON r.oid = x.grantee WHERE n.nspname IN ('public', 'auth', 'storage') ORDER BY n.nspname ASC, grantee ASC, privilege_type ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("owner_name", "text"), ("grantee", "text"), ("privilege_type", "text"), ("is_grantable", "boolean")),
        "order": ["schema_name", "grantee", "privilege_type"],
        "pagination": "offset",
        "predicate": "no_public_schema_create",
    },
    {
        "id": "catalog_table_grants",
        "sql": "SELECT g.table_schema AS schema_name, g.table_name AS object_name, g.grantee AS grantee, g.privilege_type AS privilege_type, (g.is_grantable = 'YES') AS is_grantable FROM information_schema.table_privileges AS g WHERE g.table_schema IN ('public', 'auth', 'storage') AND g.grantee IN ('PUBLIC', 'anon', 'authenticated') ORDER BY g.table_schema ASC, g.table_name ASC, g.grantee ASC, g.privilege_type ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("object_name", "text"), ("grantee", "text"), ("privilege_type", "text"), ("is_grantable", "boolean")),
        "order": ["schema_name", "object_name", "grantee", "privilege_type"],
        "pagination": "offset",
        "predicate": "package_table_acl_allowlist",
    },
    {
        "id": "catalog_column_grants",
        "sql": "SELECT g.table_schema AS schema_name, g.table_name AS object_name, g.column_name AS column_name, g.grantee AS grantee, g.privilege_type AS privilege_type, (g.is_grantable = 'YES') AS is_grantable FROM information_schema.column_privileges AS g WHERE g.table_schema IN ('public', 'auth', 'storage') AND g.grantee IN ('PUBLIC', 'anon', 'authenticated') ORDER BY g.table_schema ASC, g.table_name ASC, g.column_name ASC, g.grantee ASC, g.privilege_type ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("object_name", "text"), ("column_name", "text"), ("grantee", "text"), ("privilege_type", "text"), ("is_grantable", "boolean")),
        "order": ["schema_name", "object_name", "column_name", "grantee", "privilege_type"],
        "pagination": "offset",
        "predicate": "package_column_acl_allowlist",
    },
    {
        "id": "catalog_sequence_grants",
        "sql": "SELECT n.nspname AS schema_name, c.relname AS object_name, COALESCE(r.rolname, 'PUBLIC') AS grantee, x.privilege_type::text AS privilege_type, x.is_grantable AS is_grantable FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(c.relacl, pg_catalog.acldefault('S', c.relowner))) AS x LEFT JOIN pg_catalog.pg_roles AS r ON r.oid = x.grantee WHERE c.relkind = 'S' AND n.nspname IN ('public', 'auth', 'storage') AND COALESCE(r.rolname, 'PUBLIC') IN ('PUBLIC', 'anon', 'authenticated') ORDER BY n.nspname ASC, c.relname ASC, grantee ASC, privilege_type ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("object_name", "text"), ("grantee", "text"), ("privilege_type", "text"), ("is_grantable", "boolean")),
        "order": ["schema_name", "object_name", "grantee", "privilege_type"],
        "pagination": "offset",
        "predicate": "no_public_role_sequence_grants",
    },
    {
        "id": "catalog_routines",
        "sql": "SELECT n.nspname AS schema_name, p.proname AS routine_name, pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments, l.lanname AS language_name, p.prosecdef AS security_definer, COALESCE(pg_catalog.array_to_string(p.proconfig, ','), '') AS runtime_settings, pg_catalog.pg_get_userbyid(p.proowner) AS owner_name, pg_catalog.pg_get_function_result(p.oid) AS result_type FROM pg_catalog.pg_proc AS p JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace JOIN pg_catalog.pg_language AS l ON l.oid = p.prolang WHERE n.nspname = 'public' ORDER BY n.nspname ASC, p.proname ASC, identity_arguments ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("routine_name", "text"), ("identity_arguments", "text"), ("language_name", "text"), ("security_definer", "boolean"), ("runtime_settings", "text"), ("owner_name", "text"), ("result_type", "text")),
        "order": ["schema_name", "routine_name", "identity_arguments"],
        "pagination": "offset",
        "predicate": "exec_sql_absent_or_service_role_only",
    },
    {
        "id": "catalog_routine_grants",
        "sql": "SELECT n.nspname AS schema_name, p.proname AS routine_name, pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments, COALESCE(r.rolname, 'PUBLIC') AS grantee, x.privilege_type::text AS privilege_type, x.is_grantable AS is_grantable FROM pg_catalog.pg_proc AS p JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) AS x LEFT JOIN pg_catalog.pg_roles AS r ON r.oid = x.grantee WHERE n.nspname = 'public' AND COALESCE(r.rolname, 'PUBLIC') IN ('PUBLIC', 'anon', 'authenticated', 'service_role') ORDER BY n.nspname ASC, p.proname ASC, identity_arguments ASC, grantee ASC, privilege_type ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("routine_name", "text"), ("identity_arguments", "text"), ("grantee", "text"), ("privilege_type", "text"), ("is_grantable", "boolean")),
        "order": ["schema_name", "routine_name", "identity_arguments", "grantee", "privilege_type"],
        "pagination": "offset",
        "predicate": "exec_sql_execute_service_role_only",
    },
    {
        "id": "catalog_views",
        "sql": "SELECT n.nspname AS schema_name, c.relname AS view_name, c.relkind::text AS view_kind, COALESCE(c.reloptions::text, '') AS security_options, pg_catalog.pg_get_userbyid(c.relowner) AS owner_name FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace WHERE n.nspname IN ('public', 'auth', 'storage') AND c.relkind IN ('v', 'm') ORDER BY n.nspname ASC, c.relname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("view_name", "text"), ("view_kind", "text"), ("security_options", "text"), ("owner_name", "text")),
        "order": ["schema_name", "view_name"],
        "pagination": "offset",
        "predicate": "public_views_security_invoker",
    },
    {
        "id": "catalog_triggers",
        "sql": "SELECT n.nspname AS schema_name, c.relname AS relation_name, t.tgname AS trigger_name, t.tgenabled::text AS enabled_mode, pg_catalog.pg_get_triggerdef(t.oid, true) AS definition FROM pg_catalog.pg_trigger AS t JOIN pg_catalog.pg_class AS c ON c.oid = t.tgrelid JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND NOT t.tgisinternal ORDER BY n.nspname ASC, c.relname ASC, t.tgname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("schema_name", "text"), ("relation_name", "text"), ("trigger_name", "text"), ("enabled_mode", "text"), ("definition", "text")),
        "order": ["schema_name", "relation_name", "trigger_name"],
        "pagination": "offset",
        "predicate": "catalog_identifiers_unique",
    },
    {
        "id": "catalog_publications",
        "sql": "SELECT p.pubname AS publication_name, p.puballtables AS all_tables, p.pubinsert AS allows_insert, p.pubupdate AS allows_update, p.pubdelete AS allows_delete, p.pubtruncate AS allows_truncate FROM pg_catalog.pg_publication AS p ORDER BY p.pubname ASC LIMIT $1::integer OFFSET $2::integer",
        "shape": _shape(("publication_name", "text"), ("all_tables", "boolean"), ("allows_insert", "boolean"), ("allows_update", "boolean"), ("allows_delete", "boolean"), ("allows_truncate", "boolean")),
        "order": ["publication_name"],
        "pagination": "offset",
        "predicate": "publication_settings_classified",
    },
)

_ALLOWED_SQL_FUNCTIONS = frozenset(
    {
        "acldefault",
        "aclexplode",
        "array_to_string",
        "coalesce",
        "pg_get_constraintdef",
        "pg_get_function_identity_arguments",
        "pg_get_function_result",
        "pg_get_triggerdef",
        "pg_get_userbyid",
    }
)
_TARGET_POLICY = {
    "algorithm": "sha256",
    "namespace": "studiamatch-target-v1",
    "comparison": "hmac.compare_digest",
    "free_origin_provenance": _FREE_ORIGIN_NAME,
    "free_key_provenance": _FREE_KEY_NAME,
    "pro_origin_provenance": _PRO_ORIGIN_NAME,
    "pro_key_provenance": _PRO_KEY_NAME,
    "forbidden_generic_names": [_PROVIDER + "_URL", _NEXT_PUBLISHABLE],
    "reviewed_identity_artifact_policy": {
        "schema_version": 1,
        "source_document_path": ".context/sistema_db_supabase.md",
        "source_document_blob_sha1": "37c5a7c7acf5fb5ee6a55d57a161698f6115b1e5",
        "origin_digest_algorithm": "sha256",
        "artifact_canonicalization": "project-JCS-v1",
        "review_required": True,
        "embedded_target_digests": False,
    },
}
_HTTP_OPERATION = {
    "id": "postgrest_public_schema_probe",
    "transport_kind": "postgrest_https_get",
    "service_origin_binding": "FREE_SUPABASE_URL",
    "path_template": _REST_V1 + "/",
    "method": "GET",
    "query_parameters": [],
    "header_names": ["Accept", _API_KEY_HEADER],
    "auth_class": "supabase_publishable_apikey_only",
    "redirects_allowed": False,
    "timeout_ms": 5000,
    "response_content_type": "application/openapi+json",
    "pagination": {"mode": "offset", "page_size": 2, "terminal_short_page": True, "exact_total_required": True},
    "cardinality": {"min_total_rows": 1, "max_total_rows": 1},
    "response_projection": {"openapi_version": "openapi", "path_count": "paths_count", "definition_count": "definitions_count"},
    "response_shape": _shape(("openapi_version", "text"), ("path_count", "integer"), ("definition_count", "integer")),
    "acceptance_predicate": "public_schema_document_classified",
}
_TOOL_CATALOG = [
    {
        "id": "security_advisors",
        "adapter_identity": "supabase-free.get_advisors",
        "arguments": {"type": "security"},
        "project_binding": "FREE_SUPABASE_PROJECT_REF",
        "timeout_ms": 5000,
        "executable_in_f9_3": False,
        "response_projection": ["advisory_count", "levels_sha256", "payload_sha256"],
    },
    {
        "id": "performance_advisors",
        "adapter_identity": "supabase-free.get_advisors",
        "arguments": {"type": "performance"},
        "project_binding": "FREE_SUPABASE_PROJECT_REF",
        "timeout_ms": 5000,
        "executable_in_f9_3": False,
        "response_projection": ["advisory_count", "levels_sha256", "payload_sha256"],
    },
]
_LOCAL_CAPABILITIES = [
    {"id": "backup_capability", "kind": "human_gate", "required_classification": "BACKUP_APPROVAL_REQUIRED_NOT_EXECUTED"},
    {"id": "writer_pause_capability", "kind": "human_gate", "required_classification": "SEPARATE_PAUSE_RESUME_APPROVAL_REQUIRED"},
    {"id": "rollback_capability", "kind": "local_contract", "required_classification": "ROLLBACK_ONLY_NO_REMOTE_EXECUTION"},
]
_COURSE_PUBLIC_COLUMNS = [
    "id", "name", "slug", "url", "institution_id", "price_pen", "price_status", "mode",
    "course_type", "category_id", "duration", "start_date_text", "description_long", "syllabus",
    "target_audience", "requirements", "certification", "benefits", "objectives",
    "expected_monthly_salary", "seniority_level", "roi_months", "address", "region", "is_active",
    "is_verified", "brochure_url", "start_date", "created_at", "updated_at", "publication_status",
]
_ACL_POLICY = {
    "public_roles": ["PUBLIC", "anon", "authenticated"],
    "grantable_allowed": False,
    "table_grants": [
        {"schema_name": "public", "object_name": "leads", "grantees": ["anon", "authenticated"], "privileges": ["INSERT"]},
    ],
    "column_grants": [
        {"schema_name": "public", "object_name": "courses", "grantees": ["anon", "authenticated"], "privilege": "SELECT", "columns": _COURSE_PUBLIC_COLUMNS},
        {"schema_name": "public", "object_name": "institution_site_profiles", "grantees": ["anon", "authenticated"], "privilege": "SELECT", "columns": ["institution_id", "production_enabled"]},
        {"schema_name": "public", "object_name": "ratings", "grantees": ["anon", "authenticated"], "privilege": "SELECT", "columns": ["id", "course_id", "rating_value", "user_nickname", "created_at"]},
        {"schema_name": "public", "object_name": "reviews", "grantees": ["anon", "authenticated"], "privilege": "SELECT", "columns": ["id", "course_id", "content", "user_nickname", "created_at"]},
    ],
    "sequence_grants": [],
    "exec_sql_contract": {
        "schema_name": "public", "routine_name": "exec_sql", "identity_arguments": "sql_text text",
        "result_type": "jsonb", "owner_name": "postgres", "language_name": "plpgsql",
        "security_definer": True, "runtime_settings": "search_path=\"\"", "allowed_execute_grantees": ["service_role"],
        "grantable_allowed": False, "maximum_overloads": 1,
    },
}
_EVIDENCE_SCHEMA = {
    "schema_version": 3,
    "pass_fields": [
        "schema_version", "status", "contract_sha256", "git_binding_sha256", "target_identity_sha256",
        "query_count", "http_count", "tool_count", "local_count", "page_count", "row_count",
        "query_observations_sha256", "http_observations_sha256", "tool_observations_sha256",
        "local_observations_sha256", "adapter_policy_sha256",
    ],
    "fail_fields": [
        "schema_version", "status", "contract_sha256", "git_binding_sha256", "target_identity_sha256",
        "query_count", "http_count", "tool_count", "local_count", "page_count", "row_count",
        "query_observations_sha256", "http_observations_sha256", "tool_observations_sha256",
        "local_observations_sha256", "adapter_policy_sha256", "failure_code", "failed_operation_id_sha256",
    ],
    "count_fields": ["query_count", "http_count", "tool_count", "local_count", "page_count", "row_count"],
    "digest_fields": [
        "contract_sha256", "git_binding_sha256", "target_identity_sha256", "query_observations_sha256",
        "http_observations_sha256", "tool_observations_sha256", "local_observations_sha256",
        "adapter_policy_sha256",
    ],
    "failure_codes": [
        "TARGET_IDENTITY_MISMATCH", "SQL_TRACE_INVALID", "HTTP_TRACE_INVALID", "TOOL_TRACE_INVALID",
        "LEDGER_MISMATCH", "CATALOG_POLICY_VIOLATION", "TIMEOUT", "TRANSPORT_ERROR",
    ],
    "validator_only": True,
    "builder_owned_by": "F9.4_SEPARATE_ADAPTER",
    "raw_rows_forbidden": True,
    "sensitive_components_forbidden": True,
}
_TRACE_SCHEMAS = {
    "sql": {"schema_version": 1, "exact_fields": ["schema_version", "target_identity_sha256", "session_id_sha256", "command_sequence_sha256", "query_ids", "query_page_digests", "timeout_settings", "rollback_completed"], "raw_rows_forbidden": True},
    "http": {"schema_version": 1, "exact_fields": ["schema_version", "target_identity_sha256", "operation_id", "method", "origin_binding", "path", "query_parameter_names", "header_names", "auth_class", "status_code", "redirected", "request_body_present", "content_type", "response_size_bytes", "page_count", "pages_sha256"], "raw_body_forbidden": True},
    "tool": {"schema_version": 1, "exact_fields": ["schema_version", "target_identity_sha256", "tool_id", "adapter_identity", "arguments", "project_binding", "project_identity_sha256", "timeout_ms", "response_projection", "response_sha256", "item_count"], "raw_response_forbidden": True},
}
_SOURCE_ENTRIES = [
    ("db/manifests/fase08_candidate.json", "f0ab0f5f62a723973f6201d067cfc6271218de4b", "6946570738aba234bb41273fc0839a50ece0617d464906a84736d1b2aafd4fee"),
    ("db/manifests/fase10_promotion_contract.json", "94afe5c1fdd63bd8bcf2509ba91e8a58d4aa0256", "ee4eb7b228545be30d031643014fb27028ac72bc24e9f7afe7bcee2d02bca66b"),
    ("db/migrations/20260724_fase06_g1b_reconciliation.sql", "1cf2b0431e08a577d452df8e37ed1940518cb052", "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df"),
    ("db/migrations/20260724_fase06_hito1_editorial_contract.sql", "18e4feefc8d92ddd7dcad02686b1125d9652d1ac", "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a"),
    ("db/migrations/20260725_fase07_g1b_closure.sql", "e7deff5dd9ffdcf2770bbcc13e32ab97cb0c3329", "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120"),
    ("db/migrations/20260725_fase08_hito1_functional_closure.sql", "0f3e9959b1436cc6501bea83d94f748a6291e097", "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527"),
]
_PACKAGE_ENTRIES = [
    ("F6-G1B-FORWARD", "20260724_fase06_g1b_reconciliation", _SOURCE_ENTRIES[2][0], _SOURCE_ENTRIES[2][2]),
    ("F6-HITO1-FORWARD", "20260724_fase06_hito1_editorial_contract", _SOURCE_ENTRIES[3][0], _SOURCE_ENTRIES[3][2]),
    ("F7-G1B-CLOSURE", "20260725_fase07_g1b_closure", _SOURCE_ENTRIES[4][0], _SOURCE_ENTRIES[4][2]),
    ("F8-HITO1-FUNCTIONAL-CLOSURE", "20260725_fase08_hito1_functional_closure", _SOURCE_ENTRIES[5][0], _SOURCE_ENTRIES[5][2]),
]


def _expected_query(definition: Mapping[str, Any]) -> dict[str, Any]:
    pagination = {
        "mode": definition["pagination"],
        "page_size": 100,
        "order_columns": definition["order"],
        "terminal_short_page": True,
        "exact_total_required": True,
    }
    if definition["pagination"] == "keyset":
        pagination["cursor_parameter"] = "after_name"
        parameters = [
            {"name": "after_name", "position": 1, "type": "nullable_migration_name"},
            {"name": "page_size", "position": 2, "type": "fixed_integer", "value": 100},
        ]
    else:
        pagination["offset_parameter"] = "offset"
        parameters = [
            {"name": "page_size", "position": 1, "type": "fixed_integer", "value": 100},
            {"name": "offset", "position": 2, "type": "bounded_integer", "minimum": 0, "maximum": 100000},
        ]
    return {
        "id": definition["id"],
        "sql": definition["sql"],
        "sql_sha256": hashlib.sha256(definition["sql"].encode("utf-8")).hexdigest(),
        "allowed_catalog_functions": sorted(_allowed_functions(definition["sql"])),
        "parameters": parameters,
        "result_shape": definition["shape"],
        "pagination": pagination,
        "cardinality": {"min_total_rows": 0, "max_total_rows": 100000, "max_page_rows": 100},
        "timeout_ms": 5000,
        "acceptance": {"predicate": definition["predicate"], "classification_output": "aggregate_digest_only"},
    }


def _allowed_functions(sql: str) -> set[str]:
    calls = set(re.findall(r"\b(?:pg_catalog\.)?([a-z_][a-z0-9_]*)\s*\(", sql.casefold()))
    calls.difference_update({"in", "where"})
    return calls.intersection(_ALLOWED_SQL_FUNCTIONS)


def _validate_sql_exact(query: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    sql = query.get("sql")
    if sql != expected["sql"] or query.get("sql_sha256") != expected["sql_sha256"]:
        _fail("catalog query differs from its reviewed exact SQL")
    lowered = sql.casefold()
    if (
        not lowered.startswith("select ")
        or ";" in sql
        or "--" in sql
        or "/*" in sql
        or re.search(r"\bselect\s+.+\s+into\b", lowered)
        or lowered.startswith("with ")
    ):
        _fail("catalog SQL is not one side-effect-free SELECT")
    calls = set(re.findall(r"\b(?:pg_catalog\.)?([a-z_][a-z0-9_]*)\s*\(", lowered))
    calls.difference_update({"in", "where"})
    unknown = calls - _ALLOWED_SQL_FUNCTIONS
    if unknown or sorted(calls) != query["allowed_catalog_functions"]:
        _fail("catalog SQL invokes a function outside the reviewed allowlist")


def validate_contract_shape(contract: Any) -> dict[str, Any]:
    top = _exact_keys(
        contract,
        {
            "schema_version", "phase", "contract_id", "capability_class", "canonicalization",
            "source_binding", "package_binding", "implementation_binding", "target_binding",
            "transaction_policy", "query_catalog", "http_catalog", "tool_catalog",
            "local_capability_catalog", "acl_policy", "trace_schemas", "evidence_schema",
        },
        "contract",
    )
    if type(top["schema_version"]) is not int or top["schema_version"] != 2:
        _fail("contract schema_version is not integer 2")
    if (top["phase"], top["contract_id"], top["capability_class"], top["canonicalization"]) != (
        "F9.3", CONTRACT_ID, "LOCAL_FREE_PREFLIGHT_CONTRACT", "project-JCS-v1"
    ):
        _fail("contract identity drifted")

    source = _exact_keys(top["source_binding"], {"commit_sha", "tree_sha", "entries"}, "source binding")
    expected_source = [
        {"path": path, "mode": "100644", "git_blob_sha1": blob, "raw_lf_sha256": raw}
        for path, blob, raw in _SOURCE_ENTRIES
    ]
    if source != {"commit_sha": SOURCE_COMMIT_SHA, "tree_sha": SOURCE_TREE_SHA, "entries": expected_source}:
        _fail("source commit/tree/blob inventory drifted")

    package = _exact_keys(
        top["package_binding"],
        {"package_id", "status", "blocked_targets", "manifest", "promotion_contract", "entries"},
        "package binding",
    )
    expected_package_entries = [
        {"id": item_id, "migration_name": name, "path": path, "sha256": digest}
        for item_id, name, path, digest in _PACKAGE_ENTRIES
    ]
    if package != {
        "package_id": "F8-HITO1-FUNCTIONAL-20260725",
        "status": "reconciled_not_certified",
        "blocked_targets": ["free", "pro"],
        "manifest": {"path": _SOURCE_ENTRIES[0][0], "canonical_json_sha256": F8_MANIFEST_SHA256},
        "promotion_contract": {"path": _SOURCE_ENTRIES[1][0], "canonical_json_sha256": F10_DESCRIPTOR_SHA256},
        "entries": expected_package_entries,
    }:
        _fail("package binding drifted")

    implementation = _exact_keys(
        top["implementation_binding"],
        {"runtime_validators", "transitive_project_modules", "candidate_git_required_paths"},
        "implementation binding",
    )
    validators = implementation["runtime_validators"]
    if (
        not isinstance(validators, list)
        or len(validators) != 1
        or set(validators[0]) != {"path", "raw_lf_sha256", "role"}
        or validators[0]["path"] != "scripts/maintenance/free_preflight.py"
        or validators[0]["role"] != "all_contract_query_target_evidence_validators"
    ):
        _fail("runtime validator inventory is not closed")
    _digest(validators[0]["raw_lf_sha256"], "runtime validator hash")
    if implementation["transitive_project_modules"] != []:
        _fail("runtime validator has a project dependency")
    if implementation["candidate_git_required_paths"] != [
        CONTRACT_PATH,
        "scripts/maintenance/free_preflight.py",
        "tests/test_fase09_free_preflight.py",
        ".github/workflows/security-audit.yml",
    ]:
        _fail("candidate Git proof path inventory drifted")

    if top["target_binding"] != _TARGET_POLICY:
        _fail("target provenance policy drifted")
    transaction = top["transaction_policy"]
    expected_sequence = [
        {"sequence": 1, "kind": "transaction", "value": "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"},
        {"sequence": 2, "kind": "set_local", "value": "SET LOCAL statement_timeout = '5000ms'"},
        {"sequence": 3, "kind": "set_local", "value": "SET LOCAL lock_timeout = '1000ms'"},
        {"sequence": 4, "kind": "set_local", "value": "SET LOCAL idle_in_transaction_session_timeout = '10000ms'"},
        {"sequence": 5, "kind": "catalog", "value": "ALL_QUERY_IDS_IN_DESCRIPTOR_ORDER"},
        {"sequence": 6, "kind": "transaction", "value": "ROLLBACK"},
    ]
    if transaction != {"adapter_command_sequence": expected_sequence, "generic_sql_allowed": False, "server_timeout_proof_required": True}:
        _fail("transaction adapter command sequence drifted")

    expected_queries = [_expected_query(item) for item in _QUERY_DEFINITIONS]
    if top["query_catalog"] != expected_queries:
        _fail("query catalog differs from the reviewed catalog")
    for query, expected in zip(top["query_catalog"], expected_queries):
        _validate_sql_exact(query, expected)
    if top["http_catalog"] != [_HTTP_OPERATION]:
        _fail("HTTP request catalog drifted")
    if top["tool_catalog"] != _TOOL_CATALOG:
        _fail("future tool catalog drifted")
    if top["local_capability_catalog"] != _LOCAL_CAPABILITIES:
        _fail("local capability catalog drifted")
    if top["acl_policy"] != _ACL_POLICY:
        _fail("package-bound ACL policy drifted")
    if top["trace_schemas"] != _TRACE_SCHEMAS:
        _fail("raw trace schema drifted")
    if top["evidence_schema"] != _EVIDENCE_SCHEMA:
        _fail("evidence schema drifted")
    return top


def load_contract(contract_path: str | Path = CONTRACT_PATH, root: str | Path = ROOT) -> dict[str, Any]:
    root_path = Path(root).absolute()
    requested = Path(contract_path)
    if not requested.is_absolute() and requested.as_posix() != CONTRACT_PATH:
        _fail("contract path is not canonical")
    path = requested if requested.is_absolute() else root_path / requested
    if path.absolute() != (root_path / CONTRACT_PATH).absolute():
        _fail("contract path is not canonical")
    value = strict_json_loads(_read_regular(path, root_path))
    return validate_contract_shape(value)


def validate_contract_files(contract: Mapping[str, Any], root: str | Path = ROOT) -> LocalFileProof:
    validated = validate_contract_shape(contract)
    root_path = Path(root).absolute()
    for entry in validated["source_binding"]["entries"]:
        payload = _lf(_read_regular(root_path / entry["path"], root_path))
        if hashlib.sha256(payload).hexdigest() != entry["raw_lf_sha256"] or _blob_sha1(payload) != entry["git_blob_sha1"]:
            _fail("source file does not match commit blob inventory")
    validator = validated["implementation_binding"]["runtime_validators"][0]
    runner = _lf(_read_regular(root_path / validator["path"], root_path))
    if hashlib.sha256(runner).hexdigest() != validator["raw_lf_sha256"]:
        _fail("runtime validator implementation drifted")
    manifest = strict_json_loads(_read_regular(root_path / _SOURCE_ENTRIES[0][0], root_path))
    promotion = strict_json_loads(_read_regular(root_path / _SOURCE_ENTRIES[1][0], root_path))
    if canonical_json_sha256(manifest) != F8_MANIFEST_SHA256 or canonical_json_sha256(promotion) != F10_DESCRIPTOR_SHA256:
        _fail("bound package descriptor canonical digest drifted")
    return LocalFileProof(
        contract_sha256=canonical_json_sha256(validated),
        source_inventory_sha256=canonical_json_sha256(validated["source_binding"]["entries"]),
        implementation_sha256=hashlib.sha256(runner).hexdigest(),
    )


def validate_git_binding(contract: Mapping[str, Any], proof: Any, root: str | Path = ROOT) -> GitBindingProof:
    """Cryptographically reconstruct raw commits and complete recursive trees."""
    validated = validate_contract_shape(contract)
    root_path = Path(root).absolute()
    value = _exact_keys(proof, {"schema_version", "provenance", "source", "candidate"}, "Git proof")
    if type(value["schema_version"]) is not int or value["schema_version"] != 2 or value["provenance"] != "raw_git_objects_complete_tree_v1":
        _fail("Git proof provenance is invalid")
    object_keys = {"commit_sha", "raw_commit_hex", "tree_sha", "entries"}
    source = _exact_keys(value["source"], object_keys, "source Git proof")
    candidate = _exact_keys(value["candidate"], object_keys, "candidate Git proof")
    for label, binding in (("source", source), ("candidate", candidate)):
        if not isinstance(binding["entries"], list) or not binding["entries"]:
            _fail(f"{label} complete Git tree inventory is missing")
        reconstructed_tree = _git_tree_sha1(binding["entries"])
        if reconstructed_tree != binding["tree_sha"]:
            _fail(f"{label} complete Git tree does not reconstruct its object id")
        _validate_raw_commit(binding["commit_sha"], binding["tree_sha"], binding["raw_commit_hex"], label)
    if source["commit_sha"] != validated["source_binding"]["commit_sha"] or source["tree_sha"] != validated["source_binding"]["tree_sha"]:
        _fail("actual Git source commit/tree differs from frozen source binding")
    source_by_path = {entry["path"]: entry for entry in source["entries"]}
    if len(source_by_path) != len(source["entries"]):
        _fail("source complete Git inventory contains duplicate paths")
    for expected in validated["source_binding"]["entries"]:
        actual = source_by_path.get(expected["path"])
        if actual != {
            "path": expected["path"], "mode": expected["mode"],
            "object_type": "blob", "object_sha1": expected["git_blob_sha1"],
        }:
            _fail("actual Git source blob differs from frozen source inventory")
    candidate_commit = _digest(candidate["commit_sha"], "candidate commit", sha1=True)
    candidate_tree = _digest(candidate["tree_sha"], "candidate tree", sha1=True)
    paths = validated["implementation_binding"]["candidate_git_required_paths"]
    entries = candidate["entries"]
    candidate_by_path = {entry["path"]: entry for entry in entries}
    if len(candidate_by_path) != len(entries) or any(path not in candidate_by_path for path in paths):
        _fail("candidate complete Git inventory omits a required path")
    required_entries = []
    for path in paths:
        entry = candidate_by_path[path]
        if entry["mode"] != "100644" or entry["object_type"] != "blob":
            _fail("candidate Git entry mode is not canonical")
        payload = _lf(_read_regular(root_path / path, root_path))
        if _blob_sha1(payload) != entry["object_sha1"]:
            _fail("candidate Git blob does not match working reviewed bytes")
        required_entries.append(entry)
    canonical = canonical_json_bytes(value)
    return GitBindingProof(
        source_commit_sha=source["commit_sha"],
        source_tree_sha=source["tree_sha"],
        candidate_commit_sha=candidate_commit,
        candidate_tree_sha=candidate_tree,
        entries_sha256=canonical_json_sha256(required_entries),
        proof_sha256=hashlib.sha256(canonical).hexdigest(),
    )


def build_target_validation(
    contract: Mapping[str, Any],
    named_configuration: Mapping[str, str],
    reviewed_identity_artifact: Mapping[str, Any],
) -> TargetValidation:
    validated = validate_contract_shape(contract)
    policy = validated["target_binding"]
    names = [
        policy["free_origin_provenance"], policy["free_key_provenance"],
        policy["pro_origin_provenance"], policy["pro_key_provenance"],
    ]
    if not isinstance(named_configuration, Mapping) or set(named_configuration) != set(names):
        _fail("target configuration provenance names are not exact")
    free_origin, free_key, pro_origin, pro_key = (named_configuration[name] for name in names)
    free_match = _ORIGIN_RE.fullmatch(free_origin) if isinstance(free_origin, str) else None
    pro_match = _ORIGIN_RE.fullmatch(pro_origin) if isinstance(pro_origin, str) else None
    if free_match is None or pro_match is None or _KEY_RE.fullmatch(free_key) is None or _KEY_RE.fullmatch(pro_key) is None:
        _fail("target configuration components are invalid")
    free_key_hash = hashlib.sha256(free_key.encode()).hexdigest()
    pro_key_hash = hashlib.sha256(pro_key.encode()).hexdigest()
    free_material = f"studiamatch-target-v1\0free\0{free_origin}\0{free_key_hash}".encode()
    pro_material = f"studiamatch-target-v1\0pro\0{pro_origin}\0{pro_key_hash}".encode()
    free_fingerprint = hashlib.sha256(free_material).hexdigest()
    pro_fingerprint = hashlib.sha256(pro_material).hexdigest()
    if (
        hmac.compare_digest(free_origin, pro_origin)
        or hmac.compare_digest(free_key_hash, pro_key_hash)
        or hmac.compare_digest(free_match.group("ref"), pro_match.group("ref"))
        or hmac.compare_digest(free_fingerprint, pro_fingerprint)
    ):
        _fail("Free and Pro target configurations are ambiguous or reused")
    artifact = _exact_keys(
        reviewed_identity_artifact,
        {
            "schema_version", "source_document_path", "source_document_blob_sha1",
            "free_origin_sha256", "pro_origin_sha256", "artifact_sha256",
        },
        "reviewed target identity artifact",
    )
    if type(artifact["schema_version"]) is not int or artifact["schema_version"] != 1:
        _fail("reviewed target artifact schema is invalid")
    policy_artifact = validated["target_binding"]["reviewed_identity_artifact_policy"]
    if (
        artifact["source_document_path"] != policy_artifact["source_document_path"]
        or artifact["source_document_blob_sha1"] != policy_artifact["source_document_blob_sha1"]
    ):
        _fail("reviewed target artifact source binding drifted")
    for field in ("free_origin_sha256", "pro_origin_sha256", "artifact_sha256"):
        _digest(artifact[field], f"target artifact {field}")
    artifact_payload = {key: artifact[key] for key in artifact if key != "artifact_sha256"}
    if canonical_json_sha256(artifact_payload) != artifact["artifact_sha256"]:
        _fail("reviewed target artifact digest is invalid")
    if (
        not hmac.compare_digest(hashlib.sha256(free_origin.encode()).hexdigest(), artifact["free_origin_sha256"])
        or not hmac.compare_digest(hashlib.sha256(pro_origin.encode()).hexdigest(), artifact["pro_origin_sha256"])
        or hmac.compare_digest(artifact["free_origin_sha256"], artifact["pro_origin_sha256"])
    ):
        _fail("Free and Pro origins are swapped or do not match the reviewed artifact")
    provenance = {name: hashlib.sha256(named_configuration[name].encode()).hexdigest() for name in names}
    payload = {
        "free_fingerprint_sha256": free_fingerprint,
        "pro_fingerprint_sha256": pro_fingerprint,
        "provenance_sha256": canonical_json_sha256(provenance),
    }
    return TargetValidation(
        free_fingerprint_sha256=free_fingerprint,
        pro_fingerprint_sha256=pro_fingerprint,
        provenance_sha256=payload["provenance_sha256"],
        validation_sha256=canonical_json_sha256({**payload, "artifact_sha256": artifact["artifact_sha256"]}),
    )


def prepare_catalog_query(contract: Mapping[str, Any], query_id: str, parameters: Mapping[str, Any]) -> PreparedCatalogQuery:
    validated = validate_contract_shape(contract)
    queries = {item["id"]: item for item in validated["query_catalog"]}
    if query_id not in queries:
        _fail("query is not in the closed catalog")
    query = queries[query_id]
    expected_names = {item["name"] for item in query["parameters"]}
    if not isinstance(parameters, Mapping) or set(parameters) != expected_names:
        _fail("query parameters are not closed")
    positional: list[Any] = []
    for specification in query["parameters"]:
        value = parameters[specification["name"]]
        kind = specification["type"]
        if kind == "fixed_integer" and (type(value) is not int or value != specification["value"]):
            _fail("fixed query parameter drifted")
        if kind == "bounded_integer" and (type(value) is not int or not specification["minimum"] <= value <= specification["maximum"]):
            _fail("bounded query parameter is invalid")
        if kind == "nullable_migration_name" and value is not None and (not isinstance(value, str) or _MIGRATION_RE.fullmatch(value) is None):
            _fail("keyset query cursor is invalid")
        positional.append(value)
    return PreparedCatalogQuery(query_id, query["sql"], tuple(positional), query["sql_sha256"])


def catalog_adapter_commands(contract: Mapping[str, Any]) -> tuple[AdapterCommand, ...]:
    validated = validate_contract_shape(contract)
    return tuple(AdapterCommand(item["sequence"], item["kind"], item["value"]) for item in validated["transaction_policy"]["adapter_command_sequence"])


_PAGE_KEYS = {"operation_id", "page_index", "request_cursor", "request_offset", "total_count", "start_index", "end_index", "server_timeout_ms", "timeout_enforced", "rows"}


def _validate_row(shape: Sequence[Mapping[str, Any]], row: Any) -> None:
    expected = {item["name"] for item in shape}
    _exact_keys(row, expected, "projected row")
    for column in shape:
        value = row[column["name"]]
        if value is None and column["nullable"]:
            continue
        if column["type"] in {"text", "nullable_text"} and (not isinstance(value, str) or unicodedata.normalize("NFC", value) != value):
            _fail("projected row text is invalid")
        if column["type"] == "integer" and type(value) is not int:
            _fail("projected row integer is invalid")
        if column["type"] == "boolean" and type(value) is not bool:
            _fail("projected row boolean is invalid")


def _validate_pages(operation: Mapping[str, Any], pages: Sequence[Mapping[str, Any]], shape: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(pages, (list, tuple)) or not pages:
        _fail("observation pages are missing")
    pagination = operation["pagination"]
    page_size = pagination["page_size"]
    rows_all: list[dict[str, Any]] = []
    total: int | None = None
    cursor: Any = None
    previous_order: tuple[Any, ...] | None = None
    order_columns = pagination.get("order_columns", [shape[0]["name"]])
    for index, page in enumerate(pages):
        _exact_keys(page, _PAGE_KEYS, "observation page")
        if page["operation_id"] != operation["id"] or _integer(page["page_index"], "page index") != index:
            _fail("page identity or sequence drifted")
        observed_total = _integer(page["total_count"], "page total")
        total = observed_total if total is None else total
        if observed_total != total:
            _fail("page total changed")
        if type(page["timeout_enforced"]) is not bool or not page["timeout_enforced"] or page["server_timeout_ms"] != operation["timeout_ms"]:
            _fail("server-enforced timeout proof is missing")
        rows = page["rows"]
        if not isinstance(rows, list) or len(rows) > page_size:
            _fail("page cardinality exceeds contract")
        start = len(rows_all)
        if rows:
            if type(page["start_index"]) is not int or type(page["end_index"]) is not int or page["start_index"] != start or page["end_index"] != start + len(rows) - 1:
                _fail("page boundaries are invalid")
        elif page["start_index"] is not None or page["end_index"] is not None:
            _fail("empty terminal page has boundaries")
        if pagination["mode"] == "offset":
            if page["request_cursor"] is not None or type(page["request_offset"]) is not int or page["request_offset"] != index * page_size:
                _fail("offset pagination metadata is invalid")
        else:
            if page["request_offset"] is not None or page["request_cursor"] != cursor:
                _fail("keyset cursor is invalid")
        for row in rows:
            _validate_row(shape, row)
            order = tuple(row[name] for name in order_columns)
            if previous_order is not None and order <= previous_order:
                _fail("page ordering duplicated or regressed")
            previous_order = order
            rows_all.append(dict(row))
        if pagination["mode"] == "keyset" and rows:
            cursor = rows[-1][order_columns[0]]
    if total is None or len(rows_all) != total:
        _fail("page ledger is truncated")
    expected_pages = total // page_size + 1
    if total % page_size:
        expected_pages = total // page_size + 1
    if len(pages) != expected_pages or len(pages[-1]["rows"]) >= page_size:
        _fail("mandatory terminal short page is absent")
    if any(len(page["rows"]) != page_size for page in pages[:-1]):
        _fail("non-terminal page is short")
    if not operation["cardinality"]["min_total_rows"] <= total <= operation["cardinality"]["max_total_rows"]:
        _fail("observation total is outside cardinality")
    return rows_all


def _acceptance(contract: Mapping[str, Any], query: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> str:
    predicate = query["acceptance"]["predicate"]
    public_roles = {"PUBLIC", "anon", "authenticated"}
    if predicate == "package_absent_or_exact_prefix":
        expected = {item["migration_name"]: item for item in contract["package_binding"]["entries"]}
        observed = []
        for row in rows:
            if _MIGRATION_RE.fullmatch(row["migration_name"]) is None or _MARKER_RE.fullmatch(row["checksum_marker"]) is None:
                _fail("ledger row is malformed")
            if row["migration_name"] in expected:
                if row["checksum_marker"] != "sha256:" + expected[row["migration_name"]]["sha256"]:
                    _fail("ledger checksum drifted")
                observed.append(row["migration_name"])
        names = [item["migration_name"] for item in contract["package_binding"]["entries"]]
        if observed != names[: len(observed)]:
            _fail("ledger package has a gap")
        return f"EXACT_PREFIX_{len(observed)}"
    if predicate == "owner_and_rls_classified":
        if any(not row["owner_name"] or row["relation_kind"] not in {"r", "p", "v", "m", "S"} for row in rows):
            _fail("relation owner or kind is invalid")
        enabled = sum(1 for row in rows if row["row_security"])
        return f"OWNERS_VALID_RLS_ENABLED_{enabled}_DISABLED_{len(rows) - enabled}"
    if predicate == "catalog_identifiers_unique":
        return f"CATALOG_IDENTIFIERS_VALID_{len(rows)}"
    if predicate == "policy_roles_classified":
        if any(not row["roles"] or row["command"] not in {"ALL", "SELECT", "INSERT", "UPDATE", "DELETE"} for row in rows):
            _fail("policy role or command classification is invalid")
        return f"POLICIES_CLASSIFIED_{len(rows)}"
    if predicate == "all_constraints_validated" and any(not row["validated"] for row in rows):
        _fail("catalog contains an unvalidated constraint")
    if predicate == "all_constraints_validated":
        return f"CONSTRAINTS_VALIDATED_{len(rows)}"
    if predicate == "no_public_schema_create" and any(row["grantee"] in public_roles and row["privilege_type"] == "CREATE" for row in rows):
        _fail("public role has schema CREATE")
    if predicate == "no_public_schema_create":
        if any(not row["owner_name"] or (row["grantee"] in public_roles and row["is_grantable"]) for row in rows):
            _fail("schema owner is missing or a public grant is grantable")
        return f"SCHEMA_OWNERS_ACL_RESTRICTED_{len(rows)}"
    if predicate == "package_table_acl_allowlist":
        allowed = {
            (rule["schema_name"], rule["object_name"], grantee, privilege)
            for rule in contract["acl_policy"]["table_grants"]
            for grantee in rule["grantees"] for privilege in rule["privileges"]
        }
        observed = {(row["schema_name"], row["object_name"], row["grantee"], row["privilege_type"]) for row in rows}
        if observed - allowed or any(row["is_grantable"] for row in rows):
            _fail("table ACL exceeds the package-bound allowlist")
        return f"PACKAGE_TABLE_ACL_SUBSET_{len(rows)}"
    if predicate == "package_column_acl_allowlist":
        allowed = {
            (rule["schema_name"], rule["object_name"], column, grantee, rule["privilege"])
            for rule in contract["acl_policy"]["column_grants"]
            for column in rule["columns"] for grantee in rule["grantees"]
        }
        observed = {(row["schema_name"], row["object_name"], row["column_name"], row["grantee"], row["privilege_type"]) for row in rows}
        if observed - allowed or any(row["is_grantable"] for row in rows):
            _fail("column ACL exceeds the package-bound allowlist")
        return f"PACKAGE_COLUMN_ACL_SUBSET_{len(rows)}"
    if predicate == "no_public_role_sequence_grants" and (rows or any(row["is_grantable"] for row in rows)):
        _fail("public role has a sequence privilege")
    if predicate == "no_public_role_sequence_grants":
        return f"SEQUENCE_GRANTS_RESTRICTED_{len(rows)}"
    if predicate == "exec_sql_execute_service_role_only":
        grants = [row for row in rows if row["routine_name"] == "exec_sql"]
        expected = contract["acl_policy"]["exec_sql_contract"]
        if grants and (
            len(grants) != 1 or grants[0]["identity_arguments"] != expected["identity_arguments"]
            or grants[0]["grantee"] not in expected["allowed_execute_grantees"]
            or grants[0]["privilege_type"] != "EXECUTE" or grants[0]["is_grantable"]
        ):
            _fail("exec_sql normalized ACL is not service-role-only")
        return "EXEC_SQL_GRANTS_RESTRICTED" if grants else "EXEC_SQL_GRANTS_ABSENT"
    if predicate == "exec_sql_absent_or_service_role_only":
        routines = [row for row in rows if row["routine_name"] == "exec_sql"]
        expected = contract["acl_policy"]["exec_sql_contract"]
        if len(routines) > expected["maximum_overloads"]:
            _fail("exec_sql overload is not unique")
        if routines:
            row = routines[0]
            exact = {
                "schema_name": row["schema_name"], "routine_name": row["routine_name"],
                "identity_arguments": row["identity_arguments"], "result_type": row["result_type"],
                "owner_name": row["owner_name"], "language_name": row["language_name"],
                "security_definer": row["security_definer"], "runtime_settings": row["runtime_settings"],
            }
            if exact != {key: expected[key] for key in exact}:
                _fail("exec_sql signature, owner, result, security mode, or search path drifted")
        return "EXEC_SQL_METADATA_RESTRICTED" if routines else "EXEC_SQL_METADATA_ABSENT"
    if predicate == "public_views_security_invoker" and any(row["schema_name"] == "public" and "security_invoker=true" not in row["security_options"] for row in rows):
        _fail("public view is not security-invoker")
    if predicate == "public_views_security_invoker":
        return f"PUBLIC_VIEWS_SECURITY_INVOKER_{sum(1 for row in rows if row['schema_name'] == 'public')}"
    if predicate == "publication_settings_classified":
        return f"PUBLICATIONS_CLASSIFIED_{len(rows)}"
    if predicate == "public_schema_document_classified":
        if len(rows) != 1 or not rows[0]["openapi_version"] or rows[0]["path_count"] < 0 or rows[0]["definition_count"] < 0:
            _fail("PostgREST public schema projection is malformed")
        return "PUBLIC_SCHEMA_DOCUMENT_CLASSIFIED"
    return "ACCEPTED"


def validate_query_replay(contract: Mapping[str, Any], query_id: str, pages: Sequence[Mapping[str, Any]]) -> QueryReplaySummary:
    validated = validate_contract_shape(contract)
    queries = {item["id"]: item for item in validated["query_catalog"]}
    if query_id not in queries:
        _fail("query is not enumerated")
    query = queries[query_id]
    rows = _validate_pages(query, pages, query["result_shape"])
    classification = _acceptance(validated, query, rows)
    timeout_digest = canonical_json_sha256(validated["transaction_policy"]["adapter_command_sequence"])
    return QueryReplaySummary(query_id, len(pages), len(rows), classification, canonical_json_sha256(pages), timeout_digest)


def validate_http_observation(contract: Mapping[str, Any], operation_id: str, pages: Sequence[Mapping[str, Any]]) -> HttpObservationSummary:
    validated = validate_contract_shape(contract)
    operations = {item["id"]: item for item in validated["http_catalog"]}
    if operation_id not in operations:
        _fail("HTTP operation is not enumerated")
    operation = operations[operation_id]
    rows = _validate_pages(operation, pages, operation["response_shape"])
    query_equivalent = {"acceptance": {"predicate": operation["acceptance_predicate"]}}
    _acceptance(validated, query_equivalent, rows)
    return HttpObservationSummary(operation_id, len(pages), len(rows), canonical_json_sha256(pages))


def validate_tool_observation(contract: Mapping[str, Any], observation: Any) -> ToolObservationSummary:
    validated = validate_contract_shape(contract)
    value = _exact_keys(observation, {"tool_id", "item_count", "levels_sha256", "payload_sha256"}, "tool observation")
    tools = {item["id"]: item for item in validated["tool_catalog"]}
    if value["tool_id"] not in tools:
        _fail("tool observation is not enumerated")
    count = _integer(value["item_count"], "tool item count")
    _digest(value["levels_sha256"], "tool levels digest")
    _digest(value["payload_sha256"], "tool payload digest")
    return ToolObservationSummary(value["tool_id"], count, canonical_json_sha256(value))


def validate_local_capability(contract: Mapping[str, Any], capability_id: str, classification: str) -> LocalCapabilitySummary:
    validated = validate_contract_shape(contract)
    capabilities = {item["id"]: item for item in validated["local_capability_catalog"]}
    if capability_id not in capabilities or classification != capabilities[capability_id]["required_classification"]:
        _fail("local capability classification is not exact")
    payload = {"capability_id": capability_id, "classification": classification}
    return LocalCapabilitySummary(capability_id, classification, canonical_json_sha256(payload))


def validate_evidence_structure(contract: Mapping[str, Any], evidence: Any) -> None:
    """Validate a sanitized future F9.4 envelope without deriving any capability."""
    schema = validate_contract_shape(contract)["evidence_schema"]
    if not isinstance(evidence, dict) or evidence.get("status") not in {"PASS", "FAIL"}:
        _fail("future evidence status or representation is invalid")
    expected = set(schema["pass_fields"] if evidence["status"] == "PASS" else schema["fail_fields"])
    _exact_keys(evidence, expected, "future evidence")
    if type(evidence["schema_version"]) is not int or evidence["schema_version"] != schema["schema_version"]:
        _fail("future evidence schema version is invalid")
    for field in schema["count_fields"]:
        _integer(evidence[field], f"future evidence {field}")
    for field in schema["digest_fields"]:
        _digest(evidence[field], f"future evidence {field}")
    if evidence["status"] == "FAIL":
        if evidence["failure_code"] not in schema["failure_codes"]:
            _fail("future evidence failure code is not enumerated")
        _digest(evidence["failed_operation_id_sha256"], "failed operation id digest")
    return None


def validate_sql_trace_structure(contract: Mapping[str, Any], trace: Any) -> None:
    validated = validate_contract_shape(contract)
    schema = validated["trace_schemas"]["sql"]
    value = _exact_keys(trace, set(schema["exact_fields"]), "SQL raw trace")
    if type(value["schema_version"]) is not int or value["schema_version"] != schema["schema_version"]:
        _fail("SQL trace schema version is invalid")
    for field in ("target_identity_sha256", "session_id_sha256", "command_sequence_sha256"):
        _digest(value[field], f"SQL trace {field}")
    expected_commands = canonical_json_sha256(validated["transaction_policy"]["adapter_command_sequence"])
    if value["command_sequence_sha256"] != expected_commands:
        _fail("SQL trace command sequence drifted")
    query_ids = [item["id"] for item in validated["query_catalog"]]
    if value["query_ids"] != query_ids:
        _fail("SQL trace query order drifted")
    pages = value["query_page_digests"]
    if not isinstance(pages, list) or [item.get("query_id") for item in pages] != query_ids:
        _fail("SQL trace page inventory is incomplete")
    for item in pages:
        _exact_keys(item, {"query_id", "page_count", "pages_sha256"}, "SQL trace query pages")
        _integer(item["page_count"], "SQL trace page count", minimum=1)
        _digest(item["pages_sha256"], "SQL trace pages digest")
    if value["timeout_settings"] != {"statement_timeout_ms": 5000, "lock_timeout_ms": 1000, "idle_in_transaction_timeout_ms": 10000}:
        _fail("SQL trace timeout settings drifted")
    if type(value["rollback_completed"]) is not bool or not value["rollback_completed"]:
        _fail("SQL trace lacks rollback completion")
    return None


def validate_http_trace_structure(contract: Mapping[str, Any], trace: Any) -> None:
    validated = validate_contract_shape(contract)
    schema = validated["trace_schemas"]["http"]
    value = _exact_keys(trace, set(schema["exact_fields"]), "HTTP raw trace")
    if type(value["schema_version"]) is not int or value["schema_version"] != schema["schema_version"]:
        _fail("HTTP trace schema version is invalid")
    operation = validated["http_catalog"][0]
    for field in ("target_identity_sha256", "pages_sha256"):
        _digest(value[field], f"HTTP trace {field}")
    expected = {
        "operation_id": operation["id"], "method": operation["method"],
        "origin_binding": operation["service_origin_binding"], "path": operation["path_template"],
        "query_parameter_names": [item["name"] for item in operation["query_parameters"]],
        "header_names": operation["header_names"], "auth_class": operation["auth_class"],
    }
    if any(value[field] != expected[field] for field in expected):
        _fail("HTTP trace request metadata drifted")
    if (
        value["status_code"] != 200 or value["redirected"] is not False
        or value["request_body_present"] is not False
        or value["content_type"] != operation["response_content_type"]
    ):
        _fail("HTTP trace response metadata is unsafe")
    _integer(value["response_size_bytes"], "HTTP response size")
    _integer(value["page_count"], "HTTP page count", minimum=1)
    return None


def validate_tool_trace_structure(contract: Mapping[str, Any], trace: Any) -> None:
    validated = validate_contract_shape(contract)
    schema = validated["trace_schemas"]["tool"]
    value = _exact_keys(trace, set(schema["exact_fields"]), "tool raw trace")
    if type(value["schema_version"]) is not int or value["schema_version"] != schema["schema_version"]:
        _fail("tool trace schema version is invalid")
    tools = {item["id"]: item for item in validated["tool_catalog"]}
    if value["tool_id"] not in tools:
        _fail("tool trace identity is not enumerated")
    tool = tools[value["tool_id"]]
    if (
        value["adapter_identity"] != tool["adapter_identity"]
        or value["arguments"] != tool["arguments"]
        or value["project_binding"] != tool["project_binding"]
        or value["timeout_ms"] != tool["timeout_ms"]
        or value["response_projection"] != tool["response_projection"]
    ):
        _fail("tool trace metadata drifted")
    for field in ("target_identity_sha256", "project_identity_sha256", "response_sha256"):
        _digest(value[field], f"tool trace {field}")
    _integer(value["item_count"], "tool trace item count")
    return None


def _synthetic_row(query: Mapping[str, Any], index: int = 0) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for column in query["result_shape"]:
        name = column["name"]
        if column["type"] == "boolean":
            row[name] = True
        elif column["type"] == "integer":
            row[name] = index + 1
        else:
            row[name] = f"synthetic_{index:04d}_{name}"
    predicate = query["acceptance"]["predicate"]
    if predicate == "owner_and_rls_classified":
        row.update(relation_kind="r", owner_name="synthetic_owner")
    elif predicate == "policy_roles_classified":
        row.update(roles="{service_role}", command="SELECT")
    elif predicate == "all_constraints_validated":
        row["validated"] = True
    elif predicate == "no_public_schema_create":
        row.update(grantee="service_role", privilege_type="CREATE", is_grantable=False)
    elif predicate == "package_table_acl_allowlist":
        row.update(schema_name="public", object_name="leads", grantee="anon", privilege_type="INSERT", is_grantable=False)
    elif predicate == "package_column_acl_allowlist":
        row.update(schema_name="public", object_name="courses", column_name="id", grantee="anon", privilege_type="SELECT", is_grantable=False)
    elif predicate == "exec_sql_absent_or_service_role_only":
        row.update(routine_name="safe_fixture", identity_arguments="", language_name="plpgsql", security_definer=False, runtime_settings="search_path=\"\"", owner_name="postgres", result_type="boolean")
    elif predicate == "exec_sql_execute_service_role_only":
        row.update(routine_name="safe_fixture", identity_arguments="", grantee="service_role", privilege_type="EXECUTE", is_grantable=False)
    elif predicate == "public_views_security_invoker":
        row.update(schema_name="public", security_options="security_invoker=true")
    return row


def _single_page(operation: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operation_id": operation["id"], "page_index": 0, "request_cursor": None,
        "request_offset": None if operation["pagination"]["mode"] == "keyset" else 0,
        "total_count": 1, "start_index": 0, "end_index": 0,
        "server_timeout_ms": operation["timeout_ms"], "timeout_enforced": True, "rows": [dict(row)],
    }


def run_synthetic_self_test(contract: Mapping[str, Any]) -> tuple[int, str]:
    validated = validate_contract_shape(contract)
    summaries = []
    for query in validated["query_catalog"]:
        if query["id"] == "migration_ledger":
            row = {"migration_name": validated["package_binding"]["entries"][0]["migration_name"], "checksum_marker": "sha256:" + validated["package_binding"]["entries"][0]["sha256"]}
            pages = [_single_page(query, row)]
        elif query["id"] == "catalog_sequence_grants":
            pages = [{**_single_page(query, _synthetic_row(query)), "total_count": 0, "start_index": None, "end_index": None, "rows": []}]
        else:
            row = _synthetic_row(query)
            pages = [_single_page(query, row)]
        summaries.append(validate_query_replay(validated, query["id"], pages))
    http = validated["http_catalog"][0]
    http_row = {"openapi_version": "3.0.0", "path_count": 1, "definition_count": 1}
    http_summary = validate_http_observation(validated, http["id"], [_single_page(http, http_row)])
    tools = [validate_tool_observation(validated, {"tool_id": item["id"], "item_count": 0, "levels_sha256": "0" * 64, "payload_sha256": "1" * 64}) for item in validated["tool_catalog"]]
    local = [validate_local_capability(validated, item["id"], item["required_classification"]) for item in validated["local_capability_catalog"]]
    digest = canonical_json_sha256({
        "queries": [item.observation_sha256 for item in summaries],
        "http": http_summary.observation_sha256,
        "tools": [item.observation_sha256 for item in tools],
        "local": [item.observation_sha256 for item in local],
        "commands": [item.__dict__ for item in catalog_adapter_commands(validated)],
    })
    return len(summaries) + 1 + len(tools) + len(local) + 1, digest


def _parse_cli(argv: Sequence[str]) -> tuple[str, str]:
    if len(argv) != 3 or argv[0] != "--contract" or argv[2] not in {"--validate-only", "--synthetic-self-test"}:
        _fail("CLI is restricted to two local modes")
    return argv[1], argv[2]


def main(argv: Sequence[str] | None = None) -> int:
    try:
        contract_path, mode = _parse_cli(tuple(sys.argv[1:] if argv is None else argv))
        contract = load_contract(contract_path)
        files = validate_contract_files(contract)
        if mode == "--validate-only":
            print(
                "F9_3_CONTRACT status=LOCAL_VALID git_proof=EXTERNAL_REQUIRED "
                f"queries={len(contract['query_catalog'])} contract_sha256={files.contract_sha256} "
                f"implementation_sha256={files.implementation_sha256}"
            )
        else:
            checks, digest = run_synthetic_self_test(contract)
            print(
                "F9_3_SYNTHETIC status=LOCAL_VALID git_proof=EXTERNAL_REQUIRED "
                f"checks={checks} replay_sha256={digest}"
            )
        return 0
    except (PreflightContractError, OSError, ValueError, TypeError, KeyError):
        print("F9_3_CONTRACT git_proof=EXTERNAL_REQUIRED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
