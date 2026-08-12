#!/usr/bin/env python3
"""F10.10/M3 fail-closed, read-only PostgreSQL metadata collector.

The module deliberately has no import-time database dependency.  Production
connections are created only by :func:`default_connection_factory`; tests inject
an offline factory.  Sanitized output is built from an allowlist and never
contains database values or exception text.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import urlsplit


COLLECTOR_VERSION = "f10.10-m3-readonly-collector-v2"
CANONICAL_VERSION = "f10.10-m3-canonical-v2"
NORMALIZATION_VERSION = "f10.9-metadata-v2"
HOST_NORMALIZATION_VERSION = "f10.10-m3-host-v1"
SQL_HOST_NORMALIZATION_VERSION = "f10.10-m3-sql-host-v1"
TARGET_BINDING_VERSION = "f10.10-m3-target-binding-v2"
OBSERVED_TRANSPORT_VERSION = "f10.10-m3-observed-transport-v2"
PAGE_SIZE = 500
CATALOG_FETCH_SIZE = 16
MAX_ROWS = 10_000
MAX_STRING_CHARS = 32_768
MAX_CATALOG_ROWS = 50_000
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_PREDECESSOR_BYTES = 1024 * 1024
MAX_REMOTE_UTF8_BYTES = 16 * 1024 * 1024
MAX_CA_BYTES = 8 * 1024 * 1024
MAX_TRANSPORT_ATTRIBUTE_CHARS = 256
MIN_VALID_UNTIL_EPOCH = 0
MAX_VALID_UNTIL_EPOCH = 253_402_300_799
CONNECT_TIMEOUT_SECONDS = 10
TIMEOUT_MILLISECONDS = 60_000
PSYCOPG2_VERSION = "2.9.12"
ARTIFACT_ROOT_RELATIVE = Path("local/f10_10/m3")
QUERY_SET_FILES = (
    "scripts/maintenance/f10_10_m3_readonly_collector.py",
    "tests/test_f10_10_m3_readonly_collector.py",
)

BEGIN_SQL = "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
COMMIT_SQL = "COMMIT"

Q0_SQL = """select
  session_user,
  current_user,
  current_database(),
  current_setting('transaction_read_only') as transaction_read_only,
  current_setting('default_transaction_read_only') as default_transaction_read_only,
  current_setting('search_path') as effective_search_path,
  current_setting('client_encoding') as client_encoding,
  r.rolsuper,
  r.rolbypassrls,
  r.rolcreaterole,
  r.rolcreatedb,
  r.rolcanlogin,
  r.rolinherit,
  r.rolreplication,
  r.rolconnlimit,
  extract(epoch from r.rolvaliduntil)::bigint as rolvaliduntil_epoch,
  r.rolvaliduntil > pg_catalog.statement_timestamp() as rolvaliduntil_is_future,
  exists (select 1 from pg_catalog.pg_auth_members as m where m.member = r.oid) as is_member_of_roles,
  (select count(*) from pg_catalog.pg_auth_members as m where m.roleid = r.oid) as role_member_count,
  (select member_role.rolname::text
   from pg_catalog.pg_auth_members as m
   join pg_catalog.pg_roles as member_role on member_role.oid = m.member
   where m.roleid = r.oid order by member_role.rolname::text limit 1) as member_role_name,
  (select m.admin_option from pg_catalog.pg_auth_members as m
   where m.roleid = r.oid order by m.member limit 1) as member_admin_option,
  (select m.inherit_option from pg_catalog.pg_auth_members as m
   where m.roleid = r.oid order by m.member limit 1) as member_inherit_option,
  (select m.set_option from pg_catalog.pg_auth_members as m
   where m.roleid = r.oid order by m.member limit 1) as member_set_option,
  c.relrowsecurity,
  c.relforcerowsecurity,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'SELECT') as has_table_select,
  pg_catalog.has_column_privilege(current_user, 'public.courses', 'id', 'SELECT') as can_select_id,
  pg_catalog.has_column_privilege(current_user, 'public.courses', 'is_active', 'SELECT') as can_select_is_active,
  pg_catalog.has_column_privilege(current_user, 'public.courses', 'syllabus', 'SELECT') as can_select_syllabus,
  pg_catalog.has_column_privilege(current_user, 'public.courses', 'objectives', 'SELECT') as can_select_objectives,
  exists (
    select 1 from pg_catalog.pg_attribute as a
    where a.attrelid = 'public.courses'::regclass and a.attnum > 0 and not a.attisdropped
      and a.attname not in ('id', 'is_active', 'syllabus', 'objectives')
      and pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'SELECT')
  ) as has_other_select,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'INSERT') as can_insert,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'UPDATE') as can_update,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'DELETE') as can_delete,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'TRUNCATE') as can_truncate,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'REFERENCES') as can_reference,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'TRIGGER') as can_trigger,
  exists (
    select 1 from pg_catalog.pg_attribute as a
    where a.attrelid = 'public.courses'::regclass and a.attnum > 0 and not a.attisdropped
      and (pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'INSERT')
        or pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'UPDATE')
        or pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'REFERENCES'))
  ) as has_mutating_column_privilege,
  exists (
    select 1
    from pg_catalog.pg_proc as p
    join pg_catalog.pg_namespace as n on n.oid = p.pronamespace
    where p.prosecdef
      and n.nspname not in ('pg_catalog', 'information_schema')
      and n.nspname !~ '^pg_toast'
      and pg_catalog.has_function_privilege(current_user, p.oid, 'EXECUTE')
  ) as can_execute_non_system_security_definer
from pg_catalog.pg_roles as r
join pg_catalog.pg_class as c on c.oid = 'public.courses'::regclass
where r.rolname = current_user"""

Q1_SQL = """select
  a.attname as column_name,
  pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
  a.attnotnull as not_null,
  pg_catalog.pg_get_expr(d.adbin, d.adrelid) as default_expression
from pg_catalog.pg_attribute as a
left join pg_catalog.pg_attrdef as d on d.adrelid = a.attrelid and d.adnum = a.attnum
where a.attrelid = 'public.courses'::regclass and a.attnum > 0 and not a.attisdropped
  and a.attname in ('id', 'is_active', 'syllabus', 'objectives')
order by a.attnum"""

# key_columns is structural (conkey ordinal order), never parsed from rendered SQL.
Q2_SQL = """select
  c.conname,
  c.contype,
  pg_catalog.pg_get_constraintdef(c.oid, true) as constraint_definition,
  case when c.contype = 'p' then k.ordinality::integer else null end as key_ordinality,
  case when c.contype = 'p' then a.attname else null end as key_column_name
from pg_catalog.pg_constraint as c
left join lateral unnest(c.conkey) with ordinality as k(attnum, ordinality) on true
left join pg_catalog.pg_attribute as a on a.attrelid = c.conrelid and a.attnum = k.attnum
where c.conrelid = 'public.courses'::regclass
  and (c.contype = 'p' or pg_catalog.pg_get_constraintdef(c.oid, true) ~* '(syllabus|objectives)')
order by c.conname, k.ordinality nulls first"""

Q3_SQL = """select
  t.oid as trigger_oid, t.tgname, pg_catalog.pg_get_triggerdef(t.oid, true),
  p.oid as function_oid, p.proname, pg_catalog.pg_get_functiondef(p.oid)
from pg_catalog.pg_trigger as t
join pg_catalog.pg_proc as p on p.oid = t.tgfoid
where t.tgrelid = 'public.courses'::regclass
order by t.tgname, p.proname, t.oid"""

Q3_ROUTINES_SQL = """select
  n.nspname, p.proname, p.prokind, l.lanname,
  pg_catalog.pg_get_function_identity_arguments(p.oid), pg_catalog.pg_get_functiondef(p.oid)
from pg_catalog.pg_proc as p
join pg_catalog.pg_namespace as n on n.oid = p.pronamespace
join pg_catalog.pg_language as l on l.oid = p.prolang
where n.nspname not in ('pg_catalog', 'information_schema') and n.nspname !~ '^pg_toast'
  and p.prokind in ('f', 'p', 'w')
