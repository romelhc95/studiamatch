"""Repository-level guards for the manual FG2 cohort handoff."""

import ast
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import textwrap
import time
import uuid
from types import SimpleNamespace
from urllib.parse import unquote

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/production_pipeline.yml"


def _valid_provider_pillars() -> dict:
    return {
        "official_name": "Synthetic course",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250.0,
        "requirements": ["Synthetic requirement"],
        "graduate_profile": "Synthetic graduate profile",
        "target_audience": "Synthetic audience",
        "objectives": "Synthetic objectives",
        "benefits": "Synthetic benefits",
        "certification": "Synthetic certification",
        "curriculum_summary": {"pilares": ["Synthetic curriculum"]},
        "modality": "Remoto",
        "primary_campus": "Virtual",
        "degree_type": "Curso",
        "start_date": None,
        "categories": ["Data"],
        "difficulty_level": "Básico",
        "ai_summary": "Synthetic summary",
    }


def _openai_wire_payload(pillars: dict | None = None) -> bytes:
    return json.dumps({
        "status": "completed",
        "output": [{
            "type": "message",
            "content": [{
                "type": "output_text",
                "text": json.dumps(pillars or _valid_provider_pillars(), ensure_ascii=False),
            }],
        }],
    }, ensure_ascii=False).encode("utf-8")


class FileBackedFG2E2EDatabase:
    """Disposable PostgREST-shaped fixture shared only through a JSON file."""

    supabase_url = "https://fixture-postgrest.invalid"

    def __init__(self) -> None:
        self.path = Path(os.environ["FG2_E2E_STATE"])

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, state: dict) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)

    @staticmethod
    def _matches(row: dict, filters: str) -> bool:
        if not filters:
            return True
        regex_match = re.search(r"(?:^|&)url=match\.([^&]+)", filters)
        if regex_match:
            pattern = unquote(regex_match.group(1))
            if not re.search(pattern, str(row.get("url") or ""), re.IGNORECASE):
                return False
        for condition in filters.split("&"):
            if condition.startswith("url=match."):
                continue
            if "=" not in condition:
                continue
            field, expression = condition.split("=", 1)
            actual = row.get(field)
            if expression.startswith("eq."):
                expected = unquote(expression[3:])
                if str(actual) != expected:
                    return False
            elif expression.startswith("in.(") and expression.endswith(")"):
                allowed = {unquote(value) for value in expression[4:-1].split(",")}
                if str(actual) not in allowed:
                    return False
            elif expression.startswith("ilike."):
                expected = unquote(expression[6:]).strip("*").lower()
                if expected not in str(actual or "").lower():
                    return False
            elif expression.startswith("match."):
                if not re.search(unquote(expression[6:]), str(actual or ""), re.IGNORECASE):
                    return False
        return True

    @staticmethod
    def _project(rows: list[dict], columns: str | None) -> list[dict]:
        if not columns or columns == "*":
            return [dict(row) for row in rows]
        names = [name.strip() for name in columns.split(",") if name.strip()]
        return [{name: row.get(name) for name in names} for row in rows]

    def _select(self, table: str, filters: str = "", columns: str | None = None,
                limit: int | None = None, order: str | None = None) -> list[dict]:
        rows = [row for row in self._read()["tables"].get(table, []) if self._matches(row, filters)]
        if order:
            field = order.split(".", 1)[0]
            descending = ".desc" in order
            nulls_first = ".nullsfirst" in order
            rows.sort(key=lambda row: (row.get(field) is not None, row.get(field) or "") if nulls_first else (row.get(field) is None, row.get(field) or ""), reverse=descending)
        if limit is not None:
            rows = rows[:limit]
        return self._project(rows, columns)

    def select_pipeline_raise(self, table, filters="", columns=None, limit=None, order=None, **_kwargs):
        return self._select(table, filters, columns, limit, order)

    def select_service_raise(self, table, filters="", columns=None, limit=None, order=None, **_kwargs):
        return self._select(table, filters, columns, limit, order)

    def select_all_pipeline(self, table, filters="", columns=None, limit=None, order=None, **_kwargs):
        return self._select(table, filters, columns, limit, order)

    def select_all_service(self, table, filters="", columns=None, limit=None, order=None, **_kwargs):
        return self._select(table, filters, columns, limit, order)

    def select(self, table, filters="", columns=None, limit=None, **kwargs):
        return self._select(table, filters, columns, limit, kwargs.get("order"))

    @staticmethod
    def _new_id(table: str, key: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fg2-e2e:{table}:{key}"))

    def insert(self, table, data):
        row = dict(data)
        row.setdefault("id", self._new_id(table, str(row.get("url") or len(self._read()["tables"].get(table, [])))))
        state = self._read()
        state["tables"].setdefault(table, []).append(row)
        self._write(state)
        return [dict(row)]

    def patch(self, table, filters, data):
        state = self._read()
        matches = [row for row in state["tables"].get(table, []) if self._matches(row, filters)]
        for row in matches:
            row.update(data)
        self._write(state)
        return [dict(row) for row in matches]

    def patch_raise(self, table, filters, data):
        return self.patch(table, filters, data)

    def patch_exact_one_raise(self, table, filters, data, expected_id):
        state = self._read()
        matches = [
            row for row in state["tables"].get(table, [])
            if str(row.get("id")) == str(expected_id) and self._matches(row, filters)
        ]
        if len(matches) != 1:
            raise AssertionError(f"fixture expected exactly one {table} row for patch")
        matches[0].update(data)
        self._write(state)
        return dict(matches[0])

    def upsert(self, table, data, on_conflict="url", **_kwargs):
        incoming = data if isinstance(data, list) else [data]
        state = self._read()
        stored = state["tables"].setdefault(table, [])
        results = []
        for payload in incoming:
            row = next((candidate for candidate in stored if candidate.get(on_conflict) == payload.get(on_conflict)), None)
            if row is None:
                row = dict(payload)
                row.setdefault("id", self._new_id(table, str(payload.get(on_conflict))))
                stored.append(row)
            else:
                row.update(payload)
            results.append(dict(row))
        self._write(state)
        return results

    def rpc(self, function, params):
        if function == "lock_staging_records":
            return None
        return self.rpc_raise(function, params)

    def rpc_raise(self, function, params):
        state = self._read()
        tables = state["tables"]
        if function == "atomic_cleansing_promote":
            for payload in params["p_cleansed_data"]:
                row = next((candidate for candidate in tables.setdefault("cleansed_programs", []) if candidate.get("staging_id") == payload.get("staging_id")), None)
                if row is None:
                    row = dict(payload, id=self._new_id("cleansed_programs", str(payload.get("staging_id"))))
                    tables["cleansed_programs"].append(row)
                else:
                    row.update(payload)
            for staging_id in params["p_staging_ids"]:
                row = next(candidate for candidate in tables["staging_raw"] if candidate.get("id") == staging_id)
                row["status"] = "processed"
            state.setdefault("rpc_events", []).append(function)
            self._write(state)
            return [{"success": True}]
        if function == "atomic_enrichment_promote":
            if state.get("fail_next_enrichment_rpc"):
                state["fail_next_enrichment_rpc"] = False
                state.setdefault("rpc_events", []).append("atomic_enrichment_promote_failed_once")
                self._write(state)
                raise RuntimeError("synthetic enrichment persistence interruption")
            for payload in params["p_enriched_data"]:
                row = next((candidate for candidate in tables.setdefault("enriched_programs", []) if candidate.get("cleansed_id") == payload.get("cleansed_id")), None)
                if row is None:
                    row = dict(payload, id=self._new_id("enriched_programs", str(payload.get("cleansed_id"))), status="pending")
                    tables["enriched_programs"].append(row)
                else:
                    row.update(payload)
                    row["status"] = "pending"
            clean = next(candidate for candidate in tables["cleansed_programs"] if candidate.get("id") == params["p_cleansed_id"])
            clean["status"] = "enriched"
            state.setdefault("rpc_events", []).append(function)
            self._write(state)
            return [{"success": True}]
        if function == "h2_update_course_quality":
            course_id = params["p_course_id"]
            rows = tables.setdefault("course_editorial_state", [])
            row = next((candidate for candidate in rows if candidate.get("course_id") == course_id), None)
            if row is None:
                row = {
                    "course_id": course_id,
                    "editorial_status": "pending_review",
                    "manual_overrides": {},
                    "manual_updated_at": None,
                }
                rows.append(row)
            row.update({
                "quality_status": "synthetic-quality-evaluated",
                "missing_fields": params.get("p_missing_fields"),
                "field_sources": params.get("p_field_sources"),
                "field_timestamps": params.get("p_field_timestamps"),
            })
            state.setdefault("rpc_events", []).append(function)
            self._write(state)
            return [{"success": True}]
        raise AssertionError(f"unexpected fixture RPC: {function}")


class FixtureResponse:
    def __init__(self, url: str, status_code: int, body: bytes) -> None:
        self.url = url
        self.status_code = status_code
        self.headers = {"content-type": "text/html" if status_code == 200 else "text/plain"}
        self.content = body
        self.text = body.decode("utf-8", errors="replace")
        self._body = body

    async def aiter_content(self, chunk_size=None):
        if self._body:
            yield self._body

    async def aclose(self):
        return None

    def close(self):
        return None


class FixtureAsyncSession:
    def __init__(self, **_kwargs) -> None:
        self.max_redirects = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, url, **_kwargs):
        path = Path(os.environ["FG2_E2E_STATE"])
        state = json.loads(path.read_text(encoding="utf-8"))
        status = state.get("http_status_by_path", {}).get(url, 200)
        state.setdefault("http_requests", []).append({"url": url, "status": status})
        path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        if status != 200:
            return FixtureResponse(url, status, b"")
        label = "Programa nuevo" if url.endswith("/programs/new/") else "Programa actualizado"
        body = (
            "<!doctype html><html><head><title>" + label + "</title>"
            "<meta name=\"description\" content=\"Formación sintética verificable.\"></head>"
            "<body><main><h1>" + label + "</h1><p>Duración: 6 meses. Modalidad Remoto. "
            "Inversión S/ 1250.</p><h2>Objetivos</h2><p>Aprender con evidencia sintética.</p>"
            "<h2>Requisitos</h2><p>Conocimientos iniciales.</p><h2>Beneficios</h2>"
            "<p>Ejercicios prácticos.</p></main></body></html>"
        ).encode("utf-8")
        return FixtureResponse(url, 200, body)


class FixtureProviderOrchestrator:
    def __init__(self, providers, logger=None):
        self.providers = list(providers)
        self.logger = logger

    @property
    def mode(self):
        return os.getenv("FG2_E2E_PROVIDER_MODE", "success")

    def run_health_checks(self):
        for provider in self.providers:
            provider._healthy = self.mode != "all_unhealthy"
        return [provider.name for provider in self.providers]

    def call_with_fallback(self, _prompt, _clean_fn, validate_fn=None):
        if self.mode == "no_result":
            return None, None
        payload = {
            "official_name": "Programa sintético verificado",
            "duration_text": "6 meses",
            "duration_months": 6,
            "total_cost_est": 1250,
            "requirements": ["Conocimientos iniciales"],
            "graduate_profile": "Perfil sintético",
            "target_audience": "Personas en formación",
            "objectives": "Aprender con evidencia sintética",
            "benefits": "Ejercicios prácticos",
            "certification": "Constancia sintética",
            "curriculum_summary": {"pilares": ["Contenido sintético"]},
            "modality": "Remoto",
            "primary_campus": "Virtual",
            "degree_type": "Curso",
            "start_date": None,
            "categories": ["Data"],
            "difficulty_level": "Básico",
            "ai_summary": "Resumen de curso sintético.",
        }
        if validate_fn is not None and validate_fn(payload) is not True:
            return None, None
        return payload, "OpenAI"

    def _all_degraded(self):
        return self.mode == "dynamic_degraded"

    def summary(self):
        return "fixture-provider: 2/2"


