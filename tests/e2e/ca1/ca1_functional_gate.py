#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from copy import deepcopy
from datetime import datetime, timezone
from xml.etree import ElementTree as ET


APP = pathlib.Path(os.environ.get("CA1_APP_DIR", "/app"))
HARNESS = pathlib.Path(__file__).resolve().parent
EVIDENCE = pathlib.Path(os.environ.get("CA1_EVIDENCE_DIR", "/evidence"))
DATA_API_PORT = int(os.environ.get("CA1_DATA_API_PORT", "18431"))
SITE_PORT = int(os.environ.get("CA1_SITE_PORT", "18080"))
RUN_ID = os.environ.get(
    "CA1_RUN_ID", datetime.now(timezone.utc).strftime("f99-ca1-%Y%m%dT%H%M%SZ")
)
KNOWN_DEFECT_DECISION = "NO_GO_KNOWN_T_H1_CA1_002B"
PASS_DECISION = "GO_TO_PREPARE_CERTIFICATION_PR"
SECRET_KEY = "sb_" + "secret_" + "synthetic_ca1_secret_value"
PUBLISHABLE_KEY = "sb_" + "publishable_" + "synthetic_ca1_publishable_value"
ALLOWED_SYNTHETIC_ENV = {
    "CA1_APP_DIR",
    "CA1_CANDIDATE_COMMIT",
    "CA1_CANDIDATE_TREE",
    "CA1_DATA_API_PORT",
    "CA1_CONTENT_LENIENT",
    "CA1_ENV_EXAMPLE_SCAN_PASS",
    "CA1_ENV_EXAMPLE_VERSIONED",
    "CA1_EVIDENCE_DIR",
    "CA1_EXPECTED_DECISION",
    "CA1_HARNESS_MANIFEST_JSON",
    "CA1_MODE_LENIENT",
    "CA1_RUN_ID",
    "CA1_SITE_PORT",
    "CA1_SYNTHETIC_ENV",
    "CA1_TLS_VERIFIED",
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_SUPABASE_PUBLISHABLE_KEY",
    "NEXT_SUPABASE_SECRET_KEY",
    "PYTHONPATH",
    "SUPABASE_URL",
}


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.tables = {
            "institutions": [],
            "institution_site_profiles": [],
            "staging_raw": [],
            "cleansed_programs": [],
            "enriched_programs": [],
            "courses": [],
        }
        self.next_id = 1
        self.site_hits = {}
        self.egress_attempts = []

    def new_id(self, prefix):
        del prefix
        value = f"00000000-0000-4000-8000-{self.next_id:012d}"
        self.next_id += 1
        return value

    def snapshot(self):
        with self.lock:
            return deepcopy(self.tables)