order by n.nspname, p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid)"""

Q3_EXTENSIONS_SQL = """select e.extname, e.extversion, n.nspname
from pg_catalog.pg_extension as e
join pg_catalog.pg_namespace as n on n.oid = e.extnamespace
order by e.extname"""

Q3_AGGREGATES_SQL = """select
  n.nspname, p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid),
  pg_catalog.pg_get_function_result(p.oid), a.aggkind, a.aggnumdirectargs,
  a.aggtransfn::regprocedure::text, a.aggfinalfn::regprocedure::text,
  a.aggcombinefn::regprocedure::text, a.aggserialfn::regprocedure::text,
  a.aggdeserialfn::regprocedure::text, pg_catalog.format_type(a.aggtranstype, null),
  a.aggtransspace, a.aggmtransfn::regprocedure::text, a.aggminvtransfn::regprocedure::text,
  a.aggmfinalfn::regprocedure::text, pg_catalog.format_type(a.aggmtranstype, null),
  a.aggmtransspace, a.aggfinalextra, a.aggmfinalextra, a.aggfinalmodify,
  a.aggmfinalmodify, a.agginitval, a.aggminitval, onsp.nspname, o.oprname,
  olnsp.nspname, olt.typname, ornsp.nspname, ort.typname
from pg_catalog.pg_aggregate as a
join pg_catalog.pg_proc as p on p.oid = a.aggfnoid
join pg_catalog.pg_namespace as n on n.oid = p.pronamespace
left join pg_catalog.pg_operator as o on o.oid = a.aggsortop
left join pg_catalog.pg_namespace as onsp on onsp.oid = o.oprnamespace
left join pg_catalog.pg_type as olt on olt.oid = o.oprleft
left join pg_catalog.pg_namespace as olnsp on olnsp.oid = olt.typnamespace
left join pg_catalog.pg_type as ort on ort.oid = o.oprright
left join pg_catalog.pg_namespace as ornsp on ornsp.oid = ort.typnamespace
where n.nspname not in ('pg_catalog', 'information_schema') and n.nspname !~ '^pg_toast'
order by n.nspname, p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid)"""

Q3_EXTENSION_MEMBERS_SQL = """select
  e.extname, d.classid::regclass::text, d.objid, d.objsubid
