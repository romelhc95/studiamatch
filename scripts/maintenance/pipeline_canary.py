"""Run an isolated downstream pipeline canary and always remove its fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

from scripts.shared.supabase_credentials import (
    SupabaseCredentialError,
    build_supabase_headers,
)


ROOT = Path(__file__).resolve().parents[2]
PROJECT_REFS = {"free": "aqrldlmlszjtgpqiegaa", "pro": "xwhtiqmboljkshrtviyw"}
FINGERPRINT_COLUMNS = {
    "institutions": "*",
    "institution_site_profiles": "*",
    "staging_raw": "*",
    "cleansed_programs": "*",
    "enriched_programs": "*",
    "courses": "*",
}


class CanaryError(RuntimeError):
    pass


class StrictRest:
    def __init__(self, url, secret_key, publishable_key):
        self.url = url.rstrip("/")
        self._publishable_key = publishable_key
        self.secret_headers = build_supabase_headers(secret_key, kind="secret")
        self.public_headers = build_supabase_headers(
            publishable_key,
            kind="publishable",
        )

    def _request(
        self, method, table, query="", payload=None, public=False,
        permission_denied_is_empty=False, access_token=None,
    ):
        headers = dict(self.public_headers if public else self.secret_headers)
        if access_token:
            headers = build_supabase_headers(
                self._publishable_key,
                kind="publishable",
                access_token=access_token,
            )
        if method in {"POST", "PATCH", "DELETE"}:
            headers["Prefer"] = "return=representation"
        response = None
        for attempt in range(3):
            try:
                response = requests.request(
                    method,
                    f"{self.url}/rest/v1/{table}{'?' + query if query else ''}",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
                continue
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                break
            time.sleep(2 ** attempt)
        if response is None:
            raise CanaryError(f"Data API {method} {table} produced no response")
        if public and response.status_code in {401, 403}:
            try:
                error_code = response.json().get("code")
            except (ValueError, AttributeError):
                error_code = None
            if permission_denied_is_empty and error_code == "42501":
                return []
        if response.status_code not in {200, 201, 204, 206}:
            raise CanaryError(f"Data API {method} {table} failed with HTTP {response.status_code}")
        if not response.content:
            return []
        data = response.json()
        if not isinstance(data, list):
            raise CanaryError(f"Data API {table} returned an unexpected shape")
        return data

    def select_all(
        self, table, columns, query="", public=False,
        permission_denied_is_empty=False,
    ):
        rows = []
        offset = 0
        while True:
            page_query = f"select={columns}&limit=1000&offset={offset}"
            if query:
                page_query += f"&{query}"
            page_query += "&order=id.asc"
            page = self._request(
                "GET", table, page_query, public=public,
                permission_denied_is_empty=permission_denied_is_empty,
            )
            rows.extend(page)
            if len(page) < 1000:
                return rows
            offset += 1000

    def insert(self, table, payload):
        rows = self._request("POST", table, payload=payload)
        if len(rows) != 1:
            raise CanaryError(f"Expected one inserted row in {table}, got {len(rows)}")
        return rows[0]

    def patch_one(self, table, row_id, payload):
        rows = self._request("PATCH", table, f"id=eq.{row_id}", payload=payload)
        if len(rows) != 1:
            raise CanaryError(f"Expected one patched row in {table}, got {len(rows)}")

    def delete(self, table, query):
        return self._request("DELETE", table, query)

    def rpc(self, function_name, payload=None):
        return self._request("POST", f"rpc/{function_name}", payload=payload or {})

    def rpc_with_access_token(self, function_name, access_token, payload=None):
        return self._request(
            "POST", f"rpc/{function_name}", payload=payload or {},
            access_token=access_token,
        )


def _fingerprint_out_of_scope(api, institution_id):
    result = {}
    for table, columns in FINGERPRINT_COLUMNS.items():
        if table == "institutions":
            query = f"id=neq.{institution_id}"
        else:
            query = f"or=(institution_id.neq.{institution_id},institution_id.is.null)"
        rows = api.select_all(table, columns, query)
        payload = json.dumps(sorted(rows, key=lambda row: row.get("id", "")), sort_keys=True, default=str)
        result[table] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return result


def _run_worker(arguments, worker_root, worker_image=None):
    command = [sys.executable, *arguments]
    cwd = worker_root
    cidfile = None
    env = os.environ.copy()
    env["STUDIAMATCH_CANARY_WORKER"] = "1"
    if env.get("NEXT_SUPABASE_ACCESS_TOKEN"):
        env.pop("NEXT_SUPABASE_SECRET_KEY", None)
    if worker_image:
        descriptor, cidfile_name = tempfile.mkstemp(prefix="studiamatch-canary-", suffix=".cid")
        os.close(descriptor)
        Path(cidfile_name).unlink()
        cidfile = Path(cidfile_name)
        command = [
            "docker", "run", "--rm", "--read-only", "--cap-drop=ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "128",
            "--memory", "1g", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--cidfile", str(cidfile),
        ]
        for name in (
            "SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL",
            "NEXT_SUPABASE_PUBLISHABLE_KEY", "NEXT_SUPABASE_ACCESS_TOKEN",
            "STUDIAMATCH_CANARY_WORKER",
        ):
            command.extend(["--env", name])
        command.extend([worker_image, *arguments])
        cwd = ROOT
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        if cidfile and cidfile.exists():
            container_id = cidfile.read_text(encoding="utf-8").strip()
            if container_id:
                subprocess.run(
                    ["docker", "rm", "--force", container_id],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
        raise CanaryError(f"Worker timed out: {arguments[0]}") from exc
    finally:
        if cidfile:
            cidfile.unlink(missing_ok=True)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-500:].replace("\n", " ")
        raise CanaryError(f"Worker failed: {arguments[0]} ({tail})")


def _count_rows(api, table, institution_id, public=False):
    return len(api.select_all(table, "id", f"institution_id=eq.{institution_id}", public=public))


def _validate_run_manifest(run_manifest, expected_env):
    run_id = str(run_manifest.get("run_id", ""))
    if run_manifest.get("environment") != expected_env or not run_id.isdigit():
        raise CanaryError("Cleanup manifest environment or run ID is invalid")
    try:
        uuid.UUID(str(run_manifest["institution_id"]))
        uuid.UUID(str(run_manifest["staging_id"]))
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise CanaryError("Cleanup manifest UUIDs are invalid") from exc
    expected_slug = f"zz-studiamatch-canary-{expected_env}-{run_id}"
    expected_prefix = f"https://canary.invalid/{expected_env}/{run_id}/"
    if run_manifest.get("slug") != expected_slug or run_manifest.get("url_prefix") != expected_prefix:
        raise CanaryError("Cleanup manifest is outside the reserved canary namespace")


def _cleanup(api, run_manifest):
    institution_id = run_manifest["institution_id"]
    expected_slug = run_manifest["slug"]
    expected_prefix = run_manifest["url_prefix"]
    errors = []
    institutions = api.select_all(
        "institutions", "id,slug,status", f"id=eq.{institution_id}"
    )
    profiles = api.select_all(
        "institution_site_profiles", "id,institution_id,notes,production_enabled",
        f"institution_id=eq.{institution_id}",
    )
    fixture_rows = {
        table: api.select_all(table, "id,url", f"institution_id=eq.{institution_id}")
        for table in ("staging_raw", "cleansed_programs", "enriched_programs", "courses")
    }
    if not institutions and not profiles and not any(fixture_rows.values()):
        return []
    if len(institutions) > 1 or len(profiles) > 1:
        raise CanaryError("Cleanup markers do not match the reserved canary fixture")
    if institutions and (
        institutions[0].get("slug") != expected_slug
        or institutions[0].get("status") != "Inactiva"
    ):
        raise CanaryError("Cleanup institution marker does not match the reserved canary fixture")
    if profiles and (
        profiles[0].get("notes") != "DB_AS_CODE_RELEASE_CANARY"
        or profiles[0].get("production_enabled") is not False
    ):
        raise CanaryError("Cleanup profile marker does not match the reserved canary fixture")
    for table, rows in fixture_rows.items():
        if any(not str(row.get("url") or "").startswith(expected_prefix) for row in rows):
            raise CanaryError(f"Cleanup found a non-canary URL in {table}")
    try:
        for profile in profiles:
            api.patch_one(
                "institution_site_profiles",
                profile["id"],
                {
                    "pipeline_ready": False,
                    "discovery_enabled": False,
                    "pipeline_enabled": False,
                    "production_enabled": False,
                },
            )
    except Exception as exc:
        errors.append(str(exc))
    course_ids = [row["id"] for row in fixture_rows["courses"]]
    child_rows = {"email_log": [], "leads": [], "ratings": [], "reviews": []}
    if course_ids:
        course_filter = f"course_id=in.({','.join(course_ids)})"
        leads = api.select_all("leads", "id", course_filter)
        child_rows["leads"] = leads
        child_rows["ratings"] = api.select_all("ratings", "id", course_filter)
        child_rows["reviews"] = api.select_all("reviews", "id", course_filter)
        lead_ids = [row["id"] for row in leads]
        if lead_ids:
            lead_filter = f"lead_id=in.({','.join(lead_ids)})"
            child_rows["email_log"] = api.select_all("email_log", "id", lead_filter)
            try:
                api.delete("email_log", lead_filter)
            except Exception as exc:
                errors.append(f"email_log: {exc}")
        for child in ("leads", "ratings", "reviews"):
            try:
                api.delete(child, course_filter)
            except Exception as exc:
                errors.append(f"{child}: {exc}")
    for table in ("courses", "enriched_programs", "cleansed_programs", "staging_raw", "institution_site_profiles"):
        try:
            api.delete(table, f"institution_id=eq.{institution_id}")
        except Exception as exc:
            errors.append(f"{table}: {exc}")
    try:
        api.delete("institutions", f"id=eq.{institution_id}")
    except Exception as exc:
        errors.append(f"institutions: {exc}")
    for table, rows in child_rows.items():
        ids = [row["id"] for row in rows]
        if ids and api.select_all(table, "id", f"id=in.({','.join(ids)})"):
            errors.append(f"{table}: cleanup left dependent rows")
    return errors


def _remaining_fixture_rows(api, institution_id):
    counts = {
        table: _count_rows(api, table, institution_id)
        for table in ("staging_raw", "cleansed_programs", "enriched_programs", "courses")
    }
    counts["institution_site_profiles"] = len(api.select_all(
        "institution_site_profiles", "institution_id", f"institution_id=eq.{institution_id}"
    ))
    counts["institutions"] = len(api.select_all("institutions", "id", f"id=eq.{institution_id}"))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", choices=["free", "pro"], required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cleanup-manifest", type=Path)
    parser.add_argument("--worker-root", type=Path, default=ROOT)
    parser.add_argument("--worker-image")
    parser.add_argument("--candidate-commit")
    args = parser.parse_args()
    worker_root = args.worker_root.resolve()
    expected_ref = PROJECT_REFS[args.env]
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    secret_key = os.environ.get("NEXT_SUPABASE_SECRET_KEY", "")
    publishable_key = os.environ.get("NEXT_SUPABASE_PUBLISHABLE_KEY", "")
    if urlparse(url).hostname != f"{expected_ref}.supabase.co" or not secret_key or not publishable_key:
        print("NO_GO: Canary credentials do not match the target environment", file=sys.stderr)
        return 1
    if args.worker_image and not os.environ.get("NEXT_SUPABASE_ACCESS_TOKEN"):
        print("NO_GO: isolated workers require NEXT_SUPABASE_ACCESS_TOKEN", file=sys.stderr)
        return 1

    institution_id = str(uuid.uuid4())
    staging_id = str(uuid.uuid4())
    slug = f"zz-studiamatch-canary-{args.env}-{args.run_id}"
    fixture_url = f"https://canary.invalid/{args.env}/{args.run_id}/programa-control/"
    try:
        api = StrictRest(url, secret_key, publishable_key)
    except SupabaseCredentialError as exc:
        print(f"NO_GO: invalid modern Supabase API key configuration: {exc}", file=sys.stderr)
        return 1
    if args.cleanup_manifest:
        try:
            run_manifest = json.loads(args.cleanup_manifest.read_text(encoding="utf-8"))
            _validate_run_manifest(run_manifest, args.env)
            errors = _cleanup(api, run_manifest)
            counts = _remaining_fixture_rows(api, run_manifest["institution_id"])
            remaining = sum(counts.values())
            cleanup_report = {
                "environment": args.env,
                "run_id": run_manifest.get("run_id"),
                "institution_id": run_manifest["institution_id"],
                "errors": errors,
                "remaining_rows": remaining,
                "counts": counts,
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(cleanup_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return 0 if not errors and remaining == 0 else 1
        except (OSError, KeyError, json.JSONDecodeError, CanaryError) as exc:
            print(f"NO_GO: cleanup failed: {exc}", file=sys.stderr)
            return 1
    if not args.run_id or not args.run_id.isdigit():
        print("NO_GO: --run-id is required for a canary run", file=sys.stderr)
        return 1
    if not args.candidate_commit or not re.fullmatch(r"[0-9a-f]{40}", args.candidate_commit):
        print("NO_GO: --candidate-commit must be a full SHA", file=sys.stderr)
        return 1
    if args.worker_image:
        identity_rows = api.rpc_with_access_token(
            "verify_canary_runner_identity",
            os.environ["NEXT_SUPABASE_ACCESS_TOKEN"],
        )
        if len(identity_rows) != 1:
            print("NO_GO: canary access token identity is ambiguous", file=sys.stderr)
            return 1
        identity = identity_rows[0]
        try:
            expires_at = datetime.fromisoformat(str(identity["expires_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            print("NO_GO: canary access token expiration is invalid", file=sys.stderr)
            return 1
        remaining_seconds = (expires_at - datetime.now(timezone.utc)).total_seconds()
        if (
            identity.get("effective_role") != "canary_runner"
            or identity.get("jwt_role") != "canary_runner"
            or remaining_seconds < 300
            or remaining_seconds > 86400
        ):
            print("NO_GO: canary access token is not least-privilege and short-lived", file=sys.stderr)
            return 1
    report = {
        "environment": args.env,
        "run_id": args.run_id,
        "candidate_commit": args.candidate_commit,
        "institution_id": institution_id,
        "fixture_url_sha256": hashlib.sha256(fixture_url.encode("utf-8")).hexdigest(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "worker_sha256": {
            name: hashlib.sha256((worker_root / path).read_bytes()).hexdigest()
            for name, path in {
                "cleansing": "scripts/core/cleansing_worker.py",
                "enrichment": "scripts/core/enrichment_worker.py",
                "sync": "scripts/core/sync_vector_worker.py",
            }.items()
        },
    }
    exit_code = 1
    baseline = None
    run_manifest_path = args.output.parent / "run-manifest.json"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run_manifest_path.write_text(
        json.dumps({
            "environment": args.env,
            "run_id": args.run_id,
            "institution_id": institution_id,
            "staging_id": staging_id,
            "slug": slug,
            "url_prefix": f"https://canary.invalid/{args.env}/{args.run_id}/",
            "candidate_commit": args.candidate_commit,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        guard_rows = api.rpc("verify_release_canary_guards")
        if guard_rows != [{"guards_valid": True}]:
            raise CanaryError("Reserved canary RLS guards are missing or invalid")
        baseline = _fingerprint_out_of_scope(api, institution_id)
        encoded_url = quote(fixture_url, safe="")
        for table in ("staging_raw", "cleansed_programs", "enriched_programs", "courses"):
            if api.select_all(table, "id,institution_id", f"url=eq.{encoded_url}"):
                raise CanaryError(f"Reserved fixture URL already exists in {table}")
        api.insert("institutions", {
            "id": institution_id,
            "name": f"StudIAMatch Canary {args.run_id}",
            "slug": slug,
            "website_url": "https://canary.invalid",
            "official_website": "https://canary.invalid",
            "type": "Inst",
            "status": "Inactiva",
        })
        api.insert("institution_site_profiles", {
            "institution_id": institution_id,
            "site_type": "traditional_ssr",
            "discovery_mode": "hardcoded_urls",
            "seed_urls": [fixture_url],
            "allowed_url_patterns": [r"re:^/free/|^/pro/"],
            "exclusion_patterns": [],
            "noise_patterns": [],
            "max_courses_per_run": 1,
            "pipeline_ready": True,
            "discovery_enabled": True,
            "pipeline_enabled": True,
            "production_enabled": False,
            "circuit_open": False,
            "notes": "DB_AS_CODE_RELEASE_CANARY",
            "field_defaults": {"mode": "Remoto", "price_status": "consultar"},
        })
        fixture_html = (
            "<html><body><h1>Programa Control de Analitica</h1>"
            "<p>Curso sintetico para validar aislamiento, limpieza y publicacion segura.</p>"
            "<p>Modalidad: Remoto. Duracion: 16 horas. Precio: S/ 100.</p>"
            "<h2>Temario</h2><ul><li>Fundamentos</li><li>Proyecto controlado</li></ul>"
            "</body></html>"
        )
        api.insert("staging_raw", {
            "id": staging_id,
            "institution_id": institution_id,
            "url": fixture_url,
            "raw_name": "Programa Control de Analitica",
            "raw_description": "Curso sintetico para validar el pipeline de extremo a extremo.",
            "raw_html": fixture_html,
            "content_hash": hashlib.sha256(fixture_html.encode("utf-8")).hexdigest(),
            "status": "pending",
            "metadata": {"canary_run_id": args.run_id},
        })

        _run_worker([
            "scripts/core/cleansing_worker.py", "--institution-id", institution_id,
            "--limit", "1", "--require-atomic-rpc",
        ], worker_root, args.worker_image)
        _run_worker([
            "scripts/core/enrichment_worker.py", "--institution-id", institution_id,
            "--limit", "1", "--require-atomic-rpc", "--mock-only",
        ], worker_root, args.worker_image)
        _run_worker([
            "scripts/core/sync_vector_worker.py", "--institution-id", institution_id,
            "--limit", "1", "--canary-mode",
        ], worker_root, args.worker_image)

        staging_rows = api.select_all(
            "staging_raw", "id,institution_id,url,status,metadata", f"institution_id=eq.{institution_id}"
        )
        cleansed_rows = api.select_all(
            "cleansed_programs", "id,staging_id,institution_id,url,status", f"institution_id=eq.{institution_id}"
        )
        enriched_rows = api.select_all(
            "enriched_programs", "id,cleansed_id,institution_id,url,status", f"institution_id=eq.{institution_id}"
        )
        courses = api.select_all(
            "courses", "id,is_active,is_verified,url,provider_used,is_mock_data",
            f"institution_id=eq.{institution_id}"
        )
        if not (
            len(staging_rows) == len(cleansed_rows) == len(enriched_rows) == len(courses) == 1
            and staging_rows[0]["id"] == staging_id
            and staging_rows[0]["status"] == "processed"
            and staging_rows[0].get("metadata", {}).get("canary_run_id") == args.run_id
            and cleansed_rows[0]["staging_id"] == staging_id
            and cleansed_rows[0]["status"] == "enriched"
            and enriched_rows[0]["cleansed_id"] == cleansed_rows[0]["id"]
            and enriched_rows[0]["status"] == "synced"
            and all(
                row["url"] == fixture_url
                for row in (staging_rows[0], cleansed_rows[0], enriched_rows[0], courses[0])
            )
        ):
            raise CanaryError("Canary lineage, URL, or terminal states are invalid")
        if courses[0].get("is_active") is not False:
            raise CanaryError("Canary course became active")
        if courses[0].get("provider_used") != "mock" or courses[0].get("is_mock_data") is not True:
            raise CanaryError("Canary enrichment did not use deterministic mock provenance")
        public_checks = {
            "institutions": ("id", f"id=eq.{institution_id}"),
            "institution_site_profiles": ("institution_id", f"institution_id=eq.{institution_id}"),
            "staging_raw": ("id", f"institution_id=eq.{institution_id}"),
            "cleansed_programs": ("id", f"institution_id=eq.{institution_id}"),
            "enriched_programs": ("id", f"institution_id=eq.{institution_id}"),
            "courses": ("id", f"institution_id=eq.{institution_id}"),
        }
        for table, (columns, query) in public_checks.items():
            if api.select_all(
                table, columns, query, public=True,
                permission_denied_is_empty=table in {
                    "staging_raw", "cleansed_programs", "enriched_programs"
                },
            ):
                raise CanaryError(f"Public API exposed canary rows from {table}")
        post = _fingerprint_out_of_scope(api, institution_id)
        if baseline != post:
            raise CanaryError("Out-of-scope pipeline fingerprint changed")
        report["checks"] = {
            "pipeline_lineage": "PASS",
            "public_fixtures_zero": "PASS",
            "out_of_scope_mutations_zero": "PASS",
            "production_enabled_false": "PASS",
            "rpc_fallback_zero": "PASS",
            "rls_guard_definitions": "PASS",
            "mock_provenance": "PASS",
        }
        exit_code = 0
    except Exception as exc:
        report["error"] = str(exc)[:500]
    finally:
        run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        try:
            cleanup_errors = _cleanup(api, run_manifest)
        except Exception as exc:
            cleanup_errors = [str(exc)]
        report["cleanup_errors"] = cleanup_errors
        try:
            counts = _remaining_fixture_rows(api, institution_id)
            remaining = sum(counts.values())
            report["cleanup_remaining_rows"] = remaining
            report["cleanup_counts"] = counts
            if remaining or cleanup_errors:
                exit_code = 1
            if baseline is not None:
                cleanup_fingerprint = _fingerprint_out_of_scope(api, institution_id)
                report["cleanup_out_of_scope_unchanged"] = cleanup_fingerprint == baseline
                if cleanup_fingerprint != baseline:
                    exit_code = 1
        except Exception as exc:
            report["cleanup_verification_error"] = str(exc)[:500]
            exit_code = 1
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if exit_code:
        print("NO_GO: pipeline canary failed; inspect report artifact", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
