#!/usr/bin/env python3
"""Build the exact local-only SQL body for Supabase apply_migration."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql"
PROJECTION_VERSION = "f10.10-m3-apply-projection-v1"
ROLE_RE = re.compile(r"[a-z_][a-z0-9_]{0,62}\Z")
DIGEST_RE = re.compile(r"sha256:([0-9a-f]{64})\Z")
TRANSACTION_CONTROL_RE = re.compile(
    r"(?:ABORT|BEGIN|COMMIT|END|ROLLBACK)(?:\s|\Z)"
    r"|START\s+TRANSACTION(?:\s|\Z)"
    r"|PREPARE\s+TRANSACTION(?:\s|\Z)"
    r"|SAVEPOINT(?:\s|\Z)"
    r"|RELEASE(?:\s+SAVEPOINT)?(?:\s|\Z)"
    r"|SET\s+(?:LOCAL\s+)?TRANSACTION(?:\s|\Z)"
    r"|SET\s+SESSION\s+CHARACTERISTICS\s+AS\s+TRANSACTION(?:\s|\Z)",
)


class ProjectionError(ValueError):
    pass


@dataclass(frozen=True)
class Projection:
    source_package_digest: str
    applied_query_digest: str
    provisioner_fingerprint: str
    applied_query: bytes


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def provisioner_fingerprint(role: str) -> str:
    if not ROLE_RE.fullmatch(role) or len(role.encode("ascii")) > 63:
        raise ProjectionError("STOP_CONFIG_INVALID")
    return _digest(b"provisioner-v1\0" + role.encode("ascii"))


def _normalize_source(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf") or b"\x00" in raw:
        raise ProjectionError("STOP_SOURCE_INVALID")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ProjectionError("STOP_SOURCE_INVALID") from exc
    if "\r" in text.replace("\r\n", ""):
        raise ProjectionError("STOP_SOURCE_INVALID")
    return text.replace("\r\n", "\n").encode("utf-8")


def _statement_spans(sql: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    start = 0
    code: list[str] = []
    code_start: int | None = None
    index = 0
    block_depth = 0
    quote: str | None = None
    dollar: str | None = None

    while index < len(sql):
        if dollar is not None:
            if sql.startswith(dollar, index):
                index += len(dollar)
                dollar = None
            else:
                index += 1
            continue
        if quote is not None:
            if sql[index] == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if block_depth:
            if sql.startswith("/*", index):
                block_depth += 1
                index += 2
            elif sql.startswith("*/", index):
                block_depth -= 1
                index += 2
            else:
                index += 1
            continue
        if sql.startswith("--", index):
            newline = sql.find("\n", index + 2)
            index = len(sql) if newline < 0 else newline + 1
            code.append(" ")
            continue
        if sql.startswith("/*", index):
            block_depth = 1
            index += 2
            code.append(" ")
            continue
        char = sql[index]
        if char in {"'", '"'}:
            if code_start is None:
                code_start = index
            quote = char
            code.append("?")
            index += 1
            continue
        if char == "$":
            match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[index:])
            if match:
                if code_start is None:
                    code_start = index
                dollar = match.group(0)
                code.append("?")
                index += len(dollar)
                continue
        if char == ";":
            code.append(char)
            spans.append((code_start if code_start is not None else start, index + 1, " ".join("".join(code).split())))
            start = index + 1
            code = []
            code_start = None
        else:
            if code_start is None and not char.isspace():
                code_start = index
            code.append(char)
        index += 1

    if quote is not None or dollar is not None or block_depth:
        raise ProjectionError("STOP_SOURCE_INVALID")
    if "".join(code).strip():
        raise ProjectionError("STOP_TRANSACTION_ENVELOPE_INVALID")
    return spans


def project_apply_migration_query(
    source: bytes,
    *,
    expected_source_package_digest: str,
    provisioner: str,
    expected_provisioner_fingerprint: str,
) -> Projection:
    normalized = _normalize_source(source)
    if not DIGEST_RE.fullmatch(expected_source_package_digest):
        raise ProjectionError("STOP_CONFIG_INVALID")
    actual_source_digest = _digest(normalized)
    if not hmac.compare_digest(actual_source_digest, expected_source_package_digest):
        raise ProjectionError("STOP_PACKAGE_DIGEST_MISMATCH")
    if not DIGEST_RE.fullmatch(expected_provisioner_fingerprint):
        raise ProjectionError("STOP_CONFIG_INVALID")
    actual_fingerprint = provisioner_fingerprint(provisioner)
    if not hmac.compare_digest(actual_fingerprint, expected_provisioner_fingerprint):
        raise ProjectionError("STOP_PROVISIONER_BINDING_MISMATCH")

    text = normalized.decode("utf-8")
    spans = _statement_spans(text)
    if len(spans) < 3 or spans[0][2] != "BEGIN;" or spans[-1][2] != "COMMIT;":
        raise ProjectionError("STOP_TRANSACTION_ENVELOPE_INVALID")
    for _start, _end, statement in spans[1:-1]:
        control = statement[:-1].strip().upper()
        if TRANSACTION_CONTROL_RE.match(control):
            raise ProjectionError("STOP_TRANSACTION_ENVELOPE_INVALID")

    expected_hex = expected_provisioner_fingerprint.removeprefix("sha256:")
    guard = f"""DO $f1010_executor_binding$