STORE = Store()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path):
    data = pathlib.Path(path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def redact(text):
    if not text:
        return ""
    for value, label in (
        (SECRET_KEY, "[SYNTHETIC_SECRET]"),
        (PUBLISHABLE_KEY, "[SYNTHETIC_PUBLISHABLE]"),
    ):
        text = text.replace(value, label)
    return text[-8000:]


def parse_query(path):
    parsed = urllib.parse.urlparse(path)
    return parsed.path, urllib.parse.parse_qs(parsed.query, keep_blank_values=True)


def match_filter(row, key, raw):
    value = row.get(key)
    if raw.startswith("eq."):
        return str(value) == urllib.parse.unquote(raw[3:])
    if raw.startswith("ilike.*") and raw.endswith("*"):
        return urllib.parse.unquote(raw[7:-1]).lower() in str(value or "").lower()
    if raw.startswith("in.(") and raw.endswith(")"):
        return str(value) in {item.strip() for item in raw[4:-1].split(",")}
    if raw == "is.null":
        return value is None
    return True


def apply_filters(rows, query):
    filtered = list(rows)
    for key, values in query.items():
        if key in {"select", "limit", "offset", "order", "on_conflict"} or key == "or":
            continue
        filtered = [row for row in filtered if match_filter(row, key, values[0])]
    return filtered


def project_columns(rows, query):
    select = query.get("select", ["*"])[0]
    if select in ("*", "count"):
        return rows
    columns = [column.strip() for column in select.split(",") if column.strip()]
    return [{key: row.get(key) for key in columns if key in row} for row in rows]


def apply_order(rows, query):
    order = query.get("order", [None])[0]
    if not order:
        return rows
    ordered = list(rows)
    for part in reversed([part for part in order.split(",") if part]):
        key, _, direction = part.partition(".")
        ordered.sort(key=lambda row: str(row.get(key, "")), reverse=direction == "desc")
    return ordered


class DataApiHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, _fmt, *_args):
        return

    def _json(self, status, payload, extra_headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return None
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path, query = parse_query(self.path)
        if not path.startswith("/rest/v1/"):
            return self._json(404, {"error": "not_found"})
        table = path.rsplit("/", 1)[-1]
        with STORE.lock:
            rows = apply_order(apply_filters(STORE.tables.get(table, []), query), query)
            total = len(rows)
            offset = int(query.get("offset", ["0"])[0] or 0)
            limit_raw = query.get("limit", [None])[0]
            limit = int(limit_raw) if limit_raw not in (None, "") else None
            page = rows[offset:] if limit is None else rows[offset: offset + limit]
            page = project_columns(page, query)
        end = offset + max(len(page) - 1, 0)
        return self._json(200, page, {"Content-Range": f"{offset}-{end}/{total}"})

    def do_POST(self):
        path, query = parse_query(self.path)
        payload = self._read_json()
        if path.startswith("/rest/v1/rpc/atomic_cleansing_promote"):
            return self._atomic_cleansing_promote(payload or {})
        if path.startswith("/rest/v1/rpc/lock_staging_records"):
            return self._lock_staging_records(payload or {})
        if not path.startswith("/rest/v1/"):
            return self._json(404, {"error": "not_found"})
        table = path.rsplit("/", 1)[-1]
        rows = payload if isinstance(payload, list) else [payload]
        out = []
        with STORE.lock:
            for raw in rows:
                item = dict(raw or {})
                if table == "staging_raw" and not query.get("on_conflict"):
                    if any(row.get("url") == item.get("url") for row in STORE.tables[table]):
                        return self._json(409, {"error": "duplicate_url"})
                if not item.get("id"):
                    item["id"] = STORE.new_id(table)
                conflict = query.get("on_conflict", [None])[0]
                existing = None
                if conflict:
                    for candidate in STORE.tables.setdefault(table, []):
                        if candidate.get(conflict) == item.get(conflict):
                            existing = candidate
                            break
                if existing is None:
                    STORE.tables.setdefault(table, []).append(item)
                    out.append(dict(item))
                else:
                    existing.update(item)
                    out.append(dict(existing))
        return self._json(201, out)

    def _lock_staging_records(self, payload):
        batch_size = int(payload.get("batch_size") or 100)
        with STORE.lock:
            rows = [row for row in STORE.tables["staging_raw"] if row.get("status") == "pending"][:batch_size]
            out = [dict(row) for row in rows]
        return self._json(200, out)

    def _atomic_cleansing_promote(self, payload):
        staging_ids = set(payload.get("p_staging_ids") or [])
        with STORE.lock:
            for row in STORE.tables["staging_raw"]:
                if row.get("id") in staging_ids:
                    row["status"] = "processed"
            for item in payload.get("p_cleansed_data") or []:
                record = dict(item)
                if not record.get("id"):
                    record["id"] = STORE.new_id("cleansed_programs")
                STORE.tables["cleansed_programs"].append(record)
        return self._json(200, [{"status": "success"}])

    def do_PATCH(self):
        path, query = parse_query(self.path)
        payload = self._read_json() or {}
        table = path.rsplit("/", 1)[-1]
        with STORE.lock:
            rows = apply_filters(STORE.tables.get(table, []), query)
            for row in rows:
                row.update(payload)
            body = [dict(row) for row in rows]
        if "return=representation" in self.headers.get("Prefer", ""):
            return self._json(200, body)
        return self._json(204, {})


class SiteHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, _fmt, *_args):
        return

    def do_GET(self):
        with STORE.lock:
            STORE.site_hits[self.path] = STORE.site_hits.get(self.path, 0) + 1
        if self.path == "/course/timeout":
            body = b"temporary failure"
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        title = "Curso Python CA1" if self.path != "/course/partial-ok" else "Curso Parcial CA1"
        desc = "Curso sintetico CA1 con contenido suficiente para pasar cleansing sin descarte artificial."
        body = (
            "<html><head>"
            f"<title>{title}</title>"
            f"<meta name='description' content='{desc}' />"
            "</head><body>"
            f"<h1>{title}</h1><p>{desc}</p><h2>Duracion</h2><p>40 horas virtuales.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_server(handler, port):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def assert_runner_env():
    bad = []
    for key, value in os.environ.items():
        upper = key.upper()
        sensitive_name = (
            key.startswith("SUPABASE_")
            or (key.startswith("NEXT_") and "SUPABASE" in key)
            or key.startswith("CF_")
            or key.startswith("OPENCODE_")
            or any(token in upper for token in ("TOKEN", "PASSWORD", "SECRET"))
        )
        if not sensitive_name:
            continue
        if key in {"SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"} and str(value).startswith("http://127.0.0.1:"):
            continue
        if key in ALLOWED_SYNTHETIC_ENV and "synthetic" in str(value).lower():
            continue
        bad.append(key)
    if bad:
        raise RuntimeError("non-synthetic environment variables present: " + ",".join(sorted(bad)))


def assert_env_files():
    env_files = sorted(path.name for path in APP.glob(".env*"))
    blocked = [name for name in env_files if name != ".env.example"]
    if blocked:
        raise RuntimeError("blocked env files present: " + ",".join(blocked))
    if ".env.example" not in env_files:
        raise RuntimeError(".env.example missing")
    if os.environ.get("CA1_ENV_EXAMPLE_VERSIONED") != "synthetic_versioned":
        raise RuntimeError(".env.example versioned preflight missing")
    if os.environ.get("CA1_ENV_EXAMPLE_SCAN_PASS") != "synthetic_scan_pass":
        raise RuntimeError(".env.example secret scan preflight missing")
    if os.environ.get("CA1_TLS_VERIFIED") != "synthetic_tls_verified":
        raise RuntimeError("TLS verification attestation missing")


def assert_manifest(manifest):
    rows = []
    mode_lenient = os.environ.get("CA1_MODE_LENIENT") == "synthetic_bind_mount_mode"
    content_lenient = os.environ.get("CA1_CONTENT_LENIENT") == "synthetic_bind_mount_content"
    for item in manifest:
        path = item["path"]
        expected_mode = item["mode"]
        expected_blob = item["blob"]
        full = APP / path
        if not full.exists():
            raise RuntimeError(f"runtime manifest missing: {path}")
        actual_mode = "100755" if os.access(full, os.X_OK) else "100644"
        actual_blob = git_blob_sha1(full)
        if (not mode_lenient and actual_mode != expected_mode) or (not content_lenient and actual_blob != expected_blob):
            raise RuntimeError(f"runtime manifest drift: {path}")
        rows.append({"path": path, "mode": expected_mode, "blob": expected_blob})
    return rows


def base_env():
    return {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONPATH": f"{HARNESS / 'stubs'}:{APP}:{APP / 'scripts'}",
        "CA1_SYNTHETIC_ENV": "synthetic",
        "SUPABASE_URL": f"http://127.0.0.1:{DATA_API_PORT}",
        "NEXT_PUBLIC_SUPABASE_URL": f"http://127.0.0.1:{DATA_API_PORT}",
        "NEXT_SUPABASE_SECRET_KEY": SECRET_KEY,
        "NEXT_SUPABASE_PUBLISHABLE_KEY": PUBLISHABLE_KEY,
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def run_command(cmd, timeout=60):
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(APP),
        env=base_env(),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout": redact(proc.stdout),
        "stderr": redact(proc.stderr),
        "duration_sec": round(time.time() - started, 3),
    }


def seed_profile(institution_id, pipeline_enabled, seed_urls=None):
    with STORE.lock:
        STORE.tables["institution_site_profiles"] = [{
            "id": "profile-ca1",
            "institution_id": institution_id,
            "site_type": "traditional_ssr",
            "discovery_mode": "hardcoded_urls",
            "seed_urls": seed_urls if seed_urls is not None else [f"http://127.0.0.1:{SITE_PORT}/course/python-ca1"],
            "allowed_url_patterns": ["/course/"],
            "exclusion_patterns": [],
            "pipeline_ready": bool(pipeline_enabled),
            "pipeline_enabled": bool(pipeline_enabled),
            "discovery_enabled": True,
            "circuit_open": False,
            "max_consecutive_errors": 2,
        }]


def assert_one_row(url, status):
    rows = [row for row in STORE.snapshot()["staging_raw"] if row.get("url") == url]
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one row for {url}, got {len(rows)}")
    if rows[0].get("status") != status:
        raise AssertionError(f"expected {status} for {url}, got {rows[0].get('status')}")
    return rows[0]


def write_artifacts(cases, summary):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary_path = EVIDENCE / "summary.json"
    junit_path = EVIDENCE / "junit.xml"
    logs_path = EVIDENCE / "redacted-logs.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    testsuite = ET.Element(
        "testsuite",
        name="ca1-functional",
        tests=str(len(cases)),
        failures=str(sum(1 for case in cases if case["status"] == "FAIL")),
        skipped=str(sum(1 for case in cases if case["status"] in {"SKIPPED", "BLOCKED"})),
    )
    for case in cases:
        test_case = ET.SubElement(testsuite, "testcase", name=case["test_id"], classname="F9.9.CA1")
        if case["status"] == "FAIL":
            failure = ET.SubElement(test_case, "failure", message=case.get("message", "FAIL"))
            failure.text = case.get("details", "")
        elif case["status"] in {"SKIPPED", "BLOCKED"}:
            skipped = ET.SubElement(test_case, "skipped", message=case["status"])
            skipped.text = case.get("message", "")
    ET.ElementTree(testsuite).write(junit_path, encoding="utf-8", xml_declaration=True)
    logs_path.write_text(json.dumps({"cases": cases}, indent=2), encoding="utf-8")
    return {
        "summary": str(summary_path),
        "summary_sha256": digest_file(summary_path),
        "junit": str(junit_path),
        "junit_sha256": digest_file(junit_path),
        "logs": str(logs_path),
        "logs_sha256": digest_file(logs_path),
    }


