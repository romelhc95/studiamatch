"""Repository-level guards for the manual FG2 cohort handoff."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/production_pipeline.yml"


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

    def run_health_checks(self):
        for provider in self.providers:
            provider._healthy = True
        return [provider.name for provider in self.providers]

    def call_with_fallback(self, _prompt, _clean_fn):
        return ({
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
        }, "fixture-provider")

    def _all_degraded(self):
        return False

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


def test_main_schedule_propagates_a_run_scoped_manifest_to_all_workers() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "FG2_SCHEDULED_COHORT: ${{ github.event_name == 'schedule' && github.ref == 'refs/heads/main' }}" in workflow
    assert "--scheduled-cohort --cohort-manifest \"$RUNNER_TEMP/fg2-cohort-manifest.json\"" in workflow
    assert "FG2_COHORT_SCOPED: ${{ (github.event_name == 'schedule' && github.ref == 'refs/heads/main')" in workflow
    assert "if: always() && (github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.bounded_first_run))" in workflow
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


def test_fg2_workflow_entrypoints_complete_across_runner_manifest_handoffs(tmp_path: Path) -> None:
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
        "discovery_mode": "hardcoded_urls",
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "pipeline_ready": True,
        "production_enabled": True,
        "circuit_open": False,
        "seed_urls": [f"{blocked_seed}/", f"{new_url}/", f"{refresh_url}/"],
        "exclusion_patterns": ["/pregrado/"],
        "allowed_url_patterns": ["/programs/"],
    }
    preflight = validate_controlled_profile(institution, profile)
    assert preflight["seed_urls"] == [new_url, refresh_url]

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
                (new_url, "new_discovery", []),
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
    ], harvest_env)
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

    def run_worker(stage: str, script: str, *, expected: int = 0) -> None:
        manifest, worker_env = restore_runner_manifest(stage)
        run_entrypoint([
            sys.executable,
            str(ROOT / "scripts/core" / script),
            "--cohort-manifest", str(manifest),
            "--cohort-manifest-sha256", outputs["cohort_manifest_sha256"],
        ], worker_env, expected=expected)

    run_worker("cleansing", "cleansing_worker.py")
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


def test_fg2_ci_fixture_records_the_pull_request_source_sha() -> None:
    """The isolated E2E records the candidate commit rather than the PR merge ref."""
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text()
    fixture_runner = (ROOT / "tests/fg2_full_pipeline_pg17/run.sh").read_text()

    assert "FG2_FIXTURE_SOURCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert 'source_sha="${FG2_FIXTURE_SOURCE_SHA:-95d0e7d52e5c2c67eb473a2f12fc7df4d89fc40b}"' in fixture_runner
    assert "invalid_source_sha" in fixture_runner