BEGIN
  IF current_user IS DISTINCT FROM session_user
     OR pg_catalog.sha256(
          pg_catalog.convert_to('provisioner-v1', 'UTF8')
          || pg_catalog.decode('00', 'hex')
          || pg_catalog.convert_to(current_user::text, 'UTF8')
        ) IS DISTINCT FROM pg_catalog.decode('{expected_hex}', 'hex') THEN
    RAISE EXCEPTION 'F10.10 M3 reader: executor binding failed';
  END IF;
END
$f1010_executor_binding$;

""".encode("ascii")
    begin_start, begin_end, _ = spans[0]
    commit_start, commit_end, _ = spans[-1]
    body = (
        normalized[:begin_start]
        + normalized[begin_end:commit_start]
        + normalized[commit_end:]
    )
    applied_query = guard + body
    if provisioner.encode("ascii") in guard:
        raise ProjectionError("STOP_PRIVATE_VALUE_LEAK")
    return Projection(
        source_package_digest=actual_source_digest,
        applied_query_digest=_digest(applied_query),
        provisioner_fingerprint=expected_provisioner_fingerprint,
        applied_query=applied_query,
    )


def _write_private_at(directory_fd: int, name: str, contents: bytes) -> None:
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("no-follow unavailable")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= os.O_NOFOLLOW
    fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        os.fchmod(fd, 0o600)
        remaining = memoryview(contents)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("short write")
            remaining = remaining[written:]
        os.fsync(fd)
        metadata = os.fstat(fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_nlink != 1
        ):
            raise OSError("unsafe private artifact")
    except BaseException:
        try:
            os.unlink(name, dir_fd=directory_fd)
        except OSError:
            pass
        raise
    finally:
        os.close(fd)


def _write_private(path: Path, contents: bytes) -> None:
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_fd = os.open(path.parent, directory_flags)
    try:
        _write_private_at(directory_fd, path.name, contents)
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _open_private_root(private_root: Path) -> int:
    metadata = private_root.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or private_root.is_symlink():
        raise ProjectionError("STOP_OUTPUT_PATH_INVALID")
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("no-follow unavailable")
    flags |= os.O_NOFOLLOW
    return os.open(private_root, flags)


def _publish_private_pair(
    private_root: Path,
    sql_name: str,
    sql_contents: bytes,
    manifest_name: str,
    manifest_contents: bytes,
) -> None:
    root_fd = _open_private_root(private_root)
    sql_created = False
    manifest_created = False
    try:
        _write_private_at(root_fd, sql_name, sql_contents)
        sql_created = True
        _write_private_at(root_fd, manifest_name, manifest_contents)
        manifest_created = True
        os.fsync(root_fd)
    except BaseException:
        for created, name in (
            (manifest_created, manifest_name),
            (sql_created, sql_name),
        ):
            if created:
                try:
                    os.unlink(name, dir_fd=root_fd)
                except OSError:
                    pass
        try:
            os.fsync(root_fd)
        except OSError:
            pass
        raise
    finally:
        os.close(root_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-package-digest", required=True)
    parser.add_argument("--expected-provisioner-fingerprint", required=True)
    parser.add_argument("--output-sql", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        role = os.environ.get("F10_10_M3_PROVISIONER", "")
        projection = project_apply_migration_query(
            SOURCE.read_bytes(),
            expected_source_package_digest=args.expected_package_digest,
            provisioner=role,
            expected_provisioner_fingerprint=args.expected_provisioner_fingerprint,
        )
        private_root = ROOT / "local/f10_10/m3"
        if args.output_sql.resolve() == args.output_manifest.resolve():
            raise ProjectionError("STOP_OUTPUT_PATH_INVALID")
        for output in (args.output_sql, args.output_manifest):
            if output.resolve().parent != private_root:
                raise ProjectionError("STOP_OUTPUT_PATH_INVALID")
        manifest = {
            "schema": PROJECTION_VERSION,
            "source_package_digest": projection.source_package_digest,
            "applied_query_digest": projection.applied_query_digest,
            "provisioner_fingerprint": projection.provisioner_fingerprint,
        }
        _publish_private_pair(
            private_root,
            args.output_sql.name,
            projection.applied_query,
            args.output_manifest.name,
            (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"),
        )
    except (OSError, ProjectionError) as exc:
        reason = str(exc) if isinstance(exc, ProjectionError) else "STOP_LOCAL_IO"
        print(json.dumps({"status": "STOP", "reason": reason}, separators=(",", ":")))
        return 2
    print(json.dumps({
        "status": "PASS",
        "schema": PROJECTION_VERSION,
        "applied_query_digest": projection.applied_query_digest,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