def install_fg2_e2e_adapters() -> None:
    """Install only synthetic DB/HTTP/provider boundaries in child processes."""
    import socket
    import curl_cffi.requests as curl_requests
    import shared.db_client as db_client
    import shared.utils as shared_utils

    db_client.get_db_client = FileBackedFG2E2EDatabase
    curl_requests.AsyncSession = FixtureAsyncSession
    shared_utils.ProviderOrchestrator = FixtureProviderOrchestrator
    original_getaddrinfo = socket.getaddrinfo

    def fixture_getaddrinfo(host, port, *args, **kwargs):
        if str(host).lower() == "fg2-synthetic.example":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        return original_getaddrinfo(host, port, *args, **kwargs)

    socket.getaddrinfo = fixture_getaddrinfo


def test_bounded_first_run_is_opt_in_and_does_not_change_the_schedule() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    header = workflow.split("concurrency:", 1)[0]

    assert "cron: '0 5 * * *'" in header
    assert "bounded_first_run:" in header
    bounded_input = header.split("bounded_first_run:", 1)[1].split("concurrency:", 1)[0]
    assert "type: boolean" in bounded_input
    assert "default: false" in bounded_input
    assert "required: false" in bounded_input
    assert "github.event_name == 'workflow_dispatch' && inputs.bounded_first_run" in workflow
    for field in (
        "approved_lot_reference:",
        "approved_lot_sha256:",
        "approved_lot_manifest_b64:",
    ):
        assert field in header
    assert "--approved-lot-manifest \"$RUNNER_TEMP/fg2-approved-lot.json\"" in workflow
    assert "--approved-lot-reference \"$FG2_APPROVED_LOT_REFERENCE\"" in workflow
    assert "--approved-lot-sha256 \"$FG2_APPROVED_LOT_SHA256\"" in workflow
    assert "FG2_APPROVED_LOT_MANIFEST_B64: ${{ inputs.approved_lot_manifest_b64 }}" in workflow


def test_controlled_manifest_is_bound_through_each_downstream_job() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "cohort_manifest_b64: ${{ steps.harvest.outputs.cohort_manifest_b64 }}" in workflow
    assert "cohort_manifest_sha256: ${{ steps.harvest.outputs.cohort_manifest_sha256 }}" in workflow
    assert workflow.count("Restore exact controlled cohort manifest") == 3
    assert "Preserve controlled FG2 cohort manifest for review and recovery" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "if-no-files-found: ignore" in workflow
    assert workflow.count("--cohort-manifest-sha256 \"$FG2_COHORT_MANIFEST_SHA256\"") == 3

    for job in ("phase_1_5_cleansing", "phase_2_enrichment", "phase_3_sync"):
        section = workflow.split(f"  {job}:", 1)[1].split("\n  phase_", 1)[0]
        assert "needs: [production_control_preflight, phase_1_harvesting" in section
        assert "FG2_COHORT_MANIFEST_SHA256" in section


def test_ordinary_harvest_and_downstream_paths_remain_available() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "python3 scripts/core/master_orchestrator.py --limit 10 --skip-cleansing" in workflow
    assert "python scripts/core/cleansing_worker.py\n" in workflow
    assert "python scripts/core/enrichment_worker.py\n" in workflow
    assert "python scripts/core/sync_vector_worker.py\n" in workflow
    assert "production_control_preflight.sh FG2-HARVEST --enforce" in workflow
    assert "production_control_preflight.sh FG2-CLEANSING --enforce" in workflow
    assert "production_control_preflight.sh FG2-ENRICHMENT --enforce" in workflow
    assert "production_control_preflight.sh FG2-SYNC --enforce" in workflow


def test_production_manual_and_schedule_workers_require_real_enrichment() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    production_guard = (
        "FG2_REQUIRE_REAL_PROVIDER: ${{ github.ref == 'refs/heads/main' && "
        "(github.event_name == 'schedule' || github.event_name == 'workflow_dispatch') }}"
    )
    for job in ("phase_2_enrichment", "phase_3_sync"):
        section = workflow.split(f"  {job}:", 1)[1].split("\n  phase_", 1)[0]
        assert production_guard in section

    assert "default: false" in workflow.split("bounded_first_run:", 1)[1].split("concurrency:", 1)[0]


def test_openai_secret_is_bound_only_to_backend_enrichment_step_for_manual_and_schedule() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    enrichment = workflow.split("      - name: Multicloud AI Enrichment", 1)[1].split("\n  # 🚉 STATION 3", 1)[0]
    assert "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}" in enrichment
    assert workflow.count("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}") == 1
    assert "OPENAI_API_KEY" not in workflow.split("jobs:", 1)[1].split("  phase_2_enrichment:", 1)[0]
    assert "github.event_name == 'schedule'" in workflow.split("  phase_2_enrichment:", 1)[1].split("\n  phase_", 1)[0]
    assert "github.event_name == 'workflow_dispatch'" in workflow.split("  phase_2_enrichment:", 1)[1].split("\n  phase_", 1)[0]
    sync = workflow.split("      - name: Sync to Production Courses", 1)[1].split("\n\n  phase_4_audit", 1)[0]
    assert "OPENAI_API_KEY" not in sync


def test_main_schedule_propagates_a_run_scoped_manifest_to_all_workers() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "FG2_SCHEDULED_COHORT: ${{ github.event_name == 'schedule' && github.ref == 'refs/heads/main' }}" in workflow
    assert "--scheduled-cohort --cohort-manifest \"$RUNNER_TEMP/fg2-cohort-manifest.json\"" in workflow
    assert "FG2_COHORT_SCOPED: ${{ (github.event_name == 'schedule' && github.ref == 'refs/heads/main')" in workflow
    assert "if: always() && (github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && (inputs.bounded_first_run || inputs.resume_enrichment_from_272)))" in workflow
    assert workflow.count("if: env.FG2_COHORT_SCOPED == 'true'") == 3

    for job, script in (
        ("phase_1_5_cleansing", "cleansing_worker.py"),
        ("phase_2_enrichment", "enrichment_worker.py"),
        ("phase_3_sync", "sync_vector_worker.py"),
    ):
        section = workflow.split(f"  {job}:", 1)[1].split("\n  phase_", 1)[0]
        assert "FG2_COHORT_SCOPED" in section
        assert f"python scripts/core/{script} --cohort-manifest" in section
        assert f"python scripts/core/{script}\n" in section
        assert "Restore exact controlled cohort manifest" in section



def _workflow_job_condition(workflow: str, job: str) -> str:
    section = workflow.split(f"  {job}:", 1)[1]
    if job != "phase_4_audit":
        section = section.split("\n  phase_", 1)[0]
    multiline = re.search(r"(?m)^    if: >-\n((?:      .*\n?)+)", section)
    if multiline:
        return " ".join(line.strip() for line in multiline.group(1).splitlines())
    single_line = re.search(r"(?m)^    if: (.+)$", section)
    assert single_line, f"{job} must define a job-level condition"
    return single_line.group(1).strip()


def _evaluate_workflow_job_condition(
    expression: str,
    *,
    resume: bool,
    statuses: dict[str, str],
    allow_writer: bool = True,
    event_name: str = "workflow_dispatch",
    workflow_cancelled: bool = False,
) -> bool:
    bindings = {
        "needs.production_control_preflight.outputs.allow_writer": "true" if allow_writer else "false",
        "needs.main_ref_guard.result": statuses.get("main_ref_guard", ""),
        "needs.production_control_preflight.result": statuses.get("production_control_preflight", ""),
        "needs.phase_1_harvesting.result": statuses.get("phase_1_harvesting", ""),
        "needs.phase_1_5_cleansing.result": statuses.get("phase_1_5_cleansing", ""),
        "needs.phase_2_enrichment.result": statuses.get("phase_2_enrichment", ""),
        "needs.phase_3_sync.result": statuses.get("phase_3_sync", ""),
        "inputs.resume_enrichment_from_272": resume,
        "github.event_name": event_name,
    }
    has_status_function = bool(re.search(r"\b(?:always|success|failure|cancelled)\(\)", expression))
    for token, value in sorted(bindings.items(), key=lambda item: len(item[0]), reverse=True):
        expression = expression.replace(token, repr(value))
    expression = expression.replace("always()", "True")
    expression = expression.replace("!cancelled()", "False" if workflow_cancelled else "True")
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"(?<!['\"])\btrue\b(?!['\"])", "True", expression, flags=re.IGNORECASE)
    expression = re.sub(r"(?<!['\"])\bfalse\b(?!['\"])", "False", expression, flags=re.IGNORECASE)

    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (bool, str)):
            return node.value
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return all(visit(value) for value in node.values)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            return any(visit(value) for value in node.values)
        if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
            left, right = visit(node.left), visit(node.comparators[0])
            if isinstance(node.ops[0], ast.Eq):
                return left == right
            if isinstance(node.ops[0], ast.NotEq):
                return left != right
        raise AssertionError(f"unsupported workflow condition expression: {ast.dump(node)}")

    condition_result = bool(visit(tree))
    if not has_status_function:
        upstream = {
            "main_ref_guard",
            "production_control_preflight",
            "phase_1_harvesting",
            "phase_1_5_cleansing",
            "phase_2_enrichment",
        }
        if "needs.phase_3_sync.result" in expression:
            upstream.add("phase_3_sync")
        condition_result = condition_result and all(statuses.get(job) == "success" for job in upstream)
    return condition_result


@pytest.mark.parametrize(
    ("resume", "overrides", "allow_writer", "workflow_cancelled", "expected"),
    [
        pytest.param(True, {"phase_1_5_cleansing": "skipped"}, True, False, True, id="recovery-cleansing-skipped-enrichment-success"),
        pytest.param(True, {"phase_2_enrichment": "failure", "phase_3_sync": "skipped"}, True, False, False, id="recovery-enrichment-failed-blocks-writes"),
        pytest.param(True, {"phase_2_enrichment": "cancelled", "phase_3_sync": "skipped"}, True, False, False, id="recovery-enrichment-cancelled-blocks-writes"),
        pytest.param(True, {"phase_1_5_cleansing": "failure"}, True, False, False, id="recovery-cleansing-failure-not-accepted-as-skip"),
        pytest.param(True, {"phase_1_5_cleansing": "success"}, True, False, False, id="recovery-only-allows-planned-cleansing-skip"),
        pytest.param(False, {"phase_1_5_cleansing": "success"}, True, False, True, id="normal-mode-keeps-cleansing-success-path"),
        pytest.param(False, {"phase_1_5_cleansing": "skipped"}, True, False, False, id="normal-mode-does-not-allow-skipped-cleansing"),
        pytest.param(False, {"phase_1_5_cleansing": "failure"}, True, False, False, id="normal-mode-cleansing-failure-blocks-writes"),
        pytest.param(True, {"production_control_preflight": "failure"}, True, False, False, id="failed-production-preflight-blocks-writes"),
        pytest.param(True, {"phase_1_harvesting": "cancelled"}, True, False, False, id="cancelled-harvesting-blocks-writes"),
        pytest.param(True, {}, True, True, False, id="workflow-cancellation-blocks-downstream"),
        pytest.param(True, {}, False, False, False, id="writer-pause-blocks-downstream"),
    ],
)
def test_sync_and_ca1_allow_only_the_planned_recovery_skip_and_require_successful_predecessors(
    resume: bool,
    overrides: dict[str, str],
    allow_writer: bool,
    workflow_cancelled: bool,
    expected: bool,
) -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    statuses = {
        "main_ref_guard": "success",
        "production_control_preflight": "success",
        "phase_1_harvesting": "success",
        "phase_1_5_cleansing": "success",
        "phase_2_enrichment": "success",
        "phase_3_sync": "success",
    }
    statuses.update(overrides)

    for job in ("phase_3_sync", "phase_4_audit"):
        actual = _evaluate_workflow_job_condition(
            _workflow_job_condition(workflow, job),
            resume=resume,
            statuses=statuses,
            allow_writer=allow_writer,
            workflow_cancelled=workflow_cancelled,
        )
        assert actual is expected, job