def load_json_argument(value, file_path, b64_value):
    if file_path:
        return json.loads(pathlib.Path(file_path).read_text(encoding="utf-8"))
    if b64_value:
        return json.loads(base64.b64decode(b64_value).decode("utf-8"))
    return json.loads(value)


def run_three_pass_case(cases, commands):
    config_path = APP / "config" / "institution_sources.json"
    original_config = config_path.read_text(encoding="utf-8")
    try:
        config_path.write_text(
            json.dumps([{"name": "CA1 Synthetic Institute", "url": f"http://127.0.0.1:{SITE_PORT}/"}]),
            encoding="utf-8",
        )
        fg1_first = run_command(["python3", "scripts/core/discovery_institutions.py"])
        fg1_second = run_command(["python3", "scripts/core/discovery_institutions.py"])
        commands.extend([{ "id": "fg1_first", **fg1_first }, { "id": "fg1_second", **fg1_second }])
        if fg1_first["exit_code"] != 0 or fg1_second["exit_code"] != 0:
            raise AssertionError("FG1 discovery failed")
        inst = STORE.snapshot()["institutions"][0]
        target_url = f"http://127.0.0.1:{SITE_PORT}/course/python-ca1"
        seed_profile(inst["id"], pipeline_enabled=False)
        discovery_only = run_command(["python3", "scripts/core/universal_harvester.py", json.dumps(inst)])
        commands.append({"id": "fg2_discovery_only", **discovery_only})
        if discovery_only["exit_code"] != 0:
            raise AssertionError("FG2 discovery-only failed")
        assert_one_row(target_url, "discovered")

        seed_profile(inst["id"], pipeline_enabled=True)
        enabled = run_command(["python3", "scripts/core/universal_harvester.py", json.dumps(inst)])
        commands.append({"id": "fg2_pipeline_enabled", **enabled})
        row = assert_one_row(target_url, "pending")
        if not row.get("raw_html") or not row.get("raw_name") or not re.fullmatch(r"[0-9a-f]{64}", row.get("content_hash", "")):
            raise AssertionError("pending row lacks complete extraction payload")
        hits_before = dict(STORE.site_hits)
        third = run_command(["python3", "scripts/core/universal_harvester.py", json.dumps(inst)])
        commands.append({"id": "fg2_third_noop", **third})
        if third["exit_code"] != 0:
            raise AssertionError("FG2 third NOOP failed")
        assert_one_row(target_url, "pending")
        if STORE.site_hits != hits_before:
            raise AssertionError("third run fetched a protected pending URL")
        cleansing = run_command(["python3", "scripts/core/cleansing_worker.py"])
        commands.append({"id": "cleansing_success_row", **cleansing})
        if cleansing["exit_code"] != 0:
            raise AssertionError("cleansing failed")
        processed = assert_one_row(target_url, "processed")
        cleansed = STORE.snapshot()["cleansed_programs"]
        if len(cleansed) != 1 or cleansed[0].get("status") != "pending" or cleansed[0].get("staging_id") != processed["id"]:
            raise AssertionError("cleansing did not promote exactly one pending cleansed row")
        cases.append({
            "run_id": RUN_ID,
            "test_id": "T-H1-CA1-002B-E2E",
            "status": "PASS",
            "message": "discovery-only -> pending -> NOOP -> cleansing processed completed",
            "final_status": "processed",
        })
    finally:
        config_path.write_text(original_config, encoding="utf-8")


