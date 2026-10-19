"""Exercise real H3 pipeline workers over a local PostgREST/PG17 fixture."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os

# Set this before importing project or third-party modules: workers load dotenv at import time.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

import re
import sys
import tempfile
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import requests

sys.path[:0] = ["/workspace/scripts/core", "/workspace/scripts/shared", "/workspace"]

from scripts.core import enrichment_worker as enrichment_module
from scripts.core import sync_vector_worker as sync_vector_module
from scripts.core import universal_harvester as harvester_module
from scripts.core.cleansing_worker import CleansingWorker
from scripts.core.enrichment_worker import EnrichmentWorker
from scripts.core.sync_vector_worker import SyncVectorWorker
from scripts.core.universal_harvester import UniversalHarvester
from scripts.shared import db_client as db_client_module
from scripts.shared.db_client import DatabaseClient
import integrity_ping as integrity_ping_module


INSTITUTION_ID = "10000000-0000-0000-0000-000000000001"
COURSE_URL = "https://synthetic.h3.example/programas/analitica-aplicada"
COURSE_HTML = """<!doctype html><html><head>
<title>Analítica Aplicada | H3 Synthetic Institute</title>
<meta name="description" content="Programa sintético de analítica aplicada para formación profesional.">
<link rel="canonical" href="https://synthetic.h3.example/programas/analitica-aplicada">
</head><body><main><h1>Programa de Analítica Aplicada</h1>
<p>Duración: 6 meses. Modalidad online. Inversión total S/ 1,250.</p>
<h2>Requisitos</h2><p>Conocimientos básicos de hojas de cálculo.</p>
<h2>Objetivos</h2><p>Modelar datos sintéticos y comunicar hallazgos.</p>
</main></body></html>"""
JWT_SECRET = b"h3req1-pg17-postgrest-local-fixture-secret"
FAULTS: dict[str, int] = {}
FAILURES_SEEN: dict[str, int] = {}
CURRENT_PHASE = "startup"


class PhaseFailure(RuntimeError):
    def __init__(self, phase: str, code: str) -> None:
        super().__init__(code)
        self.phase = phase
        self.code = code


def require(condition: bool, phase: str, code: str) -> None:
    if not condition:
        raise PhaseFailure(phase, code)


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def service_token() -> str:
    now = int(time.time())
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64url(json.dumps({"role": "service_role", "iat": now, "exp": now + 1800}, separators=(",", ":")).encode())
    signed = f"{header}.{payload}".encode()
    signature = b64url(hmac.new(JWT_SECRET, signed, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


class PrefixProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _forward(self) -> None:
        parsed = urlsplit(self.path)
        if not parsed.path.startswith("/rest/v1"):
            self.send_error(404)
            return
        route = parsed.path.removeprefix("/rest/v1") or "/"
        fault_key = f"{self.command}:{route}"
        if FAULTS.get(fault_key, 0) > 0:
            FAULTS[fault_key] -= 1
            FAILURES_SEEN[fault_key] = FAILURES_SEEN.get(fault_key, 0) + 1
            body = b'{"code":"synthetic_upstream_failure","message":"fixture fault"}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() in {
                "accept", "accept-profile", "authorization", "apikey",
                "content-profile", "content-type", "prefer", "range",
            }
        }
        try:
            response = requests.request(
                self.command,
                f"http://postgrest:3000{route}"
                + (f"?{parsed.query}" if parsed.query else ""),
                headers=headers,
                data=body,
                timeout=(2, 5),
            )
        except requests.RequestException:
            body = b'{"code":"fixture_proxy_unavailable"}'
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            if key.lower() not in {"connection", "content-length", "transfer-encoding", "content-encoding"}:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(response.content)))
        self.end_headers()
        if response.content:
            self.wfile.write(response.content)

    do_GET = _forward
    do_POST = _forward
    do_PATCH = _forward
    do_DELETE = _forward


def make_client(proxy_url: str) -> DatabaseClient:
    # Explicitly inject a synthetic identity. A caller environment may contain
    # real keys; DatabaseClient must never read them for this fixture.
    client = DatabaseClient(
        supabase_url=proxy_url,
        supabase_key="sb_publishable_fixture",
    )
    token = service_token()
    client._get_headers = lambda use_service_role=None: {
        "apikey": "h3req1-local-api-fixture",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return client


def fetch_rows(client: DatabaseClient, table: str, filters: str = "", *, service: bool = False) -> list[dict]:
    getter = client.select_service_raise if service else client.select_pipeline_raise
    return getter(table, filters=filters, limit=10, order="id.asc")


def verify_dotenv_isolation() -> None:
    require(os.environ.get("PYTHON_DOTENV_DISABLED") == "1", "dotenv-isolation", "DOTENV_DISABLE_FLAG_MISSING")
    for path in (
        Path("/workspace/.env"),
        Path("/workspace/scripts/.env"),
        Path("/workspace/scripts/shared/.env"),
    ):
        require(not path.exists(), "dotenv-isolation", "WORKSPACE_DOTENV_FILE_PRESENT")

    from dotenv import load_dotenv

    sentinel = "H3REQ1_DOTENV_ISOLATION_SENTINEL"
    previous = os.environ.pop(sentinel, None)
    original_cwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory(prefix="h3req1-dotenv-") as temporary_dir:
            Path(temporary_dir, ".env").write_text(f"{sentinel}=synthetic-fixture-only\n", encoding="utf-8")
            os.chdir(temporary_dir)
            load_dotenv()
            require(sentinel not in os.environ, "dotenv-isolation", "DOTENV_DISABLE_PROBE_LOADED_SENTINEL")
    finally:
        os.chdir(original_cwd)
        if previous is not None:
            os.environ[sentinel] = previous
    print("phase=dotenv-isolation|result=PASS|disabled=verified|workspace=allowlisted")


def run() -> None:
    global CURRENT_PHASE
    logging.disable(logging.CRITICAL)
    CURRENT_PHASE = "dotenv-isolation"
    verify_dotenv_isolation()
    CURRENT_PHASE = "postgrest-readiness"
    postgrest_ready = False
    for _ in range(30):
        try:
            response = requests.get("http://postgrest:3000/", timeout=2)
            if response.status_code == 200:
                postgrest_ready = True
                break
        except requests.RequestException:
            pass
        time.sleep(1)
    require(postgrest_ready, "postgrest-readiness", "POSTGREST_NOT_READY")

    proxy = ThreadingHTTPServer(("127.0.0.1", 0), PrefixProxyHandler)
    thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    thread.start()
    proxy_url = f"http://127.0.0.1:{proxy.server_address[1]}"
    client = make_client(proxy_url)
    db_client_module.DNS_RETRY_MAX = 1
    harvester_module.get_db_client = lambda: client
    enrichment_module.get_db_client = lambda: client
    sync_vector_module.get_db_client = lambda: client

    try:
        api_probe = requests.get(f"{proxy_url}/rest/v1/", headers=client._get_headers(True), timeout=5)
        require(api_probe.status_code == 200, "postgrest-readiness", "REST_ROOT_NOT_READY")
        print("phase=postgrest-http|result=PASS")

        institution = {
            "id": INSTITUTION_ID,
            "name": "H3 Synthetic Institute",
            "slug": "h3-synthetic",
            "website_url": "https://synthetic.h3.example",
        }
        CURRENT_PHASE = "harvester-construction"
        first = UniversalHarvester(institution, max_discovered_urls=1)
        CURRENT_PHASE = "discovery-checkpoint"
        first_discovery = asyncio.run(first.discover_courses())
        CURRENT_PHASE = "discovery-checkpoint-read"
        rows = fetch_rows(client, "staging_raw", "institution_id=eq." + INSTITUTION_ID)
        require(first_discovery == [COURSE_URL] and len(rows) == 1 and rows[0]["status"] == "discovered", "discovery-checkpoint", "CHECKPOINT_NOT_PERSISTED")

        CURRENT_PHASE = "discovery-resume-construction"
        resumed = UniversalHarvester(institution, max_discovered_urls=1)
        CURRENT_PHASE = "discovery-resume"
        resumed_urls = asyncio.run(resumed.discover_courses())
        require(resumed_urls == [COURSE_URL], "discovery-resume", "DISCOVERED_URL_NOT_RESUMED")
        require(len(fetch_rows(client, "staging_raw", "institution_id=eq." + INSTITUTION_ID)) == 1, "discovery-resume", "RESUME_DUPLICATED_URL")
        print("phase=discovery-checkpoint-resume|result=PASS|rows=1")

        raw = {
            "url": COURSE_URL,
            "effective_url": COURSE_URL,
            "canonical_url": COURSE_URL,
            "institution_id": INSTITUTION_ID,
            "status": "pending",
            "raw_name": "Programa de Analítica Aplicada",
            "raw_description": "Programa sintético para formación profesional.",
            "raw_html": COURSE_HTML,
            "content_hash": hashlib.sha256(COURSE_HTML.encode()).hexdigest(),
            "metadata": {"fixture": "pipeline-postgrest-pg17-r1"},
        }
        CURRENT_PHASE = "discovery-handoff"
        promoted = resumed._save_to_staging(raw)
        require(promoted.get("status") == "pending" and promoted.get("raw_html") == COURSE_HTML, "discovery-handoff", "PENDING_HANDOFF_NOT_PERSISTED")
        print("phase=discovery-to-staging|result=PASS")

        CURRENT_PHASE = "cleansing-failure-recovery"
        cleanser = CleansingWorker(db_client=client)
        pending_stage = fetch_rows(client, "staging_raw", "status=eq.pending&institution_id=eq." + INSTITUTION_ID)
        require(len(pending_stage) == 1, "cleansing-setup", "PENDING_STAGE_NOT_FOUND")
        clean_fault = "POST:/rpc/atomic_cleansing_promote"
        FAULTS[clean_fault] = 1
        cleansing_failed = False
        try:
            cleanser.process_batch(pending_stage)
        except RuntimeError:
            cleansing_failed = True
        require(cleansing_failed, "cleansing-failure", "INJECTED_FAILURE_NOT_PROPAGATED")
        staged_after_fail = fetch_rows(client, "staging_raw", "institution_id=eq." + INSTITUTION_ID)
        clean_after_fail = fetch_rows(client, "cleansed_programs", "institution_id=eq." + INSTITUTION_ID)
        require(FAILURES_SEEN.get(clean_fault) == 1 and staged_after_fail[0]["status"] == "pending" and clean_after_fail == [], "cleansing-failure", "FAILURE_PARTIALLY_PROMOTED")
        require(cleanser.process_batch(pending_stage) == 1, "cleansing-recovery", "CLEANSING_RECOVERY_FAILED")
        clean_rows = fetch_rows(client, "cleansed_programs", "institution_id=eq." + INSTITUTION_ID)
        require(len(clean_rows) == 1 and clean_rows[0]["status"] == "pending", "cleansing-recovery", "CLEANSING_NOT_SINGLE_PERSISTED")
        print("phase=cleansing-failure-recovery|result=PASS|rows=1")

        CURRENT_PHASE = "enrichment-failure-recovery"
        enricher = EnrichmentWorker()
        enricher._mock_only = True
        pending_clean = enricher.get_pending_cleansed(limit=5, institution_id=INSTITUTION_ID)
        require(len(pending_clean) == 1, "enrichment-setup", "PENDING_CLEANSED_NOT_FOUND")
        enrich_fault = "POST:/rpc/atomic_enrichment_promote"
        FAULTS[enrich_fault] = 1
        enrichment_failed = False
        try:
            enricher.enrich_record(pending_clean[0])
        except RuntimeError:
            enrichment_failed = True
        require(enrichment_failed, "enrichment-failure", "INJECTED_FAILURE_NOT_PROPAGATED")
        enriched_after_fail = fetch_rows(client, "enriched_programs", "institution_id=eq." + INSTITUTION_ID)
        clean_after_enrich_fail = fetch_rows(client, "cleansed_programs", "institution_id=eq." + INSTITUTION_ID)
        require(FAILURES_SEEN.get(enrich_fault) == 1 and enriched_after_fail == [] and clean_after_enrich_fail[0]["status"] == "pending", "enrichment-failure", "FAILURE_PARTIALLY_PROMOTED")
        require(enricher.enrich_record(pending_clean[0]) is True, "enrichment-recovery", "ENRICHMENT_RECOVERY_FAILED")
        require(enricher.enrich_record(pending_clean[0]) is True, "enrichment-idempotency", "ENRICHMENT_REPLAY_FAILED")
        enriched_rows = fetch_rows(client, "enriched_programs", "institution_id=eq." + INSTITUTION_ID)
        clean_rows = fetch_rows(client, "cleansed_programs", "institution_id=eq." + INSTITUTION_ID)
        require(len(enriched_rows) == 1 and enriched_rows[0]["status"] == "pending" and clean_rows[0]["status"] == "enriched", "enrichment-recovery", "ENRICHMENT_NOT_SINGLE_PERSISTED")
        print("phase=enrichment-failure-recovery|result=PASS|rows=1")

        CURRENT_PHASE = "sync-worker-construction"
        syncer = SyncVectorWorker()
        CURRENT_PHASE = "sync-read-pending"
        pending_enriched = syncer.get_pending_enriched(limit=5, institution_id=INSTITUTION_ID)
        require(len(pending_enriched) == 1, "sync-setup", "PENDING_ENRICHED_NOT_FOUND")
        integrity_ping_module.resolve_public_host = lambda _host: ["93.184.216.34"]
        sync_fault = "POST:/courses"
        FAULTS[sync_fault] = 1
        CURRENT_PHASE = "sync-injected-upstream-failure"
        first_sync = syncer.sync_to_production(pending_enriched[0])
        require(first_sync is False and FAILURES_SEEN.get(sync_fault) == 1, "sync-failure", "SYNC_FAILURE_NOT_REPORTED")
        CURRENT_PHASE = "sync-verify-failure-state"
        enriched_after_sync_fail = fetch_rows(client, "enriched_programs", "institution_id=eq." + INSTITUTION_ID)
        require(enriched_after_sync_fail[0]["status"] == "error" and fetch_rows(client, "courses", "", service=True) == [], "sync-failure", "SYNC_FAILURE_STATE_NOT_PERSISTED")
        CURRENT_PHASE = "sync-operator-requeue"
        client.patch_raise("enriched_programs", "id=eq." + enriched_after_sync_fail[0]["id"], {"status": "pending"})
        retry_record = fetch_rows(client, "enriched_programs", "institution_id=eq." + INSTITUTION_ID)[0]
        CURRENT_PHASE = "sync-recovery"
        require(syncer.sync_to_production(retry_record) is True, "sync-recovery", "SYNC_RECOVERY_FAILED")
        synced_courses = fetch_rows(client, "courses", "", service=True)
        synced_record = fetch_rows(client, "enriched_programs", "institution_id=eq." + INSTITUTION_ID)
        require(len(synced_courses) == 1 and synced_record[0]["status"] == "synced", "sync-recovery", "SYNC_NOT_SINGLE_PERSISTED")
        CURRENT_PHASE = "sync-idempotency"
        require(syncer.sync_to_production(synced_record[0]) is True, "sync-idempotency", "SYNC_REPLAY_FAILED")
        require(len(fetch_rows(client, "courses", "", service=True)) == 1, "sync-idempotency", "SYNC_REPLAY_DUPLICATED_COURSE")
        print("phase=sync-failure-manual-requeue-recovery|result=PASS|courses=1")
        print("phase=pipeline-persistent-handoff|result=PASS|staging=1|cleansed=1|enriched=1|courses=1")
    finally:
        proxy.shutdown()
        proxy.server_close()


if __name__ == "__main__":
    try:
        run()
    except PhaseFailure as failure:
        print(f"phase={failure.phase}|result=FAIL|code={failure.code}")
        raise SystemExit(1)
    except Exception as exc:  # Sanitized: never emit exception text or payloads.
        code = type(exc).__name__.upper().replace("ERROR", "ERR")[:40]
        allowed = {
            "h3req1_pipeline_postgrest_pg17_integration.py",
            "universal_harvester.py",
            "db_client.py",
        }
        frames = [frame for frame in traceback.extract_tb(exc.__traceback__) if frame.filename.rsplit("/", 1)[-1] in allowed]
        frame_label = ",".join(
            f"{frame.filename.rsplit('/', 1)[-1]}:{frame.lineno}:{frame.name}"
            for frame in frames[-3:]
        ) or "unavailable"
        context_match = re.search(r"DB select failed for ([a-z_]+): HTTP ([1-5][0-9]{2})", str(exc))
        context = f"|table={context_match.group(1)}|http_status={context_match.group(2)}" if context_match else ""
        print(f"phase={CURRENT_PHASE}|result=FAIL|code={code}|frames={frame_label}{context}")
        raise SystemExit(1)