@pytest.mark.parametrize(
    ("resume", "cleansing", "preflight", "harvest", "workflow_cancelled", "expected"),
    [
        pytest.param(True, "skipped", "success", "success", False, True, id="recovery-enrichment-runs-after-planned-skip"),
        pytest.param(True, "failure", "success", "success", False, False, id="recovery-enrichment-blocked-by-cleansing-failure"),
        pytest.param(True, "cancelled", "success", "success", False, False, id="recovery-enrichment-blocked-by-cleansing-cancellation"),
        pytest.param(True, "success", "success", "success", False, False, id="recovery-enrichment-requires-exact-planned-skip"),
        pytest.param(False, "success", "success", "success", False, True, id="normal-enrichment-requires-cleansing-success"),
        pytest.param(False, "skipped", "success", "success", False, False, id="normal-enrichment-rejects-skipped-cleansing"),
        pytest.param(False, "failure", "success", "success", False, False, id="normal-enrichment-rejects-cleansing-failure"),
        pytest.param(True, "skipped", "failure", "success", False, False, id="enrichment-rejects-failed-production-preflight"),
        pytest.param(True, "skipped", "success", "cancelled", False, False, id="enrichment-rejects-cancelled-harvesting"),
        pytest.param(True, "skipped", "success", "success", True, False, id="enrichment-rejects-workflow-cancellation"),
    ],
)
def test_enrichment_allows_only_successful_cleansing_or_the_planned_recovery_skip(
    resume: bool,
    cleansing: str,
    preflight: str,
    harvest: str,
    workflow_cancelled: bool,
    expected: bool,
) -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    statuses = {
        "main_ref_guard": "success",
        "production_control_preflight": preflight,
        "phase_1_harvesting": harvest,
        "phase_1_5_cleansing": cleansing,
        "phase_2_enrichment": "success",
        "phase_3_sync": "success",
    }
    actual = _evaluate_workflow_job_condition(
        _workflow_job_condition(workflow, "phase_2_enrichment"),
        resume=resume,
        statuses=statuses,
        workflow_cancelled=workflow_cancelled,
    )
    assert actual is expected

def test_post272_recovery_uses_pinned_artifact_and_runs_only_downstream_stations() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    header = workflow.split("concurrency:", 1)[0]
    recovery_input = header.split("resume_enrichment_from_272:", 1)[1].split("approved_lot_reference:", 1)[0]
    assert "type: boolean" in recovery_input
    assert "default: false" in recovery_input
    assert "FG2_RECOVERY_SOURCE_VERIFIED run=45342980592 attempt=1" in workflow
    assert "artifact-ids: 14896234555" in workflow
    assert "run-id: 45342980592" in workflow
    download_step = workflow.split('      - name: "Download exact #272 cohort artifact"', 1)[1].split(
        '      - name: "Verify downloaded #272 manifest bytes"', 1
    )[0]
    assert "merge-multiple: true" in download_step
    assert "sha256:a313fbcbcece66f61e66a91d174126051a26e4d8461327514912243b16ee4864" in workflow
    assert "5bb5f594b3e49c1369cd50d233db72b852e1ca3d48d8451a4a523ca7c50c0450" in workflow
    manifest_path = "$RUNNER_TEMP/fg2-recovery-source/fg2-cohort-manifest.json"
    verify_step = workflow.split('      - name: "Verify downloaded #272 manifest bytes"', 1)[1].split(
        "      - name: Setup Python", 1
    )[0]
    assert f'python3 - "{manifest_path}" <<\'PY\'' in verify_step
    assert f'--source-cohort-manifest "{manifest_path}"' in workflow
    assert "reason=manifest_file_missing" in verify_step
    assert "reason=manifest_digest_mismatch" in verify_step
    assert "--prepare-post272-enrichment-recovery" in workflow
    assert "--source-cohort-manifest" in workflow
    assert "if: env.FG2_RECOVERY_ENRICHMENT != 'true'\n        run: playwright install chromium" in workflow
    preflight = workflow.split("  production_control_preflight:", 1)[1].split("  # 🚉 STATION 1:", 1)[0]
    assert "FG2_RECOVERY_ENRICHMENT" in preflight
    assert "production_control_preflight.sh FG2-ENRICHMENT" in preflight
    assert "production_control_preflight.sh FG2-HARVEST" in preflight
    cleansing = workflow.split("  phase_1_5_cleansing:", 1)[1].split("  phase_2_enrichment:", 1)[0]
    assert "inputs.resume_enrichment_from_272 != true" in cleansing
    enrichment = workflow.split("  phase_2_enrichment:", 1)[1].split("  phase_3_sync:", 1)[0]
    assert "inputs.resume_enrichment_from_272 == true" in enrichment
    sync = workflow.split("  phase_3_sync:", 1)[1].split("  phase_4_audit:", 1)[0]
    assert "needs.phase_2_enrichment.result == 'success'" in sync
    audit = workflow.split("  phase_4_audit:", 1)[1]
    assert "needs.phase_3_sync.result == 'success'" in audit
    assert "CA1 Audit Boundary" in audit
    assert "FG2_BOUNDED_FIRST_RUN: ${{ github.event_name == 'workflow_dispatch' && inputs.bounded_first_run }}" in workflow
    assert "FG2_RESUME_ENRICHMENT: ${{ github.event_name == 'workflow_dispatch' && inputs.resume_enrichment_from_272 }}" in workflow
    assert '"$FG2_BOUNDED_FIRST_RUN" == "true" && "$FG2_RESUME_ENRICHMENT" == "true"' in workflow


def test_post272_artifact_layout_is_flattened_verified_and_passed_to_orchestrator(tmp_path: Path) -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    download_step = workflow.split('      - name: "Download exact #272 cohort artifact"', 1)[1].split(
        '      - name: "Verify downloaded #272 manifest bytes"', 1
    )[0]
    assert "artifact-ids: 14896234555" in download_step
    assert "merge-multiple: true" in download_step
    assert "path: ${{ runner.temp }}/fg2-recovery-source" in download_step

    verify_step = workflow.split('      - name: "Verify downloaded #272 manifest bytes"', 1)[1].split(
        "      - name: Setup Python", 1
    )[0]
    script_match = re.search(r"        run: \|\n(?P<run>.*)", verify_step, re.DOTALL)
    assert script_match is not None
    heredoc_match = re.search(r"<<'PY'\n(?P<script>.*?)\n          PY", script_match.group("run"), re.DOTALL)
    assert heredoc_match is not None
    verifier_script = textwrap.dedent(heredoc_match.group("script"))

    pinned_digest = "5bb5f594b3e49c1369cd50d233db72b852e1ca3d48d8451a4a523ca7c50c0450"
    synthetic_manifest = b'{"fixture":"deferred","entries":[]}'
    expected_digest = hashlib.sha256(synthetic_manifest).hexdigest()
    assert verifier_script.count(pinned_digest) == 2
    verifier_script = verifier_script.replace(pinned_digest, expected_digest)

    runner_temp = tmp_path / "runner-temp"
    artifact_name = "fg2-bounded-cohort-45342980592-1"
    nested_manifest = runner_temp / "fg2-recovery-source" / artifact_name / "fg2-cohort-manifest.json"
    nested_manifest.parent.mkdir(parents=True)
    nested_manifest.write_bytes(synthetic_manifest)

    # Model the pinned action's merge-multiple output: one selected artifact's
    # contents are placed directly under the configured destination directory.
    flattened_manifest = runner_temp / "fg2-recovery-source" / "fg2-cohort-manifest.json"
    flattened_manifest.write_bytes(nested_manifest.read_bytes())
    assert flattened_manifest.read_bytes() == synthetic_manifest

    def verify(path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-", str(path)],
            input=verifier_script,
            capture_output=True,
            check=False,
            text=True,
        )

    valid = verify(flattened_manifest)
    assert valid.returncode == 0, valid.stderr
    assert f"sha256={expected_digest}" in valid.stdout

    missing = verify(runner_temp / "fg2-recovery-source" / "missing.json")
    assert missing.returncode != 0
    assert "reason=manifest_file_missing" in missing.stderr
    assert "reason=manifest_digest_mismatch" not in missing.stderr

    flattened_manifest.write_bytes(synthetic_manifest + b" ")
    altered = verify(flattened_manifest)
    assert altered.returncode != 0
    assert "reason=manifest_digest_mismatch" in altered.stderr
    assert "reason=manifest_file_missing" not in altered.stderr

    orchestrator_call = (
        '--source-cohort-manifest "$RUNNER_TEMP/fg2-recovery-source/fg2-cohort-manifest.json"'
    )
    assert orchestrator_call in workflow