def run_partial_case(cases, commands):
    STORE.reset()
    inst = {"id": "partial-inst", "name": "CA1 Partial", "slug": "ca1-partial", "website_url": f"http://127.0.0.1:{SITE_PORT}/"}
    with STORE.lock:
        STORE.tables["institutions"].append({**inst, "last_harvest_at": "unchanged"})
    ok_url = f"http://127.0.0.1:{SITE_PORT}/course/partial-ok"
    fail_url = f"http://127.0.0.1:{SITE_PORT}/course/timeout"
    protected = {
        "pending": f"http://127.0.0.1:{SITE_PORT}/course/already-pending",
        "processed": f"http://127.0.0.1:{SITE_PORT}/course/already-processed",
        "discarded": f"http://127.0.0.1:{SITE_PORT}/course/already-discarded",
    }
    seed_profile(inst["id"], pipeline_enabled=True, seed_urls=[])
    with STORE.lock:
        STORE.tables["staging_raw"].extend([
            {"id": "ok", "institution_id": inst["id"], "url": ok_url, "status": "discovered"},
            {"id": "fail", "institution_id": inst["id"], "url": fail_url, "status": "discovered"},
            {"id": "pending", "institution_id": inst["id"], "url": protected["pending"], "status": "pending", "raw_html": "kept"},
            {"id": "processed", "institution_id": inst["id"], "url": protected["processed"], "status": "processed"},
            {"id": "discarded", "institution_id": inst["id"], "url": protected["discarded"], "status": "discarded"},
        ])
    result = run_command(["python3", "scripts/core/universal_harvester.py", json.dumps(inst)])
    commands.append({"id": "fg2_partial", **result})
    if result["exit_code"] == 0:
        raise AssertionError("partial FG2 run returned success")
    assert_one_row(ok_url, "pending")
    assert_one_row(fail_url, "discovered")
    for status, url in protected.items():
        assert_one_row(url, status)
    inst_after = STORE.snapshot()["institutions"][0]
    if inst_after.get("last_harvest_at") != "unchanged":
        raise AssertionError("freshness changed after partial run")
    cases.append({
        "run_id": RUN_ID,
        "test_id": "T-H1-CA1-003-PARTIAL",
        "status": "PASS",
        "message": "partial run exits non-zero, preserves failed discovered and protected states",
        "exit_code": result["exit_code"],
    })