from pg_catalog.pg_depend as d
join pg_catalog.pg_extension as e on e.oid = d.refobjid
where d.refclassid = 'pg_catalog.pg_extension'::regclass and d.deptype = 'e'
order by e.extname, d.classid::regclass::text, d.objid, d.objsubid"""

Q4_FIRST_SQL = """select id, is_active, syllabus, objectives
from public.courses
order by id asc
limit 500"""

Q4_NEXT_SQL = """select id, is_active, syllabus, objectives
from public.courses
where id > %s
order by id asc
limit 500"""

CATALOG_QUERIES = (
    ("schema", Q1_SQL),
    ("constraints", Q2_SQL),
    ("triggers", Q3_SQL),
    ("routines", Q3_ROUTINES_SQL),
    ("extensions", Q3_EXTENSIONS_SQL),
    ("aggregates", Q3_AGGREGATES_SQL),
    ("extension_members", Q3_EXTENSION_MEMBERS_SQL),
)
STATIC_SQL = frozenset(
    [BEGIN_SQL, COMMIT_SQL, Q0_SQL, Q4_FIRST_SQL, Q4_NEXT_SQL]
    + [sql for _, sql in CATALOG_QUERIES]
)
QUERY_IDS = {
    BEGIN_SQL: "TX_BEGIN", COMMIT_SQL: "TX_COMMIT", Q0_SQL: "Q0",
    Q1_SQL: "Q1", Q2_SQL: "Q2", Q3_SQL: "Q3",
    Q3_ROUTINES_SQL: "Q3B_ROUTINES", Q3_EXTENSIONS_SQL: "Q3B_EXTENSIONS",
    Q3_AGGREGATES_SQL: "Q3B_AGGREGATES",
    Q3_EXTENSION_MEMBERS_SQL: "Q3B_EXTENSION_MEMBERS",
    Q4_FIRST_SQL: "Q4_FIRST", Q4_NEXT_SQL: "Q4_NEXT",
}


class CollectorError(Exception):
    """Expected fail-closed result carrying only a stable public reason code."""

    def __init__(self, reason_code: str, *, decision: str = "STOP") -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.decision = decision
        self.partial_private: dict[str, Any] | None = None


@dataclass(frozen=True)
class Config:
    target_alias: str
    approval_id: str
    api_url: str
    project_ref: str
    sql_host: str
    sql_port: int
    database: str
    user: str
    password: str | None
    ca_file: Path
    ca_sha256: str
    valid_until_epoch: int
    provisioner: str


@dataclass(frozen=True)
class Snapshot:
    private_rows: list[list[Any]]
    summary: dict[str, Any]
    q0_attestation: list[Any]


@dataclass(frozen=True)
class CollectionResult:
    private: dict[str, Any]
    manifest: dict[str, Any]


@dataclass(frozen=True)
class PinnedCA:
    fd: int
    proc_path: str
    digest: str


@dataclass
class RemoteBudget:
    used: int = 0
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.limit is None:
            self.limit = MAX_REMOTE_UTF8_BYTES

    def consume(self, value: Any) -> None:
        if value is None:
            size = 0
        elif isinstance(value, bool):
            size = 4 if value else 5
        elif isinstance(value, (int, uuid.UUID)):
            size = len(str(value).encode("utf-8"))
        elif isinstance(value, str):
            size = len(_checked_string(value).encode("utf-8"))
        elif isinstance(value, (tuple, list)):
            for item in value:
                self.consume(item)
            return
        else:
            raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT")
        if self.limit is None or self.used + size > self.limit:
            raise CollectorError("STOP_REMOTE_BYTE_LIMIT")
        self.used += size


@dataclass
class PrivateEvidence:
    transcript: list[dict[str, Any]]
    page_boundaries: list[dict[str, Any]]
    transaction: int = 0

    @classmethod
    def create(cls) -> "PrivateEvidence":
        return cls([], [])


ConnectionFactory = Callable[[Config, PinnedCA], Any]


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT") from exc


def envelope_digest(domain: str, payload: Any) -> str:
    version = 1
    if domain in {"target-binding-v2", "observed-transport-v2"}:
        version = 2
    elif domain not in {
        "total-ids-v1", "active-ids-v1", "snapshot-raw-v1",
        "snapshot-normalized-v1", "cohort-v1", "schema-v1",
        "constraints-v1", "triggers-v1", "query-set-v1",
    }:
        raise CollectorError("STOP_INTERNAL_CONTRACT")
    encoded = canonical_json({"domain": domain, "version": version, "payload": payload})
    digest = hashlib.sha256()
    digest.update(f"f10.10-m3:{domain}\n".encode("ascii"))
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _plain_sha256(prefix: bytes, value: str) -> str:
    return "sha256:" + hashlib.sha256(prefix + value.encode("utf-8")).hexdigest()


def _checked_string(value: Any) -> str:
    if not isinstance(value, str) or len(value) > MAX_STRING_CHARS:
        raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT") from exc
    return value


def tagged(value: Any) -> list[Any]:
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["boolean", value]
    if isinstance(value, int):
        return ["integer", str(value)]
    if isinstance(value, str):
        return ["string", _checked_string(value)]
    raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT")


def typed_uuid(value: Any) -> list[str]:
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise CollectorError("STOP_SCHEMA_DRIFT") from exc
    canonical = str(parsed)
    if isinstance(value, str) and value.lower() != canonical:
        raise CollectorError("STOP_SCHEMA_DRIFT")
    return ["uuid", canonical]


def normalize_metadata(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", _checked_string(value))
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")
    return " ".join(normalized.split()).casefold()


def normalized_tag(value: Any) -> list[Any]:
    if value is None:
        return ["null"]
    text = normalize_metadata(value) if isinstance(value, str) else None
    if text is None:
        raise CollectorError("STOP_UNTRUSTED_REMOTE_CONTENT")
    if text in {"", "n/a", "none", "por definir"}:
        return ["null"]
    return ["string", text]


def _normalize_file(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CollectorError("STOP_QUERY_SET_INVALID")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise CollectorError("STOP_QUERY_SET_INVALID") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def query_set_payload(workspace: Path) -> dict[str, Any]:
    files: list[list[str]] = []
    for relative in sorted(QUERY_SET_FILES):
        path = workspace / relative
        try:
            text = _normalize_file(path.read_bytes())
        except OSError as exc:
            raise CollectorError("STOP_QUERY_SET_INVALID") from exc
        per_file = hashlib.sha256(text.encode("utf-8")).hexdigest()
        files.append([relative, per_file, text])
    return {"collector_version": COLLECTOR_VERSION, "files": files}


def query_set_digest(workspace: Path) -> str:
    return envelope_digest("query-set-v1", query_set_payload(workspace))


def _normalize_hostname(value: str, reason: str) -> str:
    if not value or any(ch in value for ch in "/@?#:\\\x00\r\n"):
        raise CollectorError(reason)
    try:
        host = value.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise CollectorError(reason) from exc
    if not host or len(host) > 253 or any(not label for label in host.split(".")):
        raise CollectorError(reason)
    return host


def normalize_api_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme.lower() != "https" or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")
            or parsed.port not in (None, 443) or not parsed.hostname
        ):
            raise ValueError
        return _normalize_hostname(parsed.hostname, "STOP_TARGET_MISMATCH")
    except (ValueError, UnicodeError) as exc:
        raise CollectorError("STOP_TARGET_MISMATCH") from exc


def _env_required(env: dict[str, str], name: str) -> str:
    value = env.get(name)
    if value is None or value == "" or "\x00" in value or "\r" in value or "\n" in value:
        raise CollectorError("STOP_CONFIG_INVALID")
    return value


def _parse_valid_until_epoch(value: str) -> int:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        raise CollectorError("STOP_CONFIG_INVALID")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        epoch = calendar.timegm(parsed.utctimetuple())
    except (OverflowError, ValueError) as exc:
        raise CollectorError("STOP_CONFIG_INVALID") from exc
    if (
        parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value
        or epoch < MIN_VALID_UNTIL_EPOCH
        or epoch > MAX_VALID_UNTIL_EPOCH
    ):
        raise CollectorError("STOP_CONFIG_INVALID")
    return epoch


def _parse_role_name(value: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", value):
        raise CollectorError("STOP_CONFIG_INVALID")
    if len(value.encode("ascii")) > 63:
        raise CollectorError("STOP_CONFIG_INVALID")
    return value


def load_config(
    env: dict[str, str], target_alias: str, approval_id: str, *,
    require_password: bool = True,
) -> Config:
    if (
        target_alias != "FREE_DB"
        or not re.fullmatch(r"(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9][A-Za-z0-9._:-]{15,127}", approval_id)
    ):
        raise CollectorError("STOP_CONFIG_INVALID")
    try:
        port = int(_env_required(env, "F10_10_M3_SQL_PORT"))
    except ValueError as exc:
        raise CollectorError("STOP_CONFIG_INVALID") from exc
    if port != 5432:
        raise CollectorError("STOP_CONFIG_INVALID")
    ca_sha = _env_required(env, "F10_10_M3_CA_SHA256").lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ca_sha):
        raise CollectorError("STOP_CONFIG_INVALID")
    project_ref = _env_required(env, "F10_10_M3_PROJECT_REF").lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])", project_ref):
        raise CollectorError("STOP_CONFIG_INVALID")
    api_url = _env_required(env, "F10_10_M3_API_URL")
    api_host = normalize_api_url(api_url)
    if api_host.split(".", 1)[0] != project_ref:
        raise CollectorError("STOP_TARGET_MISMATCH")
    sql_host = _normalize_hostname(
        _env_required(env, "F10_10_M3_SQL_HOST"), "STOP_CONFIG_INVALID"
    )
    if sql_host != f"db.{project_ref}.supabase.co":
        raise CollectorError("STOP_TARGET_MISMATCH")
    ca_file = Path(_env_required(env, "F10_10_M3_CA_FILE"))
    if not ca_file.is_absolute():
        raise CollectorError("STOP_CONFIG_INVALID")
    valid_until_epoch = _parse_valid_until_epoch(
        _env_required(env, "F10_10_M3_VALID_UNTIL")
    )
    provisioner = _parse_role_name(_env_required(env, "F10_10_M3_PROVISIONER"))
    return Config(
        target_alias=target_alias,
        approval_id=approval_id,
        api_url=api_url,
        project_ref=project_ref,
        sql_host=sql_host,
        sql_port=port,
        database=_env_required(env, "F10_10_M3_DATABASE"),
        user=_env_required(env, "F10_10_M3_USER"),
        password=(
            _env_required(env, "F10_10_M3_PASSWORD")
            if require_password else None
        ),
        ca_file=ca_file,
        ca_sha256=ca_sha,
        valid_until_epoch=valid_until_epoch,
        provisioner=provisioner,
    )


@contextmanager
def open_pinned_ca(config: Config) -> Iterable[PinnedCA]:
    if (
        sys.platform != "linux" or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "memfd_create") or not hasattr(os, "MFD_ALLOW_SEALING")
        or not Path("/proc/self/fd").is_dir()
    ):
        raise CollectorError("STOP_UNSUPPORTED_PLATFORM")
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    source_fd: int | None = None
    memfd: int | None = None
    try:
        source_fd = os.open(config.ca_file, flags)
        metadata = os.fstat(source_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > MAX_CA_BYTES:
            raise CollectorError("STOP_TLS_CONTRACT")
        digest = hashlib.sha256()
        contents = bytearray()
        total = 0
        while True:
            chunk = os.read(source_fd, 64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_CA_BYTES:
                raise CollectorError("STOP_TLS_CONTRACT")
            digest.update(chunk)
            contents.extend(chunk)
        actual = "sha256:" + digest.hexdigest()
        if actual != config.ca_sha256:
            raise CollectorError("STOP_TLS_CONTRACT")
        import fcntl  # Linux-only and deliberately lazy.

        memfd = os.memfd_create(
            "f10_10_m3_approved_ca", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING
        )
        view = memoryview(contents)
        while view:
            written = os.write(memfd, view)
            if written <= 0:
                raise OSError("short memfd write")
            view = view[written:]
        os.lseek(memfd, 0, os.SEEK_SET)
        required_seals = (
            fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK
            | fcntl.F_SEAL_SEAL
        )
        fcntl.fcntl(memfd, fcntl.F_ADD_SEALS, required_seals)
        observed_seals = fcntl.fcntl(memfd, fcntl.F_GET_SEALS)
        if observed_seals & required_seals != required_seals:
            raise CollectorError("STOP_TLS_CONTRACT")
        yield PinnedCA(memfd, f"/proc/self/fd/{memfd}", actual)
    except CollectorError:
        raise
    except (ImportError, OSError) as exc:
        raise CollectorError("STOP_TLS_CONTRACT") from exc
    finally:
        if source_fd is not None:
            try:
                os.close(source_fd)
            except OSError:
                pass
        if memfd is not None:
            try:
                os.close(memfd)
            except OSError:
                pass


def verify_pinned_ca(pinned_ca: PinnedCA) -> None:
    try:
        os.lseek(pinned_ca.fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(pinned_ca.fd, 64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_CA_BYTES:
                raise CollectorError("STOP_TLS_CONTRACT")
            digest.update(chunk)
        os.lseek(pinned_ca.fd, 0, os.SEEK_SET)
        if "sha256:" + digest.hexdigest() != pinned_ca.digest:
            raise CollectorError("STOP_TLS_CONTRACT")
    except CollectorError:
        raise
    except OSError as exc:
        raise CollectorError("STOP_TLS_CONTRACT") from exc


def default_connection_factory(config: Config, pinned_ca: PinnedCA) -> Any:
    """Create the sole production connection; psycopg2 remains a lazy import."""
    if config.password is None:
        raise CollectorError("STOP_CONFIG_INVALID")
    try:
        import psycopg2  # type: ignore
    except ImportError as exc:
        raise CollectorError("STOP_DRIVER_UNAVAILABLE") from exc
    runtime_version = getattr(psycopg2, "__version__", None)
    if not isinstance(runtime_version, str) or runtime_version.split()[0] != PSYCOPG2_VERSION:
        raise CollectorError("STOP_DRIVER_VERSION")
    options = (
        "-c search_path=pg_catalog "
        "-c client_encoding=UTF8 "
        f"-c statement_timeout={TIMEOUT_MILLISECONDS} "
        f"-c lock_timeout={TIMEOUT_MILLISECONDS} "
        f"-c idle_in_transaction_session_timeout={TIMEOUT_MILLISECONDS}"
    )
    try:
        connection = psycopg2.connect(
            host=config.sql_host,
            port=config.sql_port,
            dbname=config.database,
            user=config.user,
            password=config.password,
            sslmode="verify-full",
            sslrootcert=pinned_ca.proc_path,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
            options=options,
        )
        connection.autocommit = True
        return connection
    except Exception as exc:
        raise CollectorError("STOP_CONNECTION_FAILED") from exc


def _transport_attribute(value: Any) -> str:
    if (
        not isinstance(value, str) or not value
        or len(value) > MAX_TRANSPORT_ATTRIBUTE_CHARS
        or any(unicodedata.category(character).startswith("C") for character in value)
    ):
        raise CollectorError("STOP_TLS_CONTRACT")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise CollectorError("STOP_TLS_CONTRACT") from exc
    return value


def observed_transport_attestation(
    connection: Any, config: Config,
) -> tuple[dict[str, Any], str]:
    try:
        info = connection.info
        observed = {
            "ssl_in_use": info.ssl_in_use,
            "protocol": _transport_attribute(info.ssl_attribute("protocol")),
            "cipher": _transport_attribute(info.ssl_attribute("cipher")),
            "library": _transport_attribute(info.ssl_attribute("library")),
            "server_version_num": info.server_version,
        }
        transport = {
            "host": _normalize_hostname(info.host, "STOP_TARGET_MISMATCH"),
            "port": int(info.port),
            "database": info.dbname,
            "user": info.user,
        }
    except CollectorError:
        raise
    except Exception as exc:
        raise CollectorError("STOP_TLS_CONTRACT") from exc
    if (
        observed["ssl_in_use"] is not True
        or observed["protocol"] not in {"TLSv1.2", "TLSv1.3"}
        or isinstance(observed["server_version_num"], bool)
        or not isinstance(observed["server_version_num"], int)
        or observed["server_version_num"] <= 0
    ):
        raise CollectorError("STOP_TLS_CONTRACT")
    if transport != {
        "host": config.sql_host,
        "port": config.sql_port,
        "database": config.database,
        "user": config.user,
    }:
        raise CollectorError("STOP_TARGET_MISMATCH")
    observed["transport"] = transport
    digest_payload = {
        "schema": OBSERVED_TRANSPORT_VERSION,
        "ssl_in_use": observed["ssl_in_use"],
        "protocol": observed["protocol"],
        "cipher": observed["cipher"],
        "library": observed["library"],
        "server_version_num": observed["server_version_num"],
        "transport": [
            _plain_sha256(b"sql-host-v1\0", transport["host"]),
            transport["port"],
            _plain_sha256(b"database-v1\0", transport["database"]),
            _plain_sha256(b"user-v1\0", transport["user"]),
        ],
    }
    return observed, envelope_digest("observed-transport-v2", digest_payload)


def ensure_digest_domain_separation(
    target_binding_digest: str, observed_transport_digest: str,
) -> None:
    if target_binding_digest == observed_transport_digest:
        raise CollectorError("STOP_DIGEST_DOMAIN_COLLISION")


def target_binding(
    config: Config, ca_digest: str,
) -> tuple[dict[str, Any], str]:
    api_host = normalize_api_url(config.api_url)
    if config.sql_port != 5432 or config.sql_host != f"db.{config.project_ref}.supabase.co":
        raise CollectorError("STOP_TARGET_MISMATCH")
    private = {
        "schema": TARGET_BINDING_VERSION,
        "alias": config.target_alias,
        "api": [
            HOST_NORMALIZATION_VERSION,
            _plain_sha256(b"project-ref-v1\0", config.project_ref),
            _plain_sha256(b"f10.10-m3-host-v1\0", api_host),
        ],
        "sql": [
            SQL_HOST_NORMALIZATION_VERSION,
            _plain_sha256(b"sql-host-v1\0", config.sql_host),
            config.sql_port,
            _plain_sha256(b"database-v1\0", config.database),
            _plain_sha256(b"user-v1\0", config.user),
            _plain_sha256(b"provisioner-v1\0", config.provisioner),
            config.valid_until_epoch,
            "verify-full",
            ca_digest,
        ],
    }
    return private, envelope_digest("target-binding-v2", private)


def _execute(
    cursor: Any, sql: str, evidence: PrivateEvidence,
    params: tuple[Any, ...] | None = None,
) -> None:
    if sql not in STATIC_SQL:
        raise CollectorError("STOP_INTERNAL_CONTRACT")
    if sql == BEGIN_SQL:
        evidence.transaction += 1
    evidence.transcript.append({
        "transaction": evidence.transaction,
        "query_id": QUERY_IDS[sql],
        "parameter_count": 0 if params is None else len(params),
    })
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
    except Exception as exc:
        raise CollectorError("STOP_QUERY_FAILED") from exc


def _fetchall(cursor: Any, limit: int, reason: str) -> list[Sequence[Any]]:
    try:
        fetchmany = getattr(cursor, "fetchmany", None)
        rows = fetchmany(limit + 1) if callable(fetchmany) else cursor.fetchall()
    except Exception as exc:
        raise CollectorError("STOP_QUERY_FAILED") from exc
    if not isinstance(rows, list) or len(rows) > limit:
        raise CollectorError(reason)
    return rows


def _fetch_catalog(cursor: Any, budget: RemoteBudget) -> list[Sequence[Any]]:
    fetchmany = getattr(cursor, "fetchmany", None)
    if not callable(fetchmany):
        raise CollectorError("STOP_QUERY_FAILED")
    result: list[Sequence[Any]] = []
    try:
        while True:
            batch = fetchmany(min(CATALOG_FETCH_SIZE, MAX_CATALOG_ROWS + 1 - len(result)))
            if not isinstance(batch, list):
                raise CollectorError("STOP_QUERY_FAILED")
            if not batch:
                return result
            for row in batch:
                budget.consume(row)
                if len(result) >= MAX_CATALOG_ROWS:
                    raise CollectorError("STOP_CATALOG_LIMIT")
                result.append(row)
    except CollectorError:
        raise
    except Exception as exc:
        raise CollectorError("STOP_QUERY_FAILED") from exc


def _q0(
    cursor: Any, config: Config, budget: RemoteBudget, evidence: PrivateEvidence,
) -> list[Any]:
    _execute(cursor, Q0_SQL, evidence)
    rows = _fetchall(cursor, 1, "STOP_NEEDS_READONLY_CHANNEL")
    if len(rows) != 1 or len(rows[0]) != 39:
        raise CollectorError("STOP_NEEDS_READONLY_CHANNEL")
    row = list(rows[0])
    budget.consume(row)
    (
        session_user, current_user, _database, tx_ro, default_ro, search_path, client_encoding,
        rolsuper, bypass, createrole, createdb, can_login, inherits,
        replication, connection_limit, valid_until_epoch, valid_until_is_future,
        is_member_of_roles, role_member_count, member_role_name,
        member_admin_option, member_inherit_option, member_set_option,
        rls, _force_rls,
        has_table_select, can_select_id,
        can_select_is_active, can_select_syllabus, can_select_objectives,
        has_other_select, can_insert, can_update, can_delete, can_truncate,
        can_reference, can_trigger, mutating_column, security_definer_execute,
    ) = row
    valid = (
        isinstance(session_user, str) and session_user == current_user == config.user
        and _database == config.database and tx_ro == "on" and default_ro == "on"
        and search_path == "pg_catalog" and client_encoding == "UTF8" and rolsuper is False
        and bypass is True and createrole is False and createdb is False
        and can_login is True and inherits is False and replication is False
        and isinstance(connection_limit, int) and not isinstance(connection_limit, bool)
        and connection_limit == 1
        and isinstance(valid_until_epoch, int)
        and not isinstance(valid_until_epoch, bool)
        and valid_until_epoch == config.valid_until_epoch
        and valid_until_is_future is True
        and is_member_of_roles is False
        and isinstance(role_member_count, int)
        and not isinstance(role_member_count, bool)
        and role_member_count == 1
        and member_role_name == config.provisioner
        and member_admin_option is True
        and member_inherit_option is False
        and member_set_option is False
        and isinstance(rls, bool) and has_table_select is False
        and all(value is True for value in (
            can_select_id, can_select_is_active, can_select_syllabus,
            can_select_objectives,
        ))
        and all(value is False for value in (
            has_other_select, can_insert, can_update, can_delete, can_truncate,
            can_reference, can_trigger, mutating_column, security_definer_execute,
        ))
    )
    if not valid:
        raise CollectorError("STOP_NEEDS_READONLY_CHANNEL")
    return [tagged(value) for value in row]


def _validate_schema(raw: list[Sequence[Any]]) -> None:
    expected = {
        "id": ("uuid", True),
        "is_active": ("boolean", False),
        "syllabus": ("text", False),
        "objectives": ("text", False),
    }
    if len(raw) != 4:
        raise CollectorError("STOP_SCHEMA_DRIFT")
    observed: dict[str, tuple[Any, Any]] = {}
    for row in raw:
        if len(row) != 4 or not isinstance(row[0], str):
            raise CollectorError("STOP_SCHEMA_DRIFT")
        observed[row[0]] = (row[1], row[2])
    if observed != expected:
        raise CollectorError("STOP_SCHEMA_DRIFT")


def _validate_primary_key(raw: list[Sequence[Any]]) -> None:
    primary = [row for row in raw if len(row) == 5 and row[1] == "p"]
    if (
        len(primary) != 1 or primary[0][3] != 1
        or not isinstance(primary[0][4], str) or [primary[0][4]] != ["id"]
    ):
        raise CollectorError("STOP_UNSTABLE_KEYSET")


def _begin(
    cursor: Any, config: Config, budget: RemoteBudget, evidence: PrivateEvidence,
) -> list[Any]:
    _execute(cursor, BEGIN_SQL, evidence)
    return _q0(cursor, config, budget, evidence)


def _commit(cursor: Any, evidence: PrivateEvidence) -> None:
    _execute(cursor, COMMIT_SQL, evidence)


def _validate_catalog_surface(name: str, rows: list[Sequence[Any]]) -> None:
    expected_widths = {
        "schema": 4, "constraints": 5, "triggers": 6, "routines": 6,
        "extensions": 3, "aggregates": 30, "extension_members": 4,
    }
    if any(not isinstance(row, (tuple, list)) or len(row) != expected_widths[name] for row in rows):
        raise CollectorError("STOP_OPAQUE_ROUTINE_SURFACE")
    if name == "triggers" and any(value is None for row in rows for value in row):
        raise CollectorError("STOP_OPAQUE_ROUTINE_SURFACE")
    if name == "routines" and any(
        row[0] is None or row[1] is None or row[2] is None or row[3] is None
        or row[4] is None or row[5] is None
        for row in rows
    ):
        raise CollectorError("STOP_OPAQUE_ROUTINE_SURFACE")
    if name in {"extensions", "extension_members"} and any(
        value is None for row in rows for value in row
    ):
        raise CollectorError("STOP_OPAQUE_ROUTINE_SURFACE")


def _metadata_transaction(
    connection: Any, cursor: Any, config: Config,
    budget: RemoteBudget, evidence: PrivateEvidence,
) -> tuple[dict[str, Any], dict[str, str], list[Any], list[Any]]:
    q0_attestation = _begin(cursor, config, budget, evidence)
    raw: dict[str, list[Sequence[Any]]] = {}
    tagged_rows: dict[str, list[list[Any]]] = {}
    for name, sql in CATALOG_QUERIES:
        named_cursor = None
        try:
            named_cursor = connection.cursor(name=f"f10_10_m3_{name}")
            named_cursor.itersize = CATALOG_FETCH_SIZE
            _execute(named_cursor, sql, evidence)
            rows = _fetch_catalog(named_cursor, budget)
        except CollectorError:
            raise
        except Exception as exc:
            raise CollectorError("STOP_QUERY_FAILED") from exc
        finally:
            if named_cursor is not None:
                try:
                    named_cursor.close()
                except Exception as exc:
                    raise CollectorError("STOP_QUERY_FAILED") from exc
        _validate_catalog_surface(name, rows)
        raw[name] = rows
        tagged_rows[name] = [[tagged(value) for value in row] for row in rows]
    _validate_schema(raw["schema"])
    _validate_primary_key(raw["constraints"])
    _commit(cursor, evidence)
    trigger_payload = {
        "triggers": tagged_rows["triggers"],
        "routines": tagged_rows["routines"],
        "extensions": tagged_rows["extensions"],
        "aggregates": tagged_rows["aggregates"],
        "extension_members": tagged_rows["extension_members"],
    }
    fingerprints = {
        "schema_fingerprint": envelope_digest("schema-v1", tagged_rows["schema"]),
        "constraint_fingerprint": envelope_digest("constraints-v1", tagged_rows["constraints"]),
        "trigger_fingerprint": envelope_digest("triggers-v1", trigger_payload),
    }
    return tagged_rows, fingerprints, trigger_payload, q0_attestation


def _snapshot_transaction(
    cursor: Any, config: Config, fingerprints: dict[str, str],
    query_digest: str, binding_digest: str, transport_digest: str,
    snapshot_number: int,
    budget: RemoteBudget, evidence: PrivateEvidence,
) -> Snapshot:
    q0_attestation = _begin(cursor, config, budget, evidence)
    rows: list[list[Any]] = []
    raw_payload: list[list[Any]] = []
    normalized_payload: list[list[Any]] = []
    total_ids: list[list[list[str]]] = []
    active_ids: list[list[list[str]]] = []
    cohort: list[list[Any]] = []
    page_count = 0
    last_id: uuid.UUID | None = None
    missing_syllabus = missing_objectives = missing_both = incomplete = slots = active = 0
    while True:
        if last_id is None:
            _execute(cursor, Q4_FIRST_SQL, evidence)
        else:
            _execute(cursor, Q4_NEXT_SQL, evidence, (str(last_id),))
        page = _fetchall(cursor, PAGE_SIZE, "STOP_PAGE_INVALID")
        page_count += 1
        if len(page) > PAGE_SIZE:
            raise CollectorError("STOP_PAGE_INVALID")
        first_page_id: str | None = None
        last_page_id: str | None = None
        for source in page:
            if len(source) != 4:
                raise CollectorError("STOP_SCHEMA_DRIFT")
            identifier, is_active, syllabus, objectives = source
            try:
                parsed_id = uuid.UUID(str(identifier)) if not isinstance(identifier, uuid.UUID) else identifier
            except (ValueError, AttributeError, TypeError) as exc:
                raise CollectorError("STOP_SCHEMA_DRIFT") from exc
            if last_id is not None and parsed_id.int <= last_id.int:
                raise CollectorError("STOP_UNSTABLE_KEYSET")
            if len(rows) >= MAX_ROWS:
                raise CollectorError("STOP_POPULATION_LIMIT")
            if not isinstance(is_active, bool):
                raise CollectorError("STOP_SCHEMA_DRIFT")
            budget.consume(source)
            typed_id = typed_uuid(identifier)
            raw_syllabus, raw_objectives = tagged(syllabus), tagged(objectives)
            normalized_syllabus, normalized_objectives = normalized_tag(syllabus), normalized_tag(objectives)
            if len(normalized_syllabus) == 2:
                budget.consume(normalized_syllabus[1])
            if len(normalized_objectives) == 2:
                budget.consume(normalized_objectives[1])
            private_row = [typed_id, tagged(is_active), raw_syllabus, raw_objectives]
            rows.append(private_row)
            raw_payload.append(private_row)
            normalized_payload.append([typed_id, tagged(is_active), normalized_syllabus, normalized_objectives])
            total_ids.append([typed_id])
            if is_active:
                active += 1
                active_ids.append([typed_id])
                syllabus_missing = normalized_syllabus == ["null"]
                objectives_missing = normalized_objectives == ["null"]
                missing_syllabus += int(syllabus_missing)
                missing_objectives += int(objectives_missing)
                missing_both += int(syllabus_missing and objectives_missing)
                incomplete += int(syllabus_missing or objectives_missing)
                slots += int(syllabus_missing) + int(objectives_missing)
                cohort.append([typed_id, tagged(syllabus_missing), tagged(objectives_missing)])
            last_id = parsed_id
            first_page_id = first_page_id or str(parsed_id)
            last_page_id = str(parsed_id)
        evidence.page_boundaries.append({
            "snapshot": snapshot_number,
            "page": page_count,
            "row_count": len(page),
            "first_id": first_page_id,
            "last_id": last_page_id,
        })
        if len(page) < PAGE_SIZE:
            break
    _commit(cursor, evidence)
    summary = {
        "page_count": page_count,
        "total_count": len(rows),
        "total_ids_digest": envelope_digest("total-ids-v1", total_ids),
        "active_count": active,
        "active_ids_digest": envelope_digest("active-ids-v1", active_ids),
        "missing_syllabus": missing_syllabus,
        "missing_objectives": missing_objectives,
        "missing_both": missing_both,
        "incomplete_active_courses": incomplete,
        "incomplete_slots": slots,
        "full_snapshot_raw_digest": envelope_digest("snapshot-raw-v1", raw_payload),
        "full_snapshot_normalized_digest": envelope_digest("snapshot-normalized-v1", normalized_payload),
        "cohort_fingerprint": envelope_digest("cohort-v1", cohort),
        **fingerprints,
        "query_set_digest": query_digest,
        "target_binding_digest": binding_digest,
        "observed_transport_digest": transport_digest,
    }
    return Snapshot(rows, summary, q0_attestation)


def _bounded_raw_cause(error: BaseException) -> str | None:
    cause = error.__cause__
    if cause is None:
        return None
    try:
        return str(cause).encode("utf-8", "backslashreplace")[:4096].decode(
            "utf-8", "ignore"
        )
    except Exception:
        return "unrenderable-private-cause"


def collect(
    config: Config, connection_factory: ConnectionFactory,
    approved_query_digest: str, q0_predecessor_digest: str, pinned_ca: PinnedCA,
) -> CollectionResult:
    query_digest = _digest_argument(approved_query_digest)
    predecessor_digest = _digest_argument(q0_predecessor_digest)
    evidence = PrivateEvidence.create()
    budget = RemoteBudget()
    transport_digest: str | None = None
    try:
        connection = connection_factory(config, pinned_ca)
    except CollectorError as exc:
        exc.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "q0_predecessor_digest": predecessor_digest,
            "transcript": evidence.transcript, "page_boundaries": evidence.page_boundaries,
            "remote_utf8_bytes": budget.used, "reason_code": exc.reason_code,
            "raw_cause": _bounded_raw_cause(exc),
        }
        raise
    except Exception as exc:
        stable = CollectorError("STOP_CONNECTION_FAILED")
        stable.__cause__ = exc
        stable.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "q0_predecessor_digest": predecessor_digest,
            "transcript": evidence.transcript, "page_boundaries": evidence.page_boundaries,
            "remote_utf8_bytes": budget.used, "reason_code": stable.reason_code,
            "raw_cause": _bounded_raw_cause(stable),
        }
        raise stable
    try:
        binding_private, binding_digest = target_binding(config, pinned_ca.digest)
        transport, transport_digest = observed_transport_attestation(connection, config)
        ensure_digest_domain_separation(binding_digest, transport_digest)
        with connection.cursor() as cursor:
            catalog, fingerprints, trigger_payload, metadata_q0 = _metadata_transaction(
                connection, cursor, config, budget, evidence
            )
            first = _snapshot_transaction(
                cursor, config, fingerprints, query_digest, binding_digest,
                transport_digest, 1,
                budget, evidence,
            )
            second = _snapshot_transaction(
                cursor, config, fingerprints, query_digest, binding_digest,
                transport_digest, 2,
                budget, evidence,
            )
        if not (metadata_q0 == first.q0_attestation == second.q0_attestation):
            raise CollectorError("STOP_CHANNEL_DRIFT")
        if first.summary != second.summary or first.private_rows != second.private_rows:
            raise CollectorError("STOP_SNAPSHOT_DRIFT")
        private = {
            "schema": COLLECTOR_VERSION,
            "approval_id": config.approval_id,
            "binding": binding_private,
            "observed_transport": transport,
            "observed_transport_digest": transport_digest,
            "q0_predecessor_digest": predecessor_digest,
            "q0_attestations": [metadata_q0, first.q0_attestation, second.q0_attestation],
            "transcript": evidence.transcript,
            "page_boundaries": evidence.page_boundaries,
            "remote_utf8_bytes": budget.used,
            "catalog": catalog,
            "trigger_surface": trigger_payload,
            "snapshots": [
                {"summary": first.summary, "rows": first.private_rows},
                {"summary": second.summary, "rows": second.private_rows},
            ],
        }
        manifest = build_manifest(
            decision="PASS",
            reason_codes=[],
            target_alias=config.target_alias,
            approval_id=config.approval_id,
            query_digest=query_digest,
            binding_digest=binding_digest,
            transport_digest=transport_digest,
            q0_predecessor_digest=predecessor_digest,
            summary=first.summary,
            snapshots_equal=True,
        )
        return CollectionResult(private, manifest)
    except CollectorError as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        exc.partial_private = {
            "schema": COLLECTOR_VERSION,
            "approval_id": config.approval_id,
            "target_alias": config.target_alias,
            "query_set_digest": query_digest,
            "q0_predecessor_digest": predecessor_digest,
            "transcript": evidence.transcript,
            "page_boundaries": evidence.page_boundaries,
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": exc.reason_code,
            "raw_cause": _bounded_raw_cause(exc),
        }
        raise
    except Exception as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        stable = CollectorError("STOP_ACQUISITION_FAILED")
        stable.__cause__ = exc
        stable.partial_private = {
            "schema": COLLECTOR_VERSION,
            "approval_id": config.approval_id,
            "target_alias": config.target_alias,
            "query_set_digest": query_digest,
            "q0_predecessor_digest": predecessor_digest,
            "transcript": evidence.transcript,
            "page_boundaries": evidence.page_boundaries,
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": stable.reason_code,
            "raw_cause": _bounded_raw_cause(stable),
        }
        raise stable
    finally:
        try:
            connection.close()
        except Exception:
            pass


def collect_q0_only(
    config: Config, connection_factory: ConnectionFactory,
    approved_query_digest: str, pinned_ca: PinnedCA,
) -> CollectionResult:
    query_digest = _digest_argument(approved_query_digest)
    evidence = PrivateEvidence.create()
    budget = RemoteBudget()
    transport_digest: str | None = None
    try:
        connection = connection_factory(config, pinned_ca)
    except CollectorError as exc:
        exc.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "transcript": evidence.transcript, "page_boundaries": [],
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": exc.reason_code,
            "raw_cause": _bounded_raw_cause(exc),
        }
        raise
    except Exception as exc:
        stable = CollectorError("STOP_CONNECTION_FAILED")
        stable.__cause__ = exc
        stable.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "transcript": evidence.transcript, "page_boundaries": [],
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": stable.reason_code,
            "raw_cause": _bounded_raw_cause(stable),
        }
        raise stable
    try:
        binding_private, binding_digest = target_binding(config, pinned_ca.digest)
        transport, transport_digest = observed_transport_attestation(connection, config)
        ensure_digest_domain_separation(binding_digest, transport_digest)
        with connection.cursor() as cursor:
            q0_attestation = _begin(cursor, config, budget, evidence)
            _commit(cursor, evidence)
        private = {
            "schema": COLLECTOR_VERSION,
            "approval_id": config.approval_id,
            "binding": binding_private,
            "observed_transport": transport,
            "observed_transport_digest": transport_digest,
            "q0_attestations": [q0_attestation],
            "transcript": evidence.transcript,
            "page_boundaries": [],
            "remote_utf8_bytes": budget.used,
            "catalog": {},
            "snapshots": [],
        }
        manifest = build_manifest(
            decision="PASS", reason_codes=[], target_alias=config.target_alias,
            approval_id=config.approval_id, query_digest=query_digest,
            binding_digest=binding_digest, transport_digest=transport_digest,
            mode="q0-only", transcript=evidence.transcript,
            summary={"rows_collected": 0, "content_bytes": 0},
        )
        return CollectionResult(private, manifest)
    except CollectorError as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        exc.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "transcript": evidence.transcript, "page_boundaries": [],
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": exc.reason_code,
            "raw_cause": _bounded_raw_cause(exc),
        }
        raise
    except Exception as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        stable = CollectorError("STOP_ACQUISITION_FAILED")
        stable.__cause__ = exc
        stable.partial_private = {
            "schema": COLLECTOR_VERSION, "approval_id": config.approval_id,
            "target_alias": config.target_alias, "query_set_digest": query_digest,
            "transcript": evidence.transcript, "page_boundaries": [],
            "remote_utf8_bytes": budget.used,
            "observed_transport_digest": transport_digest,
            "reason_code": stable.reason_code,
            "raw_cause": _bounded_raw_cause(stable),
        }
        raise stable
    finally:
        try:
            connection.close()
        except Exception:
            pass


def build_manifest(
    *, decision: str, reason_codes: list[str], target_alias: str,
    approval_id: str, query_digest: str | None = None,
    binding_digest: str | None = None, transport_digest: str | None = None,
    q0_predecessor_digest: str | None = None,
    summary: dict[str, Any] | None = None, snapshots_equal: bool = False,
    mode: str = "collect", transcript: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if decision not in {"PASS", "HOLD", "STOP"}:
        raise CollectorError("STOP_INTERNAL_CONTRACT")
    if mode not in {"collect", "q0-only"}:
        raise CollectorError("STOP_INTERNAL_CONTRACT")
    safe_transcript: list[dict[str, Any]] = []
    if transcript is not None:
        for item in transcript:
            if (
                not isinstance(item, dict)
                or set(item) != {"transaction", "query_id", "parameter_count"}
                or isinstance(item["transaction"], bool)
                or not isinstance(item["transaction"], int)
                or item["transaction"] < 0
                or item["query_id"] not in set(QUERY_IDS.values())
                or isinstance(item["parameter_count"], bool)
                or not isinstance(item["parameter_count"], int)
                or item["parameter_count"] < 0
            ):
                raise CollectorError("STOP_INTERNAL_CONTRACT")
            safe_transcript.append({
                "transaction": item["transaction"],
                "query_id": item["query_id"],
                "parameter_count": item["parameter_count"],
            })
    if mode == "q0-only":
        if summary != {"rows_collected": 0, "content_bytes": 0}:
            raise CollectorError("STOP_INTERNAL_CONTRACT")
        safe_summary = dict(summary)
    else:
        safe_summary = {} if summary is None else {
            key: summary[key] for key in (
                "page_count", "total_count", "total_ids_digest", "active_count",
                "active_ids_digest", "missing_syllabus", "missing_objectives",
                "missing_both", "incomplete_active_courses", "incomplete_slots",
                "full_snapshot_raw_digest", "full_snapshot_normalized_digest",
                "cohort_fingerprint", "schema_fingerprint", "constraint_fingerprint",
                "trigger_fingerprint",
            )
        }
    return {
        "schema": "f10.10-m3-sanitized-manifest-v2",
        "commit_marker": "F10_10_M3_COMMIT_V2",
        "collector_version": COLLECTOR_VERSION,
        "canonical_version": CANONICAL_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "host_normalization_version": HOST_NORMALIZATION_VERSION,
        "target_binding_version": TARGET_BINDING_VERSION,
        "observed_transport_version": OBSERVED_TRANSPORT_VERSION,
        "mode": mode,
        "target_alias": target_alias,
        "approval_fingerprint": (
            _plain_sha256(b"approval-id-v1\0", approval_id)
            if approval_id not in {"", "UNSET"} else None
        ),
        "target_binding_digest": binding_digest,
        "observed_transport_digest": transport_digest,
        "q0_predecessor_digest": q0_predecessor_digest,
        "query_set_digest": query_digest,
        "snapshots_equal": snapshots_equal,
        "summary": safe_summary,
        "transcript": safe_transcript,
        "provider_calls": 0, "writer_calls": 0, "dml": 0, "ddl": 0,
        "rpc": 0, "backup_restore": 0, "schedule_changes": 0,
        "decision": decision,
        "reason_codes": sorted(set(reason_codes)),
    }


def _artifact_filename(value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.parts[:-1] != ARTIFACT_ROOT_RELATIVE.parts:
        raise CollectorError("STOP_PATH_UNSAFE")
    name = candidate.name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.json", name):
        raise CollectorError("STOP_PATH_UNSAFE")
    return name


def _verify_directory(fd: int) -> None:
    metadata = os.fstat(fd)
    if (
        not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid()
        or metadata.st_mode & 0o022
    ):
        raise CollectorError("STOP_PATH_UNSAFE")


class ArtifactDirectory:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.fd = -1

    def __enter__(self) -> "ArtifactDirectory":
        if sys.platform != "linux" or not hasattr(os, "O_NOFOLLOW"):
            raise CollectorError("STOP_UNSUPPORTED_PLATFORM")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        fds: list[int] = []
        try:
            current = os.open(self.workspace, flags)
            fds.append(current)
            _verify_directory(current)
            for component in ARTIFACT_ROOT_RELATIVE.parts:
                try:
                    child = os.open(component, flags, dir_fd=current)
                except FileNotFoundError:
                    os.mkdir(component, 0o700, dir_fd=current)
                    os.fsync(current)
                    child = os.open(component, flags, dir_fd=current)
                fds.append(child)
                _verify_directory(child)
                current = child
            self.fd = fds.pop()
            return self
        except CollectorError:
            raise
        except OSError as exc:
            raise CollectorError("STOP_PATH_UNSAFE") from exc
        finally:
            for descriptor in fds:
                os.close(descriptor)

    def __exit__(self, *_args: object) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def require_absent(self, *names: str) -> None:
        for name in names:
            try:
                os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise CollectorError("STOP_ARTIFACT_EXISTS")

    def read_predecessor(self, name: str, expected_digest: str) -> dict[str, Any]:
        descriptor: int | None = None
        try:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fd,
            )
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or metadata.st_mode & 0o077
                or metadata.st_size <= 0
                or metadata.st_size > MAX_PREDECESSOR_BYTES
            ):
                raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
            chunks: list[bytes] = []
            remaining = metadata.st_size
            while remaining:
                chunk = os.read(descriptor, min(64 * 1024, remaining))
                if not chunk:
                    raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
            raw = b"".join(chunks)
            actual_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
            if actual_digest != expected_digest:
                raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise CollectorError("STOP_Q0_PREDECESSOR_INVALID") from exc
            if not isinstance(payload, dict) or canonical_json(payload) + b"\n" != raw:
                raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
            return payload
        except CollectorError:
            raise
        except OSError as exc:
            raise CollectorError("STOP_Q0_PREDECESSOR_INVALID") from exc
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def publish(self, name: str, payload: bytes) -> None:
        if len(payload) > MAX_ARTIFACT_BYTES:
            raise CollectorError("STOP_ARTIFACT_LIMIT")
        temporary = f".{name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        linked = False
        durable = False
        try:
            descriptor = os.open(temporary, flags, 0o600, dir_fd=self.fd)
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise OSError("short write")
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.link(
                temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd,
                follow_symlinks=False,
            )
            linked = True
            try:
                os.fsync(self.fd)
            except OSError:
                try:
                    os.unlink(name, dir_fd=self.fd)
                    linked = False
                finally:
                    try:
                        os.fsync(self.fd)
                    except OSError:
                        pass
                raise
            durable = True
        except FileExistsError as exc:
            raise CollectorError("STOP_ARTIFACT_EXISTS") from exc
        except OSError as exc:
            raise CollectorError("STOP_ARTIFACT_WRITE_FAILED") from exc
        finally:
            try:
                os.unlink(temporary, dir_fd=self.fd)
            except OSError:
                # A temp orphan is not a commit marker.  Once the final link is
                # durable, cleanup failure must not downgrade a valid publish.
                if not durable and linked:
                    try:
                        os.unlink(name, dir_fd=self.fd)
                    except OSError:
                        pass


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise CollectorError("STOP_CLI_INVALID")


def validate_q0_predecessor(
    payload: dict[str, Any], *, query_digest: str, binding_digest: str,
) -> None:
    expected_keys = {
        "schema", "commit_marker", "collector_version", "canonical_version",
        "normalization_version", "host_normalization_version",
        "target_binding_version", "observed_transport_version", "mode",
        "target_alias", "approval_fingerprint", "target_binding_digest",
        "observed_transport_digest", "q0_predecessor_digest", "query_set_digest",
        "snapshots_equal", "summary", "transcript", "provider_calls",
        "writer_calls", "dml", "ddl", "rpc", "backup_restore",
        "schedule_changes", "decision", "reason_codes",
    }
    exact_values = {
        "schema": "f10.10-m3-sanitized-manifest-v2",
        "commit_marker": "F10_10_M3_COMMIT_V2",
        "collector_version": COLLECTOR_VERSION,
        "canonical_version": CANONICAL_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "host_normalization_version": HOST_NORMALIZATION_VERSION,
        "target_binding_version": TARGET_BINDING_VERSION,
        "observed_transport_version": OBSERVED_TRANSPORT_VERSION,
        "mode": "q0-only",
        "target_alias": "FREE_DB",
        "target_binding_digest": binding_digest,
        "q0_predecessor_digest": None,
        "query_set_digest": query_digest,
        "snapshots_equal": False,
        "summary": {"rows_collected": 0, "content_bytes": 0},
        "transcript": [
            {"transaction": 1, "query_id": "TX_BEGIN", "parameter_count": 0},
            {"transaction": 1, "query_id": "Q0", "parameter_count": 0},
            {"transaction": 1, "query_id": "TX_COMMIT", "parameter_count": 0},
        ],
        "provider_calls": 0,
        "writer_calls": 0,
        "dml": 0,
        "ddl": 0,
        "rpc": 0,
        "backup_restore": 0,
        "schedule_changes": 0,
        "decision": "PASS",
        "reason_codes": [],
    }
    if set(payload) != expected_keys or any(
        payload.get(key) != value for key, value in exact_values.items()
    ):
        raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")
    try:
        _digest_argument(payload["approval_fingerprint"])
        _digest_argument(payload["observed_transport_digest"])
    except (CollectorError, KeyError, TypeError) as exc:
        raise CollectorError("STOP_Q0_PREDECESSOR_INVALID") from exc
    if payload["observed_transport_digest"] == payload["target_binding_digest"]:
        raise CollectorError("STOP_Q0_PREDECESSOR_INVALID")


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(add_help=True)
    parser.add_argument(
        "--mode", choices=(
            "collect", "q0-only", "query-set-digest", "target-binding-digest",
        ),
        default="collect",
    )
    parser.add_argument("--target-alias", choices=("FREE_DB", "PRO_DB"))
    parser.add_argument("--approval-id")
    parser.add_argument("--expected-query-set-digest")
    parser.add_argument("--expected-target-binding-digest")
    parser.add_argument("--q0-predecessor-manifest")
    parser.add_argument("--expected-q0-predecessor-digest")
    parser.add_argument("--private-artifact")
    parser.add_argument("--sanitized-manifest")
    return parser


def _digest_argument(value: str) -> str:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise CollectorError("STOP_CONFIG_INVALID")
    return value


def run_cli(
    argv: Sequence[str], *, env: dict[str, str] | None = None,
    workspace: Path | None = None, connection_factory: ConnectionFactory | None = None,
) -> tuple[int, dict[str, Any]]:
    root = Path.cwd() if workspace is None else workspace
    alias = "UNSET"
    approval = "UNSET"
    query_digest_value: str | None = None
    binding_digest_value: str | None = None
    predecessor_digest_value: str | None = None
    output_mode = "collect"
    try:
        args = build_parser().parse_args(list(argv))
        output_mode = "q0-only" if args.mode == "q0-only" else "collect"
        query_payload = query_set_payload(root)
        actual_query = envelope_digest("query-set-v1", query_payload)
        query_digest_value = actual_query
        if args.mode == "query-set-digest":
            return 0, {"mode": "query-set-digest", "query_set_digest": actual_query}
        if args.target_alias is None or args.approval_id is None:
            raise CollectorError("STOP_CLI_INVALID")
        alias, approval = args.target_alias, args.approval_id
        config = load_config(
            dict(os.environ) if env is None else env,
            alias,
            approval,
            require_password=args.mode != "target-binding-digest",
        )
        if args.mode == "target-binding-digest":
            with open_pinned_ca(config) as pinned_ca:
                _, configured_binding = target_binding(config, pinned_ca.digest)
                return 0, {
                    "mode": "target-binding-digest",
                    "target_alias": alias,
                    "target_binding_version": TARGET_BINDING_VERSION,
                    "target_binding_digest": configured_binding,
                }
        required = (
            args.expected_query_set_digest, args.expected_target_binding_digest,
            args.private_artifact, args.sanitized_manifest,
        )
        if any(value is None for value in required):
            raise CollectorError("STOP_CLI_INVALID")
        predecessor_name: str | None = None
        if args.mode == "collect":
            if (
                args.q0_predecessor_manifest is None
                or args.expected_q0_predecessor_digest is None
            ):
                raise CollectorError("STOP_CLI_INVALID")
            predecessor_name = _artifact_filename(args.q0_predecessor_manifest)
            predecessor_digest_value = _digest_argument(
                args.expected_q0_predecessor_digest
            )
        elif (
            args.q0_predecessor_manifest is not None
            or args.expected_q0_predecessor_digest is not None
        ):
            raise CollectorError("STOP_CLI_INVALID")
        expected_query = _digest_argument(args.expected_query_set_digest)
        expected_binding = _digest_argument(args.expected_target_binding_digest)
        if actual_query != expected_query:
            raise CollectorError("STOP_QUERY_SET_MISMATCH")
        private_name = _artifact_filename(args.private_artifact)
        manifest_name = _artifact_filename(args.sanitized_manifest)
        if (
            private_name == manifest_name
            or predecessor_name in {private_name, manifest_name}
        ):
            raise CollectorError("STOP_PATH_UNSAFE")
        with ArtifactDirectory(root) as artifacts:
            artifacts.require_absent(private_name, manifest_name)
            result: CollectionResult | None = None
            try:
                with open_pinned_ca(config) as pinned_ca:
                    # The same pinned descriptor binds approval and libpq connection.
                    _, rebound = target_binding(config, pinned_ca.digest)
                    binding_digest_value = rebound
                    if rebound != expected_binding:
                        raise CollectorError("STOP_TARGET_MISMATCH")
                    if args.mode == "collect":
                        if predecessor_name is None or predecessor_digest_value is None:
                            raise CollectorError("STOP_INTERNAL_CONTRACT")
                        predecessor = artifacts.read_predecessor(
                            predecessor_name, predecessor_digest_value,
                        )
                        validate_q0_predecessor(
                            predecessor, query_digest=expected_query,
                            binding_digest=expected_binding,
                        )
                        result = collect(
                            config, connection_factory or default_connection_factory,
                            expected_query, predecessor_digest_value, pinned_ca,
                        )
                    else:
                        result = collect_q0_only(
                            config, connection_factory or default_connection_factory,
                            expected_query, pinned_ca,
                        )
                    verify_pinned_ca(pinned_ca)
                if (
                    result.manifest["target_binding_digest"] != expected_binding
                    or result.manifest["query_set_digest"] != actual_query
                ):
                    raise CollectorError("STOP_PUBLISH_BINDING_DRIFT")
                artifacts.publish(private_name, canonical_json(result.private) + b"\n")
                # Commit marker: always publish the sanitized manifest last.
                artifacts.publish(manifest_name, canonical_json(result.manifest) + b"\n")
                return 0, result.manifest
            except CollectorError as exc:
                private_stop = exc.partial_private or {
                    "schema": COLLECTOR_VERSION, "approval_id": approval,
                    "target_alias": alias, "reason_code": exc.reason_code,
                    "q0_predecessor_digest": predecessor_digest_value,
                    "raw_cause": _bounded_raw_cause(exc),
                    "transcript": (
                        result.private.get("transcript", []) if result is not None else []
                    ),
                    "page_boundaries": (
                        result.private.get("page_boundaries", []) if result is not None else []
                    ),
                }
                manifest = build_manifest(
                    decision=exc.decision, reason_codes=[exc.reason_code],
                    target_alias=alias, approval_id=approval,
                    query_digest=query_digest_value, binding_digest=binding_digest_value,
                    transport_digest=private_stop.get("observed_transport_digest"),
                    q0_predecessor_digest=predecessor_digest_value,
                    mode=output_mode,
                    summary=(
                        {"rows_collected": 0, "content_bytes": 0}
                        if output_mode == "q0-only" else None
                    ),
                    transcript=(
                        private_stop.get("transcript", [])
                        if output_mode == "q0-only" else None
                    ),
                )
                artifacts.publish(private_name, canonical_json(private_stop) + b"\n")
                artifacts.publish(manifest_name, canonical_json(manifest) + b"\n")
                return 2 if exc.decision == "STOP" else 1, manifest
    except CollectorError as exc:
        manifest = build_manifest(
            decision=exc.decision, reason_codes=[exc.reason_code],
            target_alias=alias, approval_id=approval,
            query_digest=query_digest_value, binding_digest=binding_digest_value,
            q0_predecessor_digest=predecessor_digest_value,
            mode=output_mode,
            summary=(
                {"rows_collected": 0, "content_bytes": 0}
                if output_mode == "q0-only" else None
            ),
        )
        return 2 if exc.decision == "STOP" else 1, manifest
    except Exception:
        manifest = build_manifest(
            decision="STOP", reason_codes=["STOP_INTERNAL_FAILURE"],
            target_alias=alias, approval_id=approval,
            query_digest=query_digest_value, binding_digest=binding_digest_value,
            q0_predecessor_digest=predecessor_digest_value,
            mode=output_mode,
            summary=(
                {"rows_collected": 0, "content_bytes": 0}
                if output_mode == "q0-only" else None
            ),
        )
        return 2, manifest


def main(argv: Sequence[str] | None = None) -> int:
    code, manifest = run_cli(sys.argv[1:] if argv is None else argv)
    sys.stdout.buffer.write(canonical_json(manifest) + b"\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