def test_every_downstream_cli_rejects_an_unhashed_manifest_before_startup() -> None:
    for script in (
        "cleansing_worker.py",
        "enrichment_worker.py",
        "sync_vector_worker.py",
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/core" / script),
                "--cohort-manifest",
                "/tmp/fg2-manifest-must-not-be-opened.json",
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 2, (script, result.stderr)
        assert "controlled cohort requires an expected SHA-256" in result.stderr, script


@pytest.mark.parametrize(
    ("discovery_mode", "seed_layout", "approved_discovery_is_source"),
    [
        ("hardcoded_urls", "course_details", False),
        ("sitemap_bfs", "catalog_sources", False),
        ("sitemap_bfs", "catalog_sources", True),
    ],
)
def test_fg2_workflow_entrypoints_complete_across_runner_manifest_handoffs(
    tmp_path: Path,
    discovery_mode: str,
    seed_layout: str,
    approved_discovery_is_source: bool,
) -> None:
    """Run the YAML's actual Python entrypoints with isolated fixture boundaries."""
    from scripts.core.fg2_bounded_run import (
        FG2_LIMITS,
        stable_json_sha256,
        url_sha256,
        validate_controlled_profile,
    )

    institution_id = "00000000-0000-0000-0000-000000000258"
    refresh_course_id = "70000000-0000-0000-0000-000000000258"
    outside_staging_id = "40000000-0000-0000-0000-000000000258"
    outside_clean_id = "50000000-0000-0000-0000-000000000258"
    outside_enriched_id = "60000000-0000-0000-0000-000000000258"
    category_id = "10000000-0000-0000-0000-000000000258"
    origin = "https://fg2-synthetic.example"
    new_url = f"{origin}/programs/new"
    refresh_url = f"{origin}/programs/refresh"
    blocked_seed = f"{origin}/pregrado/excluded"
    catalog_seed = f"{origin}/curso"
    source_sha = "b306c990087fd9d3a6eeb55c600d0d9595fddf16"
    run_id = "991258001"
    run_attempt = "1"
    reference = "fixture-fg2-entrypoint-e2e-v1"

    institution = {
        "id": institution_id,
        "name": "Synthetic FG2 Institution",
        "slug": "synthetic-fg2-institution",
        "website_url": origin,
        "last_harvest_at": None,
    }
    profile = {
        "institution_id": institution_id,
        "site_type": "traditional_ssr",
        "discovery_mode": discovery_mode,
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": (
            [f"{blocked_seed}/", f"{new_url}/", f"{refresh_url}/"]
            if seed_layout == "course_details"
            else [catalog_seed]
        ),
        "exclusion_patterns": ["/pregrado/"],
        "allowed_url_patterns": ["/programs/"],
    }
    preflight = validate_controlled_profile(institution, profile)
    assert preflight["seed_urls"] == (
        [new_url, refresh_url] if seed_layout == "course_details" else [catalog_seed]
    )

    refresh_course = {
        "id": refresh_course_id,
        "institution_id": institution_id,
        "url": refresh_url,
        "name": "Nombre previo",
        "slug": "nombre-previo",
        "category_id": category_id,
        "is_active": True,
        "is_verified": True,
        "last_404_at": None,
    }
    refresh_editorial_state = {
        "course_id": refresh_course_id,
        "editorial_status": "published",
        "manual_overrides": {"name": "Nombre editorial manual"},
        "field_sources": {"name": "manual_override"},
        "field_timestamps": {"name": "2026-11-01T10:00:00+00:00"},
        "manual_updated_at": "2026-11-01T10:00:00+00:00",
    }
    outside_rows = {
        "staging_raw": [{
            "id": outside_staging_id,
            "institution_id": institution_id,
            "url": f"{origin}/programs/outside-scope",
            "status": "pending",
            "raw_name": "Fuera de alcance",
            "raw_html": "<html><body>Fixture externo al lote aprobado.</body></html>",
            "content_hash": "a" * 64,
        }],
        "cleansed_programs": [{
            "id": outside_clean_id,
            "staging_id": outside_staging_id,
            "institution_id": institution_id,
            "url": f"{origin}/programs/outside-scope",
            "clean_name": "Fuera de alcance",
            "clean_description": "Fixture que no pertenece al manifiesto.",
            "status": "pending",
        }],
        "enriched_programs": [{
            "id": outside_enriched_id,
            "cleansed_id": outside_clean_id,
            "institution_id": institution_id,
            "url": f"{origin}/programs/outside-scope",
            "status": "pending",
        }],
    }

    def empty_snapshot(course_rows=None):
        return {
            "staging_rows": [],
            "course_rows": list(course_rows or []),
            "cleansed_rows": [],
            "enriched_rows": [],
        }

    institution_fingerprint = stable_json_sha256({
        "id": institution_id,
        "slug": institution["slug"],
        "website_url": origin,
    })
    approved_discovery_url = catalog_seed if approved_discovery_is_source else new_url
    lot = {
        "schema_version": 1,
        "reference": reference,
        "source_sha": source_sha,
        "limits": FG2_LIMITS,
        "institutions": [{
            "institution_id": institution_id,
            "institution_sha256": institution_fingerprint,
            "profile_sha256": preflight["profile_sha256"],
            "seed_sha256": preflight["seed_sha256"],
            "seed_urls": preflight["seed_urls"],
        }],
        "scope": [
            {
                "institution_id": institution_id,
                "url": url,
                "url_sha256": url_sha256(url),
                "kind": kind,
                "snapshot": empty_snapshot(course_rows),
            }
            for url, kind, course_rows in (
                (approved_discovery_url, "new_discovery", []),
                (refresh_url, "refresh_existing", [{
                    "id": refresh_course_id,
                    "institution_id": institution_id,
                    "url": refresh_url,
                    "is_active": True,
                    "is_verified": True,
                    "last_404_at": None,
                }]),
            )
        ],
    }
    lot_bytes = json.dumps(lot, sort_keys=True, separators=(",", ":")).encode()
    lot_digest = hashlib.sha256(lot_bytes).hexdigest()
    state_path = tmp_path / "synthetic-pro-fixture.json"
    original_state = {
        "tables": {
            "institutions": [institution],
            "institution_site_profiles": [profile],
            "staging_raw": outside_rows["staging_raw"],
            "cleansed_programs": outside_rows["cleansed_programs"],
            "enriched_programs": outside_rows["enriched_programs"],
            "courses": [refresh_course],
            "course_editorial_state": [refresh_editorial_state],
            "categories": [{"id": category_id, "name": "Data"}],
            "market_salaries": [],
        },
        "http_requests": [],
        "rpc_events": [],
        "fail_next_enrichment_rpc": False,
    }
    state_path.write_text(json.dumps(original_state, sort_keys=True), encoding="utf-8")

    from scripts.core.fg2_bounded_run import FG2ApprovedLotManifest, verify_approved_lot_scope
    previous_fixture_path = os.environ.get("FG2_E2E_STATE")
    os.environ["FG2_E2E_STATE"] = str(state_path)
    try:
        approved_fixture = FG2ApprovedLotManifest.from_bytes(
            lot_bytes,
            lot,
            expected_sha256=lot_digest,
            expected_reference=reference,
            expected_source_sha=source_sha,
        )
        verify_approved_lot_scope(FileBackedFG2E2EDatabase(), approved_fixture)
    except Exception as exc:
        raise AssertionError(f"synthetic approved-lot fixture did not reconcile: {exc}") from exc
    finally:
        if previous_fixture_path is None:
            os.environ.pop("FG2_E2E_STATE", None)
        else:
            os.environ["FG2_E2E_STATE"] = previous_fixture_path

    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "sitecustomize.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'tests')!r})\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        "from test_fg2_bounded_workflow import install_fg2_e2e_adapters\n"
        "install_fg2_e2e_adapters()\n",
        encoding="utf-8",
    )

    base_env = os.environ.copy()
    for key in (
        "SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "NEXT_SUPABASE_URL",
        "NEXT_SUPABASE_PUBLISHABLE_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_SUPABASE_SECRET_KEY", "CF_API_TOKEN", "CF_ACCOUNT_ID",
        "OPENAI_API_KEY", "OPENCODE_API_KEY", "GEMINI_API_KEY",
        "FG2_REQUIRE_REAL_PROVIDER",
    ):
        base_env.pop(key, None)
    base_env.update({
        "FG2_E2E_STATE": str(state_path),
        "PYTHONPATH": os.pathsep.join((str(adapter_dir), str(ROOT / "tests"), str(ROOT), str(ROOT / "scripts"))),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "true",
        "PYTHONIOENCODING": "utf-8",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_SHA": source_sha,
        "GITHUB_RUN_ID": run_id,
        "GITHUB_RUN_ATTEMPT": run_attempt,
        "FG2_CONTROLLED_FIRST_RUN": "true",
        "FG2_SCHEDULED_COHORT": "false",
        "FG2_COHORT_SCOPED": "true",
        "FG2_APPROVED_LOT_REFERENCE": reference,
        "FG2_APPROVED_LOT_SHA256": lot_digest,
        "FG2_APPROVED_LOT_MANIFEST_B64": base64.b64encode(lot_bytes).decode("ascii"),
    })

    def run_entrypoint(command: list[str], env: dict[str, str], *, expected: int = 0):
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        assert result.returncode == expected, (
            f"command failed with {result.returncode}, expected {expected}: {command[1]}\n"
            f"stdout tail:\n{result.stdout[-5000:]}\nstderr tail:\n{result.stderr[-5000:]}"
        )
        return result

    harvest_runner = tmp_path / "runner-harvest"
    harvest_runner.mkdir()
    (harvest_runner / "fg2-approved-lot.json").write_bytes(lot_bytes)
    harvest_manifest = harvest_runner / "fg2-cohort-manifest.json"
    harvest_env = {**base_env, "RUNNER_TEMP": str(harvest_runner), "JOB_START_TIME": str(__import__("time").time())}
    run_entrypoint([
        sys.executable,
        str(ROOT / "scripts/core/master_orchestrator.py"),
        "--limit", "10", "--max-urls", "10", "--skip-cleansing",
        "--controlled-first-run",
        "--cohort-manifest", str(harvest_manifest),
        "--approved-lot-manifest", str(harvest_runner / "fg2-approved-lot.json"),
        "--approved-lot-reference", reference,
        "--approved-lot-sha256", lot_digest,
    ], harvest_env, expected=1 if approved_discovery_is_source else 0)
    if approved_discovery_is_source:
        failed_state = json.loads(state_path.read_text(encoding="utf-8"))
        assert failed_state["http_requests"] == []
        assert failed_state["rpc_events"] == []
        assert failed_state["tables"] == original_state["tables"]
        return
    harvest_raw = harvest_manifest.read_bytes()
    cohort_digest = hashlib.sha256(harvest_raw).hexdigest()
    workflow_outputs = (
        "cohort_manifest_b64=" + base64.b64encode(harvest_raw).decode("ascii") + "\n"
        + "cohort_manifest_sha256=" + cohort_digest + "\n"
    )
    workflow_outputs_path = harvest_runner / "GITHUB_OUTPUT"
    workflow_outputs_path.write_text(workflow_outputs, encoding="utf-8")
    outputs = dict(line.split("=", 1) for line in workflow_outputs_path.read_text(encoding="utf-8").splitlines())
    assert hashlib.sha256(base64.b64decode(outputs["cohort_manifest_b64"])).hexdigest() == outputs["cohort_manifest_sha256"]
    cohort = json.loads(harvest_raw)
    assert len(cohort["entries"]) == 2
    assert {entry["kind"] for entry in cohort["entries"]} == {"new_discovery", "refresh_existing"}
    assert [request["status"] for request in json.loads(state_path.read_text())["http_requests"]] == [200, 200]
    assert {request["url"] for request in json.loads(state_path.read_text())["http_requests"]} == {new_url, refresh_url}
    assert all("/pregrado/" not in request["url"] for request in json.loads(state_path.read_text())["http_requests"])

    def restore_runner_manifest(stage: str) -> tuple[Path, dict[str, str]]:
        runner = tmp_path / f"runner-{stage}"
        runner.mkdir()
        restored = runner / "fg2-cohort-manifest.json"
        restored_bytes = base64.b64decode(outputs["cohort_manifest_b64"], validate=True)
        assert hashlib.sha256(restored_bytes).hexdigest() == outputs["cohort_manifest_sha256"]
        restored.write_bytes(restored_bytes)
        stage_env = {**base_env, "RUNNER_TEMP": str(runner), "FG2_COHORT_MANIFEST_SHA256": outputs["cohort_manifest_sha256"]}
        return restored, stage_env

    def run_worker(
        stage: str,
        script: str,
        *,
        expected: int = 0,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        manifest, worker_env = restore_runner_manifest(stage)
        if extra_env:
            worker_env.update(extra_env)
        script_path = ROOT / "scripts/core" / script
        command = [sys.executable, str(script_path)]
        if script == "sync_vector_worker.py":
            # Route the real CLI through the fixture entrypoint adapter so it
            # can allow only this synthetic provider result in the isolated
            # process. Production code has no environment-controlled bypass.
            worker_env["FG2_FIXTURE_PROVIDER_ADAPTER"] = "1"
            command = [
                sys.executable,
                str(ROOT / "tests/fg2_full_pipeline_pg17/run_entrypoint.py"),
                str(script_path),
            ]
        return run_entrypoint([
            *command,
            "--cohort-manifest", str(manifest),
            "--cohort-manifest-sha256", outputs["cohort_manifest_sha256"],
        ], worker_env, expected=expected)

    run_worker("cleansing", "cleansing_worker.py")
    pre_enrichment = json.loads(state_path.read_text(encoding="utf-8"))
    for mode, stage, expected_event in (
        ("all_unhealthy", "provider-health-failure", "stage=provider_health category=all_providers_unhealthy"),
        ("no_result", "provider-empty-fallback", "stage=provider_fallback category=real_provider_result_missing"),
        ("dynamic_degraded", "provider-runtime-degraded", "stage=provider_runtime category=all_providers_degraded"),
    ):
        failed_provider_run = run_worker(
            stage,
            "enrichment_worker.py",
            expected=1,
            extra_env={"FG2_E2E_PROVIDER_MODE": mode},
        )
        diagnostic = failed_provider_run.stdout + failed_provider_run.stderr
        assert "FG2_ENRICHMENT_ABORT" in diagnostic
        assert expected_event in diagnostic
        if mode != "all_unhealthy":
            assert "FG2_ENRICHMENT_SCOPE mode=cohort_manifest institutions=1 manifest_entries=2" in diagnostic
            assert "FG2_ENRICHMENT_BATCH mode=cohort_manifest institutions=1 manifest_entries=2 selected_pending_count=2" in diagnostic
        assert "all institutions" not in diagnostic
        assert "Sin Límite" not in diagnostic
        assert "synthetic provider response sentinel" not in diagnostic
        assert json.loads(state_path.read_text(encoding="utf-8")) == pre_enrichment

    # A no-manifest CLI run without the provider flag must fail closed too.
    # Preserve a pre-existing pending mock row when providers are unavailable.
    no_manifest_state = json.loads(state_path.read_text(encoding="utf-8"))
    no_manifest_state["tables"]["enriched_programs"].append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "fg2-pending-mock-no-manifest")),
        "cleansed_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "fg2-pending-mock-cleansed")),
        "institution_id": institution_id,
        "url": "https://synthetic.example/pending-mock",
        "status": "pending",
        "provider_used": "mock",
        "is_mock_data": True,
    })
    state_path.write_text(json.dumps(no_manifest_state, sort_keys=True), encoding="utf-8")
    before_unbounded_manual = json.loads(state_path.read_text(encoding="utf-8"))
    unbounded_manual_env = {
        **base_env,
        "FG2_COHORT_SCOPED": "false",
        "FG2_E2E_PROVIDER_MODE": "all_unhealthy",
    }
    assert "FG2_REQUIRE_REAL_PROVIDER" not in unbounded_manual_env
    unbounded_manual = run_entrypoint(
        [sys.executable, str(ROOT / "scripts/core/enrichment_worker.py")],
        unbounded_manual_env,
        expected=1,
    )
    assert "FG2_ENRICHMENT_ABORT stage=provider_health" in (
        unbounded_manual.stdout + unbounded_manual.stderr
    )
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_unbounded_manual
    state_path.write_text(json.dumps(pre_enrichment, sort_keys=True), encoding="utf-8")

    failed_partial_state = json.loads(state_path.read_text(encoding="utf-8"))
    failed_partial_state["fail_next_enrichment_rpc"] = True
    state_path.write_text(json.dumps(failed_partial_state, sort_keys=True), encoding="utf-8")

    # The synthetic persistence interruption is a real worker-process failure;
    # the next Actions stage is not invoked until the exact cohort is recovered.
    run_worker("enrichment-failure", "enrichment_worker.py", expected=1)
    after_failure = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(after_failure["tables"]["enriched_programs"]) == 1  # unrelated fixture row only
    assert all(row["status"] == "pending" for row in after_failure["tables"]["cleansed_programs"] if row["staging_id"] != outside_staging_id)
    assert "atomic_enrichment_promote_failed_once" in after_failure["rpc_events"]

    run_worker("enrichment-recovery", "enrichment_worker.py")
    run_worker("sync", "sync_vector_worker.py")

    final = json.loads(state_path.read_text(encoding="utf-8"))
    tables = final["tables"]
    entries = {entry["staging_id"]: entry for entry in cohort["entries"]}
    stage_rows = {row["id"]: row for row in tables["staging_raw"]}
    clean_rows = {row["staging_id"]: row for row in tables["cleansed_programs"]}
    enriched_rows = {row["cleansed_id"]: row for row in tables["enriched_programs"]}
    def course_identity(value: object) -> str:
        return str(value or "").rstrip("/")

    courses_by_url = {course_identity(row["url"]): row for row in tables["courses"]}

    for staging_id, entry in entries.items():
        staging = stage_rows[staging_id]
        cleansed = clean_rows[staging_id]
        enriched = enriched_rows[cleansed["id"]]
        entry_url = next(row["url"] for row in tables["staging_raw"] if row["id"] == staging_id)
        course = courses_by_url[course_identity(entry_url)]
        assert staging["status"] == "processed"
        assert cleansed["status"] == "enriched"
        assert enriched["status"] == "synced"
        assert staging["institution_id"] == cleansed["institution_id"] == enriched["institution_id"] == course["institution_id"] == institution_id
        assert course_identity(staging["url"]) == course_identity(cleansed["url"]) == course_identity(enriched["url"]) == course_identity(course["url"]) == course_identity(entry_url)
        assert enriched["is_mock_data"] is False
        assert course["is_verified"] is True

    assert tables["course_editorial_state"]
    refresh_state = next(row for row in tables["course_editorial_state"] if row["course_id"] == refresh_course_id)
    assert refresh_state["editorial_status"] == "published"
    assert refresh_state["manual_overrides"] == {"name": "Nombre editorial manual"}
    new_course = courses_by_url[course_identity(new_url)]
    new_state = next(row for row in tables["course_editorial_state"] if row["course_id"] == new_course["id"])
    assert new_state["editorial_status"] == "pending_review"
    assert new_state["manual_overrides"] == {}

    for table, row_id in (
        ("staging_raw", outside_staging_id),
        ("cleansed_programs", outside_clean_id),
        ("enriched_programs", outside_enriched_id),
    ):
        row = next(row for row in tables[table] if row["id"] == row_id)
        assert row["status"] == "pending", f"out-of-scope {table} row was consumed"
    assert [request["status"] for request in final["http_requests"]] == [200, 200]
    assert [event for event in final["rpc_events"] if event in {
        "atomic_cleansing_promote", "atomic_enrichment_promote", "h2_update_course_quality"
    }].count("atomic_cleansing_promote") == 1
    assert sum(event == "atomic_enrichment_promote" for event in final["rpc_events"]) == 2

    # Model the ten post-#269 mock rows: staging remains processed, cleansing
    # remains enriched, and each pending enriched row is explicitly synthetic.
    # Production Sync must fail without mutating any of those rows or courses.
    recovery_state = json.loads(state_path.read_text(encoding="utf-8"))
    recovery_tables = recovery_state["tables"]
    recovery_tables["enriched_programs"] = [
        row for row in recovery_tables["enriched_programs"] if row["id"] != outside_enriched_id
    ]
    recovery_tables["cleansed_programs"] = [
        row for row in recovery_tables["cleansed_programs"] if row["id"] != outside_clean_id
    ]
    recovery_tables["staging_raw"] = [
        row for row in recovery_tables["staging_raw"] if row["id"] != outside_staging_id
    ]
    for index in range(10):
        staging_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"fg2-recovery:{index}:staging"))
        cleansed_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"fg2-recovery:{index}:cleansed"))
        enriched_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"fg2-recovery:{index}:enriched"))
        recovery_url = f"https://synthetic.example/recovery/{index}"
        recovery_tables["staging_raw"].append({
            "id": staging_id,
            "institution_id": institution_id,
            "url": recovery_url,
            "content_hash": hashlib.sha256(f"body-{index}".encode()).hexdigest(),
            "status": "processed",
        })
        recovery_tables["cleansed_programs"].append({
            "id": cleansed_id,
            "staging_id": staging_id,
            "institution_id": institution_id,
            "url": recovery_url,
            "status": "enriched",
        })
        recovery_tables["enriched_programs"].append({
            "id": enriched_id,
            "cleansed_id": cleansed_id,
            "institution_id": institution_id,
            "url": recovery_url,
            "status": "pending",
            "provider_used": "mock",
            "is_mock_data": True,
        })
    state_path.write_text(json.dumps(recovery_state, sort_keys=True), encoding="utf-8")
    before_mock_sync = json.loads(state_path.read_text(encoding="utf-8"))
    sync_env = {
        **base_env,
        "FG2_COHORT_SCOPED": "false",
    }
    assert "FG2_REQUIRE_REAL_PROVIDER" not in sync_env
    failed_mock_sync = run_entrypoint(
        [sys.executable, str(ROOT / "scripts/core/sync_vector_worker.py")],
        sync_env,
        expected=1,
    )
    assert "Found 10 pending enriched records." in failed_mock_sync.stdout
    assert "Failed: 10" in failed_mock_sync.stdout
    assert "category=mock_enrichment_rejected" in (
        failed_mock_sync.stdout + failed_mock_sync.stderr
    )
    assert json.loads(state_path.read_text(encoding="utf-8")) == before_mock_sync