def classify_known_defect(cases):
    for case in cases:
        if case.get("test_id") == "T-H1-CA1-002B-E2E" and case.get("status") == "FAIL":
            details = case.get("details", "")
            if "expected pending" in details and "got discovered" in details:
                return True
    return False


def main():
    global EVIDENCE
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--candidate-tree", required=True)
    parser.add_argument("--runtime-commit", required=True)
    parser.add_argument("--runtime-tree", required=True)
    parser.add_argument("--runtime-manifest-json")
    parser.add_argument("--runtime-manifest-file")
    parser.add_argument("--runtime-manifest-b64")
    parser.add_argument("--harness-manifest-json")
    parser.add_argument("--harness-manifest-file")
    parser.add_argument("--harness-manifest-b64")
    parser.add_argument("--expected-decision", choices=[PASS_DECISION, KNOWN_DEFECT_DECISION], required=True)
    parser.add_argument("--evidence-dir", default=str(EVIDENCE))
    args = parser.parse_args()
    EVIDENCE = pathlib.Path(args.evidence_dir)
    if not (args.runtime_manifest_json or args.runtime_manifest_file or args.runtime_manifest_b64):
        raise SystemExit("runtime manifest is required")
    if not (args.harness_manifest_json or args.harness_manifest_file or args.harness_manifest_b64):
        raise SystemExit("harness manifest is required")
    runtime_manifest_input = load_json_argument(args.runtime_manifest_json, args.runtime_manifest_file, args.runtime_manifest_b64)
    harness_manifest_input = load_json_argument(args.harness_manifest_json, args.harness_manifest_file, args.harness_manifest_b64)

    cases = []
    commands = []
    data_api = site = None
    decision = "NO_GO_CA1_FUNCTIONAL"
    runtime_manifest = []
    try:
        assert_runner_env()
        assert_env_files()
        runtime_manifest = assert_manifest(runtime_manifest_input)
        data_api = start_server(DataApiHandler, DATA_API_PORT)
        site = start_server(SiteHandler, SITE_PORT)
        try:
            run_three_pass_case(cases, commands)
            run_partial_case(cases, commands)
            decision = PASS_DECISION
        except Exception as exc:
            cases.append({
                "run_id": RUN_ID,
                "test_id": "T-H1-CA1-002B-E2E",
                "status": "FAIL",
                "message": type(exc).__name__,
                "details": str(exc),
            })
            if classify_known_defect(cases):
                decision = KNOWN_DEFECT_DECISION
    except Exception as exc:
        cases.append({
            "run_id": RUN_ID,
            "test_id": "HARNESS",
            "status": "FAIL",
            "message": type(exc).__name__,
            "details": str(exc),
        })
    finally:
        teardown = []
        for name, server in (("site", site), ("data_api", data_api)):
            if server is not None:
                server.shutdown()
                server.server_close()
                teardown.append({"resource": name, "result": "destroyed"})
            else:
                teardown.append({"resource": name, "result": "noop"})
        summary = {
            "run_id": RUN_ID,
            "utc": utc_now(),
            "candidate_commit": args.candidate_commit,
            "candidate_tree": args.candidate_tree,
            "runtime_commit": args.runtime_commit,
            "runtime_tree": args.runtime_tree,
            "runtime_manifest": runtime_manifest,
            "harness_manifest": harness_manifest_input,
            "cases": cases,
            "commands": commands,
            "egress_attempts": STORE.egress_attempts,
            "teardown": teardown,
            "decision": decision,
            "expected_decision": args.expected_decision,
        }
        artifacts = write_artifacts(cases, summary)
        print(json.dumps({"decision": decision, "expected_decision": args.expected_decision, "artifacts": artifacts, "cases": cases}, indent=2))
    return 0 if decision == args.expected_decision else 1


if __name__ == "__main__":
    sys.exit(main())