def test_fg2_ci_fixture_records_the_pull_request_source_sha() -> None:
    """The isolated E2E records the candidate commit rather than the PR merge ref."""
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text()
    fixture_runner = (ROOT / "tests/fg2_full_pipeline_pg17/run.sh").read_text()

    assert "FG2_FIXTURE_SOURCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert 'source_sha="${FG2_FIXTURE_SOURCE_SHA:-467406edcb1ea70ada36036c73d024110ed4a5a5}"' in fixture_runner
    assert "invalid_source_sha" in fixture_runner


def test_enrichment_provider_diagnostics_redact_exception_and_response_bodies(monkeypatch) -> None:
    from types import SimpleNamespace
    from scripts.core import enrichment_worker

    events: list[str] = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    class FakeProviderError(Exception):
        def __init__(self):
            self.response = SimpleNamespace(status_code=400)
            super().__init__("synthetic provider response sentinel")

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-fixture-token")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-fixture-account")
    monkeypatch.setattr(
        enrichment_worker.requests,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FakeProviderError()),
    )
    assert worker._call_cloudflare("synthetic prompt sentinel") is None

    diagnostic_text = "\n".join(events)
    assert "synthetic provider response sentinel" not in diagnostic_text
    assert "synthetic prompt sentinel" not in diagnostic_text
    assert "status_code=400" in diagnostic_text
    assert "provider=Cloudflare category=request_rejected" in diagnostic_text


def test_enrichment_runtime_registers_openai_primary_and_cloudflare_fallback(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    registered = []

    class FixtureDB:
        @staticmethod
        def select_pipeline_raise(_table):
            return []

    class FixtureProvider:
        def __init__(self, name, call_fn, health_fn=None):
            self.name = name
            self.call_fn = call_fn
            self.health_fn = health_fn
            registered.append(self)

    class FixtureOrchestrator:
        def __init__(self, providers, logger):
            self.providers = list(providers)
            self.logger = logger

    monkeypatch.setenv("OPENCODE_API_KEY", "synthetic-legacy-key")
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key", raising=False)
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-cloudflare-token")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-cloudflare-account")
    monkeypatch.setattr(enrichment_worker, "get_db_client", FixtureDB)
    monkeypatch.setattr(enrichment_worker, "LLMProvider", FixtureProvider)
    monkeypatch.setattr(enrichment_worker, "ProviderOrchestrator", FixtureOrchestrator)

    worker = enrichment_worker.EnrichmentWorker()

    assert [provider.name for provider in registered] == ["OpenAI", "Cloudflare"]
    assert [provider.name for provider in worker.orchestrator.providers] == ["OpenAI", "Cloudflare"]
    assert all(callable(provider.health_fn) for provider in registered)
    assert registered[0].health_fn() is True
    assert not hasattr(enrichment_worker, "OPENCODE_API_KEY")


def test_openai_responses_adapter_uses_bounded_structured_output_without_redirects(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    calls = []

    class FakeResponse:
        status_code = 200
        raw = SimpleNamespace(isclosed=True)

        def __init__(self):
            self.body = json.dumps({
                "status": "completed",
                "output": [{
                    "type": "message",
                    "content": [{
                        "type": "output_text",
                        "text": '{"official_name":"Synthetic course"}',
                    }],
                }],
            }).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-secret")
    monkeypatch.setattr(enrichment_worker.requests, "post", fake_post)

    assert worker._call_openai("synthetic extraction prompt") == '{"official_name":"Synthetic course"}'
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.openai.com/v1/responses"
    authorization = kwargs["headers"]["Authorization"].partition(" ")
    assert authorization[0] == "Bear" + "er"
    assert authorization[2] == "synthetic-openai-secret"
    assert kwargs["json"]["model"] == "gpt-6-luna"
    assert kwargs["json"]["instructions"]
    assert kwargs["json"]["input"] == "synthetic extraction prompt"
    assert kwargs["json"]["max_output_tokens"] == 2048
    assert kwargs["json"]["reasoning"] == {"effort": "low"}
    assert kwargs["json"]["store"] is False
    fmt = kwargs["json"]["text"]["format"]
    assert fmt["type"] == "json_schema" and fmt["strict"] is True
    schema = fmt["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert len(schema["required"]) == 18
    assert kwargs["timeout"] == (
        enrichment_worker.PROVIDER_CONNECT_TIMEOUT_SECONDS,
        enrichment_worker.PROVIDER_READ_TIMEOUT_SECONDS,
    )
    assert kwargs["allow_redirects"] is False
    assert kwargs["stream"] is True


def test_openai_real_http_headers_after_legacy_five_second_timeout_succeed(monkeypatch) -> None:
    """The same delayed-header request fails with the old timeout and passes with the new one."""
    from scripts.core import enrichment_worker

    body = _openai_wire_payload()
    expected_text = json.dumps(_valid_provider_pillars(), ensure_ascii=False)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            time.sleep(5.2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    calls = []
    events = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    def local_post(url, **kwargs):
        assert url == "https://api.openai.com/v1/responses"
        calls.append(url)
        return real_post(f"http://127.0.0.1:{server.server_port}/responses", **kwargs)

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)
    try:
        # Reproduce the #272 setting against the same local endpoint and prompt.
        monkeypatch.setattr(enrichment_worker, "PROVIDER_READ_TIMEOUT_SECONDS", 5)
        legacy_started = time.monotonic()
        legacy_result = worker._call_openai("synthetic delayed-response prompt")
        legacy_elapsed = time.monotonic() - legacy_started

        monkeypatch.setattr(enrichment_worker, "PROVIDER_READ_TIMEOUT_SECONDS", 30)
        current_started = time.monotonic()
        current_result = worker._call_openai("synthetic delayed-response prompt")
        current_elapsed = time.monotonic() - current_started
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert legacy_result is None
    assert 4.5 <= legacy_elapsed < 5.2
    assert current_result == expected_text
    assert current_elapsed > 5
    assert current_elapsed < enrichment_worker.PROVIDER_RESPONSE_BODY_DEADLINE_SECONDS
    assert len(calls) == 2
    assert sum("category=timeout" in event for event in events) == 1
    diagnostics = "\n".join(events)
    assert "synthetic delayed-response prompt" not in diagnostics
    assert "synthetic-openai-key" not in diagnostics
    assert "Synthetic course" not in diagnostics


def test_openai_real_http_slow_trickle_obeys_body_deadline_and_closes_response(monkeypatch) -> None:
    """A continuously trickling body cannot extend the bounded response-body deadline."""
    from scripts.core import enrichment_worker

    body = _openai_wire_payload()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            try:
                for byte in body:
                    self.wfile.write(b"1\r\n" + bytes([byte]) + b"\r\n")
                    self.wfile.flush()
                    time.sleep(0.025)
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    calls = []
    responses = []
    events = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    def local_post(url, **kwargs):
        assert url == "https://api.openai.com/v1/responses"
        calls.append(url)
        response = real_post(f"http://127.0.0.1:{server.server_port}/responses", **kwargs)
        responses.append(response)
        return response

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "PROVIDER_RESPONSE_BODY_DEADLINE_SECONDS", 0.6)
    monkeypatch.setattr(enrichment_worker, "PROVIDER_READ_TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)
    started = time.monotonic()
    try:
        result = worker._call_openai("synthetic slow-trickle prompt")
        elapsed = time.monotonic() - started
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert result is None
    assert elapsed < 1.4
    assert len(calls) == 1
    assert len(responses) == 1
    assert responses[0].raw.closed is True
    assert any("category=response_timeout" in event for event in events), events
    assert "synthetic slow-trickle prompt" not in "\n".join(events)


def test_openai_realistic_response_uses_one_watchdog_and_joins_before_close(monkeypatch) -> None:
    """A multi-chunk 18-property response uses one joined watchdog for the whole body."""
    from scripts.core import enrichment_worker

    pillars = _valid_provider_pillars()
    for field, value in tuple(pillars.items()):
        if isinstance(value, str):
            pillars[field] = f"Synthetic {field}: " + ("course detail " * 130)
    pillars["requirements"] = [
        f"Synthetic requirement {index}: " + ("required item " * 24)
        for index in range(3)
    ]
    pillars["curriculum_summary"] = {
        "pilares": [f"Synthetic module {index}: " + ("curriculum detail " * 18) for index in range(4)]
    }
    body = _openai_wire_payload(pillars)
    assert len(pillars) == 18
    assert len(body) > enrichment_worker.PROVIDER_RESPONSE_CHUNK_BYTES

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    real_timer = enrichment_worker.threading.Timer
    timers = []
    responses = []

    class CountingTimer(real_timer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cancel_called = False
            self.join_called = False
            timers.append(self)

        def cancel(self):
            self.cancel_called = True
            return super().cancel()

        def join(self, *args, **kwargs):
            self.join_called = True
            return super().join(*args, **kwargs)

    def local_post(url, **kwargs):
        assert url == "https://api.openai.com/v1/responses"
        response = real_post(f"http://127.0.0.1:{server.server_port}/responses", **kwargs)
        original_close = response.close

        def checked_close():
            assert len(timers) == 1
            assert timers[0].cancel_called
            assert timers[0].join_called
            original_close()

        response.close = checked_close
        responses.append(response)
        return response

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "PROVIDER_RESPONSE_BODY_DEADLINE_SECONDS", 5)
    monkeypatch.setattr(enrichment_worker, "PROVIDER_READ_TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(enrichment_worker.threading, "Timer", CountingTimer)
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)
    try:
        result = worker._call_openai("synthetic realistic response prompt")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert result == json.dumps(pillars, ensure_ascii=False)
    assert len(timers) == 1
    assert len(responses) == 1
    assert responses[0].raw.closed is True


@pytest.mark.parametrize("wire_case", ["partial_chunk_size", "partial_gzip_body"])
def test_openai_http_framing_trickle_cannot_outlive_absolute_body_deadline(
    monkeypatch, wire_case
) -> None:
    """Socket activity inside urllib3 framing/decompression cannot reset the total deadline."""
    import gzip

    from scripts.core import enrichment_worker

    compressed = gzip.compress(_openai_wire_payload())
    sent_bytes = []
    events = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Transfer-Encoding", "chunked")
            if wire_case == "partial_gzip_body":
                self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            try:
                if wire_case == "partial_gzip_body":
                    self.wfile.write(f"{len(compressed):X}\r\n".encode("ascii"))
                    self.wfile.flush()
                    payload = compressed
                else:
                    # A valid-looking hexadecimal chunk-size prefix without its
                    # CRLF leaves urllib3 waiting inside the framing parser.
                    payload = b"A" * 160
                for byte in payload:
                    self.wfile.write(bytes((byte,)))
                    self.wfile.flush()
                    sent_bytes.append(byte)
                    time.sleep(0.1)
                self.wfile.write(b"\r\n0\r\n\r\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    responses = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    def local_post(url, **kwargs):
        assert url == "https://api.openai.com/v1/responses"
        response = real_post(
            f"http://127.0.0.1:{server.server_port}/responses", **kwargs
        )
        responses.append(response)
        return response

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "PROVIDER_RESPONSE_BODY_DEADLINE_SECONDS", 0.55)
    monkeypatch.setattr(enrichment_worker, "PROVIDER_READ_TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)
    started = time.monotonic()
    try:
        result = worker._call_openai("synthetic framing deadline prompt")
        elapsed = time.monotonic() - started
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert result is None
    assert elapsed < 1.5
    assert sent_bytes, wire_case
    assert len(responses) == 1
    assert responses[0].raw.closed is True
    assert any("category=response_timeout" in event for event in events), events
    assert "synthetic framing deadline prompt" not in "\n".join(events)


def test_openai_real_http_decodes_chunked_gzip_without_content_length(monkeypatch) -> None:
    """A real Requests response with chunked gzip framing stays under the decoded-byte cap."""
    import gzip

    from scripts.core import enrichment_worker

    body = gzip.compress(_openai_wire_payload())

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            try:
                for offset in range(0, len(body), 64):
                    chunk = body[offset:offset + 64]
                    self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(
        enrichment_worker.requests,
        "post",
        lambda url, **kwargs: real_post(
            f"http://127.0.0.1:{server.server_port}/responses", **kwargs
        ),
    )
    try:
        result = worker._call_openai("synthetic gzip response prompt")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert result == json.dumps(_valid_provider_pillars(), ensure_ascii=False)


def test_openai_real_http_rejects_compressed_body_over_decoded_byte_cap(monkeypatch) -> None:
    """The response-size cap applies after Requests decompresses gzip content."""
    import gzip

    from scripts.core import enrichment_worker

    body = gzip.compress(b"x" * (enrichment_worker.PROVIDER_MAX_RESPONSE_BYTES + 1))

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    events = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(
        enrichment_worker.requests,
        "post",
        lambda url, **kwargs: real_post(
            f"http://127.0.0.1:{server.server_port}/responses", **kwargs
        ),
    )
    try:
        result = worker._call_openai("synthetic compressed oversized prompt")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert result is None
    assert any("category=response_limit_exceeded" in event for event in events)
    assert "synthetic compressed oversized prompt" not in "\n".join(events)


def test_openai_complete_payload_runs_through_enrichment_record_persistence(tmp_path, monkeypatch) -> None:
    """A complete real HTTP response passes schema validation and the worker persistence path."""
    from scripts.core import enrichment_worker

    institution_id = "20000000-0000-0000-0000-000000000031"
    staging_id = "40000000-0000-0000-0000-000000000031"
    cleansed_id = "50000000-0000-0000-0000-000000000031"
    category_id = "10000000-0000-0000-0000-000000000031"
    course_url = "https://fixture.invalid/courses/synthetic-openai"
    staging = {
        "id": staging_id,
        "institution_id": institution_id,
        "url": course_url,
        "content_hash": hashlib.sha256(b"synthetic HTML").hexdigest(),
        "status": "processed",
        "metadata": {},
        "raw_html": "",
    }
    cleansed = {
        "id": cleansed_id,
        "staging_id": staging_id,
        "institution_id": institution_id,
        "url": course_url,
        "clean_name": "Synthetic course",
        "clean_description": "Synthetic educational description",
        "status": "pending",
        "metadata": {},
    }
    state_path = tmp_path / "openai-enrichment-state.json"
    state_path.write_text(json.dumps({
        "tables": {
            "staging_raw": [staging],
            "cleansed_programs": [cleansed],
            "enriched_programs": [],
            "categories": [{"id": category_id, "name": "Data"}],
            "course_editorial_state": [],
        },
        "rpc_events": [],
        "fail_next_enrichment_rpc": False,
    }, sort_keys=True), encoding="utf-8")
    monkeypatch.setenv("FG2_E2E_STATE", str(state_path))
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-cloudflare-key")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-cloudflare-account")

    body = _openai_wire_payload()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(request_length))
            assert request["model"] == "gpt-6-luna"
            assert request["store"] is False
            assert len(request["text"]["format"]["schema"]["properties"]) == 18
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    provider_calls = []

    def local_post(url, **kwargs):
        assert url == "https://api.openai.com/v1/responses"
        provider_calls.append(url)
        return real_post(f"http://127.0.0.1:{server.server_port}/responses", **kwargs)

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FileBackedFG2E2EDatabase()
    worker.profiles = [{"institution_id": institution_id, "pipeline_enabled": True}]
    worker.ready_inst_ids = {institution_id}
    worker._mock_only = False
    worker.require_real_provider = True
    worker.orchestrator = enrichment_worker.ProviderOrchestrator(
        providers=[
            enrichment_worker.LLMProvider("OpenAI", worker._call_openai, lambda: True),
            enrichment_worker.LLMProvider("Cloudflare", worker._call_cloudflare, lambda: True),
        ],
        logger=enrichment_worker.logger,
    )
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)

    try:
        assert worker.orchestrator.run_health_checks() == ["OpenAI", "Cloudflare"]
        assert enrichment_worker.process_enrichment_records(worker, [cleansed], set()) == 1
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    persisted_state = json.loads(state_path.read_text(encoding="utf-8"))
    persisted_rows = persisted_state["tables"]["enriched_programs"]
    assert len(provider_calls) == 1
    assert len(persisted_rows) == 1
    assert persisted_rows[0]["provider_used"] == "OpenAI"
    assert persisted_rows[0]["is_mock_data"] is False
    assert persisted_rows[0]["official_name"] == _valid_provider_pillars()["official_name"]
    assert persisted_rows[0]["duration_months"] == 6
    assert persisted_rows[0]["total_cost_est"] == 1250.0
    assert persisted_state["tables"]["cleansed_programs"][0]["status"] == "enriched"
    assert persisted_state["rpc_events"] == ["atomic_enrichment_promote"]


def test_total_provider_transport_failure_does_not_persist_and_is_sanitized(tmp_path, monkeypatch) -> None:
    """A real HTTP disconnect plus failed fallback makes one attempt each and writes no row."""
    import socket

    from scripts.core import enrichment_worker

    institution_id = "20000000-0000-0000-0000-000000000032"
    staging_id = "40000000-0000-0000-0000-000000000032"
    cleansed_id = "50000000-0000-0000-0000-000000000032"
    course_url = "https://fixture.invalid/courses/provider-failure"
    state = {
        "tables": {
            "staging_raw": [{
                "id": staging_id,
                "institution_id": institution_id,
                "url": course_url,
                "content_hash": hashlib.sha256(b"synthetic HTML").hexdigest(),
                "status": "processed",
                "metadata": {},
                "raw_html": "",
            }],
            "cleansed_programs": [{
                "id": cleansed_id,
                "staging_id": staging_id,
                "institution_id": institution_id,
                "url": course_url,
                "clean_name": "Synthetic course",
                "clean_description": "Synthetic failure description",
                "status": "pending",
                "metadata": {},
            }],
            "enriched_programs": [],
            "categories": [],
        },
        "rpc_events": [],
        "fail_next_enrichment_rpc": False,
    }
    state_path = tmp_path / "provider-failure-state.json"
    initial_bytes = json.dumps(state, sort_keys=True).encode("utf-8")
    state_path.write_bytes(initial_bytes)
    monkeypatch.setenv("FG2_E2E_STATE", str(state_path))
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-cloudflare-key")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-cloudflare-account")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(request_length)
            if self.path == "/openai":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "80")
                self.end_headers()
                self.wfile.write(b'{"status":"completed","output":')
                self.wfile.flush()
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            failure_body = b"synthetic provider response body sentinel"
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(failure_body)))
            self.end_headers()
            self.wfile.write(failure_body)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    real_post = enrichment_worker.requests.post
    attempts = []
    events = []

    class CaptureLogger:
        def info(self, message, *args):
            events.append(message % args if args else message)

        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    def local_post(url, **kwargs):
        if url == "https://api.openai.com/v1/responses":
            attempts.append("OpenAI")
            path = "openai"
        elif "/ai/run/" in url:
            attempts.append("Cloudflare")
            path = "cloudflare"
        else:
            raise AssertionError("unexpected external POST in provider fixture")
        return real_post(f"http://127.0.0.1:{server.server_port}/{path}", **kwargs)

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FileBackedFG2E2EDatabase()
    worker.profiles = [{"institution_id": institution_id, "pipeline_enabled": True}]
    worker.ready_inst_ids = {institution_id}
    worker._mock_only = False
    worker.require_real_provider = True
    worker.orchestrator = enrichment_worker.ProviderOrchestrator(
        providers=[
            enrichment_worker.LLMProvider("OpenAI", worker._call_openai, lambda: True),
            enrichment_worker.LLMProvider("Cloudflare", worker._call_cloudflare, lambda: True),
        ],
        logger=CaptureLogger(),
    )
    monkeypatch.setattr(enrichment_worker, "logger", worker.orchestrator.logger)
    monkeypatch.setattr(enrichment_worker.requests, "post", local_post)
    try:
        assert worker.orchestrator.run_health_checks() == ["OpenAI", "Cloudflare"]
        with pytest.raises(enrichment_worker.ControlledEnrichmentUnavailable):
            enrichment_worker.process_enrichment_records(
                worker,
                state["tables"]["cleansed_programs"],
                set(),
            )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)

    assert attempts == ["OpenAI", "Cloudflare"]
    assert state_path.read_bytes() == initial_bytes
    diagnostics = "\n".join(events)
    assert "provider=OpenAI category=request_error" in diagnostics
    assert "provider=Cloudflare category=transient_http status_code=503" in diagnostics
    assert "stage=provider_fallback category=real_provider_result_missing" in diagnostics
    assert "synthetic provider response body sentinel" not in diagnostics
    assert "synthetic-openai-key" not in diagnostics
    assert "synthetic-cloudflare-key" not in diagnostics
    assert "synthetic failure description" not in diagnostics


def test_openai_adapter_rejects_missing_key_oversize_input_and_bad_responses(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    events = []
    calls = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    class FakeResponse:
        def __init__(self, status_code=200, payload=None):
            self.status_code = status_code
            self.raw = SimpleNamespace(isclosed=True)
            self.payload = payload
            self.body = json.dumps(payload).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "")
    monkeypatch.setattr(enrichment_worker.requests, "post", lambda *a, **k: calls.append((a, k)))
    assert worker._call_openai("prompt") is None
    assert calls == []
    assert "category=missing_configuration" in events[-1]

    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-secret")
    assert worker._call_openai("x" * (enrichment_worker.OPENAI_MAX_INPUT_BYTES + 1)) is None
    assert calls == []
    assert "category=input_limit_exceeded" in events[-1]

    sentinel = "synthetic-body-and-prompt-sentinel"
    for status, category in (
        (401, "auth_or_permission"),
        (302, "http_error"),
        (429, "rate_limited"),
        (503, "transient_http"),
    ):
        def fake_status(*args, _status=status, **kwargs):
            calls.append((args, kwargs))
            assert kwargs["allow_redirects"] is False
            return FakeResponse(_status, {"error": sentinel})

        monkeypatch.setattr(enrichment_worker.requests, "post", fake_status)
        assert worker._call_openai(f"prompt {sentinel}") is None
        assert category in events[-1]
    assert len(calls) == 4
    diagnostic = "\n".join(events)
    assert sentinel not in diagnostic
    assert "synthetic-openai-secret" not in diagnostic


def test_openai_adapter_parses_responses_and_classifies_timeout_refusal_and_incomplete(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    events = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    class FakeResponse:
        status_code = 200
        raw = SimpleNamespace(isclosed=True)

        def __init__(self, payload):
            self.body = json.dumps(payload).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-secret")

    for payload, expected_category in (
        ({"status": "incomplete", "output": []}, "incomplete_response"),
        ({"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "sentinel"}]}]}, "refusal"),
        ({"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": ""}]}]}, "invalid_provider_response"),
    ):
        monkeypatch.setattr(enrichment_worker.requests, "post", lambda *a, _payload=payload, **k: FakeResponse(_payload))
        assert worker._call_openai("synthetic prompt") is None
        assert expected_category in events[-1]

    class InvalidJsonResponse:
        status_code = 200
        headers = {}
        raw = SimpleNamespace(isclosed=True)

        @staticmethod
        def iter_content(chunk_size=None):
            yield b"not-json-synthetic-response-body"

        @staticmethod
        def close():
            return None

    monkeypatch.setattr(enrichment_worker.requests, "post", lambda *a, **k: InvalidJsonResponse())
    assert worker._call_openai("synthetic prompt") is None
    assert "category=invalid_response_json" in events[-1]

    def timeout(*_args, **_kwargs):
        raise enrichment_worker.requests.Timeout("synthetic exception body")

    monkeypatch.setattr(enrichment_worker.requests, "post", timeout)
    assert worker._call_openai("synthetic prompt") is None
    assert "category=timeout" in events[-1]
    diagnostics = "\n".join(events)
    assert "synthetic exception body" not in diagnostics
    assert "synthetic prompt" not in diagnostics
    assert "synthetic-openai-secret" not in diagnostics


def test_openai_primary_falls_back_to_cloudflare_and_health_checks_do_not_call_api(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    db_calls = []

    class FixtureDB:
        @staticmethod
        def select_pipeline_raise(_table):
            return []

    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-secret")
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-cloudflare-secret")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-account")
    monkeypatch.setattr(enrichment_worker, "get_db_client", FixtureDB)

    worker = enrichment_worker.EnrichmentWorker()
    worker.profiles = []
    worker._mock_only = False
    worker.require_real_provider = True
    valid_payload = {
        "official_name": "Synthetic course",
        "duration_text": None,
        "duration_months": None,
        "total_cost_est": None,
        "requirements": [],
        "graduate_profile": None,
        "target_audience": None,
        "objectives": None,
        "benefits": None,
        "certification": None,
        "curriculum_summary": {"pilares": []},
        "modality": None,
        "primary_campus": None,
        "degree_type": None,
        "start_date": None,
        "categories": [],
        "difficulty_level": None,
        "ai_summary": None,
    }
    worker._call_openai = lambda _prompt: json.dumps(dict(valid_payload, official_name="OpenAI course"))
    worker._call_cloudflare = lambda _prompt: json.dumps(dict(valid_payload, official_name="Fallback course"))
    worker.orchestrator.providers[0].call_fn = worker._call_openai
    worker.orchestrator.providers[1].call_fn = worker._call_cloudflare
    monkeypatch.setattr(enrichment_worker.requests, "post", lambda *a, **k: db_calls.append((a, k)))

    assert worker.orchestrator.run_health_checks() == ["OpenAI", "Cloudflare"]
    assert db_calls == []
    result, provider = worker._call_llm_for_pillars("Synthetic", "Synthetic description")
    assert result["official_name"] == "OpenAI course"
    assert provider == "OpenAI"

    worker._call_openai = lambda _prompt: None
    worker.orchestrator.providers[0].call_fn = worker._call_openai
    result, provider = worker._call_llm_for_pillars("Synthetic", "Synthetic description")
    assert result["official_name"] == "Fallback course"
    assert provider == "Cloudflare"


def test_provider_fallback_rejects_oversize_prompt_and_invalid_schema(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    events = []
    requests_seen = []

    class CaptureLogger:
        def info(self, message, *args):
            events.append(message % args if args else message)

        def warning(self, message, *args):
            events.append(message % args if args else message)

    class FakeResponse:
        status_code = 200
        raw = SimpleNamespace(isclosed=True)

        def __init__(self, payload):
            self.body = json.dumps(payload).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    valid = {
        "official_name": "Synthetic course", "duration_text": None,
        "duration_months": None, "total_cost_est": None, "requirements": [],
        "graduate_profile": None, "target_audience": None, "objectives": None,
        "benefits": None, "certification": None,
        "curriculum_summary": {"pilares": []}, "modality": None,
        "primary_campus": None, "degree_type": None, "start_date": None,
        "categories": [], "difficulty_level": None, "ai_summary": None,
    }
    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-cloudflare-key")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-account")
    monkeypatch.setattr(
        enrichment_worker.requests, "post",
        lambda *args, **kwargs: requests_seen.append((args, kwargs)),
    )

    providers = [
        enrichment_worker.LLMProvider("OpenAI", worker._call_openai, lambda: True),
        enrichment_worker.LLMProvider("Cloudflare", worker._call_cloudflare, lambda: True),
    ]
    worker.orchestrator = enrichment_worker.ProviderOrchestrator(
        providers, enrichment_worker.logger
    )
    worker.orchestrator.run_health_checks()

    parsed, provider = worker.orchestrator.call_with_fallback(
        "x" * (enrichment_worker.OPENAI_MAX_INPUT_BYTES + 1),
        worker._clean_json_response,
        validate_fn=enrichment_worker._matches_openai_pillars_schema,
    )
    assert parsed is None and provider is None
    assert requests_seen == []
    assert sum("category=input_limit_exceeded" in event for event in events) == 2

    for invalid in (
        {}, [],
        dict(valid, duration_months="six"),
        dict(valid, curriculum_summary={"pilares": [], "unexpected": "x"}),
        dict(valid, unexpected="x"),
    ):
        assert not enrichment_worker._matches_openai_pillars_schema(invalid)
    assert enrichment_worker._matches_openai_pillars_schema(valid)

    # A syntactically valid but schema-invalid primary result is treated as a
    # provider failure, so the valid Cloudflare fallback may be considered.
    providers[0].call_fn = lambda _prompt: "{}"
    providers[1].call_fn = lambda _prompt: json.dumps(valid)
    worker.orchestrator.run_health_checks()
    parsed, provider = worker.orchestrator.call_with_fallback(
        "small prompt", worker._clean_json_response,
        validate_fn=enrichment_worker._matches_openai_pillars_schema,
    )
    assert parsed == valid and provider == "Cloudflare"
    assert any("provider=OpenAI category=invalid_response_schema" in event for event in events)


def test_provider_response_size_limit_bounds_bytes_and_total_read_time(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    events = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

    class StreamResponse:
        headers = {}
        raw = SimpleNamespace(isclosed=True)

        def __init__(self, chunks):
            self.chunks = chunks
            self.closed = False

        def iter_content(self, chunk_size=None):
            yield from self.chunks

        def close(self):
            self.closed = True

    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    oversized = StreamResponse([b"x" * enrichment_worker.PROVIDER_MAX_RESPONSE_BYTES,
                                b"x"])
    assert enrichment_worker._read_bounded_provider_json(
        oversized, "Cloudflare", enrichment_worker.time.monotonic() + 5
    ) is None
    assert oversized.closed
    assert "category=response_limit_exceeded" in events[-1]

    slow = StreamResponse([b"{}"])
    monkeypatch.setattr(enrichment_worker.time, "monotonic", lambda: 10.0)
    assert enrichment_worker._read_bounded_provider_json(slow, "OpenAI", 10.0) is None
    assert slow.closed
    assert "category=response_timeout" in events[-1]


def test_provider_transport_without_socket_requires_confirmed_closed_response() -> None:
    from scripts.core import enrichment_worker

    class RawResponse:
        def __init__(self, closed):
            self.closed = closed

        def isclosed(self):
            return self.closed

    assert not enrichment_worker._set_response_socket_read_timeout(
        SimpleNamespace(raw=RawResponse(False)), 1.0
    )
    assert enrichment_worker._set_response_socket_read_timeout(
        SimpleNamespace(raw=RawResponse(True)), 1.0
    )

    class UnverifiableRawResponse:
        def isclosed(self):
            raise RuntimeError("synthetic transport sentinel")

    assert not enrichment_worker._set_response_socket_read_timeout(
        SimpleNamespace(raw=UnverifiableRawResponse()), 1.0
    )
    assert not enrichment_worker._set_response_socket_read_timeout(
        SimpleNamespace(raw=SimpleNamespace(isclosed=object())), 1.0
    )


def test_cloudflare_uses_current_direct_model_and_sanitizes_provider_failures(monkeypatch) -> None:
    from types import SimpleNamespace
    from scripts.core import enrichment_worker

    events: list[str] = []
    requests_seen: list[tuple[str, dict]] = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    class FakeResponse:
        status_code = 200
        raw = SimpleNamespace(isclosed=True)

        def __init__(self):
            self.body = json.dumps({
                "result": {"response": '{"official_name":"Synthetic"}'}
            }).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    def fake_post(url, **kwargs):
        requests_seen.append((url, kwargs))
        return FakeResponse()

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-secret-sentinel")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-account-sentinel")
    monkeypatch.setattr(enrichment_worker.requests, "post", fake_post)

    assert worker._call_cloudflare("synthetic prompt sentinel") == '{"official_name":"Synthetic"}'
    assert len(requests_seen) == 1
    url, kwargs = requests_seen[0]
    assert url.endswith("/ai/run/@cf/google/gemma-4-26b-a4b-it")
    assert kwargs["json"]["messages"][1]["content"] == "synthetic prompt sentinel"
    assert kwargs["headers"]["Authorization"].partition(" ")[2] == "synthetic-secret-sentinel"
    assert kwargs["timeout"] == (
        enrichment_worker.PROVIDER_CONNECT_TIMEOUT_SECONDS,
        enrichment_worker.PROVIDER_READ_TIMEOUT_SECONDS,
    )
    assert kwargs["allow_redirects"] is False
    assert kwargs["stream"] is True
    assert kwargs["json"]["max_completion_tokens"] == 2_048
    assert "synthetic-secret-sentinel" not in "\n".join(events)
    assert "synthetic-account-sentinel" not in "\n".join(events)
    assert "synthetic prompt sentinel" not in "\n".join(events)


def test_cloudflare_missing_bindings_and_invalid_responses_fail_closed(monkeypatch) -> None:
    from types import SimpleNamespace
    from scripts.core import enrichment_worker

    events: list[str] = []
    requests_seen: list[tuple[tuple, dict]] = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "requests", SimpleNamespace(post=lambda *args, **kwargs: requests_seen.append((args, kwargs))))
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "  ")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-account-sentinel")
    assert worker._call_cloudflare("synthetic prompt sentinel") is None
    assert not requests_seen
    assert "category=missing_configuration" in events[-1]
    assert "missing_bindings=CF_API_TOKEN" in events[-1]

    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-secret-sentinel")

    class InvalidJsonResponse:
        status_code = 200
        headers = {}
        raw = SimpleNamespace(isclosed=True)

        @staticmethod
        def iter_content(chunk_size=None):
            yield b"not-json-synthetic-response-body-sentinel"

        @staticmethod
        def close():
            return None

    monkeypatch.setattr(enrichment_worker.requests, "post", lambda *_args, **_kwargs: InvalidJsonResponse())
    assert worker._call_cloudflare("synthetic prompt sentinel") is None
    assert "category=invalid_response_json" in events[-1]

    class InvalidShapeResponse:
        status_code = 200

        def __init__(self):
            self.raw = SimpleNamespace(isclosed=True)
            self.body = json.dumps({
                "result": {"response": {"unexpected": "synthetic response body sentinel"}}
            }).encode("utf-8")
            self.headers = {"Content-Length": str(len(self.body))}

        def iter_content(self, chunk_size=None):
            yield self.body

        def close(self):
            return None

    monkeypatch.setattr(enrichment_worker.requests, "post", lambda *_args, **_kwargs: InvalidShapeResponse())
    assert worker._call_cloudflare("synthetic prompt sentinel") is None
    assert "category=invalid_provider_response" in events[-1]
    diagnostic_text = "\n".join(events)
    for sentinel in (
        "synthetic-secret-sentinel",
        "synthetic-account-sentinel",
        "synthetic response body sentinel",
        "synthetic prompt sentinel",
    ):
        assert sentinel not in diagnostic_text


def test_cloudflare_provider_statuses_and_timeouts_are_categorized_without_retry(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    events: list[str] = []
    calls: list[int] = []

    class CaptureLogger:
        def warning(self, message, *args):
            events.append(message % args if args else message)

        def error(self, message, *args):
            events.append(message % args if args else message)

    class StatusResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    monkeypatch.setattr(enrichment_worker, "logger", CaptureLogger())
    monkeypatch.setattr(enrichment_worker, "CF_API_TOKEN", "synthetic-secret-sentinel")
    monkeypatch.setattr(enrichment_worker, "CF_ACCOUNT_ID", "synthetic-account-sentinel")

    for status_code, category in (
        (403, "auth_or_permission"),
        (410, "model_or_endpoint"),
        (429, "rate_limited"),
        (503, "transient_http"),
    ):
        def fake_post(*_args, _status_code=status_code, **_kwargs):
            calls.append(_status_code)
            return StatusResponse(_status_code)

        monkeypatch.setattr(enrichment_worker.requests, "post", fake_post)
        assert worker._call_cloudflare("synthetic prompt sentinel") is None
        assert f"category={category}" in events[-1]

    def timeout(*_args, **_kwargs):
        calls.append(-1)
        raise enrichment_worker.requests.Timeout("synthetic timeout body sentinel")

    monkeypatch.setattr(enrichment_worker.requests, "post", timeout)
    assert worker._call_cloudflare("synthetic prompt sentinel") is None
    assert "category=timeout" in events[-1]
    assert len(calls) == 5
    diagnostic_text = "\n".join(events)
    assert "synthetic timeout body sentinel" not in diagnostic_text
    assert "synthetic-secret-sentinel" not in diagnostic_text
    assert "synthetic-account-sentinel" not in diagnostic_text
