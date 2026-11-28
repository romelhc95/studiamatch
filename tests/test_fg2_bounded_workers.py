"""Synthetic queue isolation contracts for every downstream FG2 stage."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

core_script_dir = str(Path(__file__).resolve().parents[1] / "scripts" / "core")
if core_script_dir not in sys.path:
    sys.path.insert(0, core_script_dir)

from scripts.core.cleansing_worker import CleansingWorker
from scripts.core.enrichment_worker import ControlledEnrichmentUnavailable, EnrichmentWorker
from scripts.core.fg2_bounded_run import (
    FG2CohortManifest,
    InvalidControlledRun,
    FG2_LIMITS,
    cleanse_course_url,
    cleansed_url_sha256,
    reviewed_exact_progress_missing,
    url_sha256,
)
from scripts.core.sync_vector_worker import SyncVectorWorker


INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"
RAW_ID = "40000000-0000-0000-0000-000000000001"
CLEANSED_ID = "50000000-0000-0000-0000-000000000001"
ENRICHED_ID = "60000000-0000-0000-0000-000000000001"
URL = "https://synthetic.example/program/known"
RAW_HTML = "<!doctype html><html><title>Known Program</title><body>synthetic fixture</body></html>"
CONTENT_SHA = hashlib.sha256(RAW_HTML.encode()).hexdigest()


def cohort_manifest(result: str = "complete") -> FG2CohortManifest:
    payload = {
        "schema_version": 1,
        "run_id": "123456789",
        "run_attempt": 1,
        "source_sha": "a" * 40,
        "limits": dict(FG2_LIMITS),
        "institutions": [
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 2,
                "unique_urls": 1,
                "result": result,
            }
        ],
        "entries": [
            {
                "institution_id": INSTITUTION_ID,
                "staging_id": RAW_ID,
                "course_id": "70000000-0000-0000-0000-000000000001",
                "url_sha256": url_sha256(URL),
                "content_sha256": CONTENT_SHA,
                "kind": "refresh_existing",
            }
        ],
        "blocked_staging_rows": [],
    }
    return FG2CohortManifest.from_payload(payload)


class SelectAdapter:
    def __init__(self, responses: dict[str, list[dict]], profiles: list[dict] | None = None) -> None:
        self.responses = responses
        self.profiles = profiles or [
            {"institution_id": INSTITUTION_ID, "pipeline_enabled": True, "exclusion_patterns": []}
        ]
        self.calls: list[tuple[str, str]] = []
        self.writes: list[tuple[str, str, dict]] = []
        self.rpc_calls: list[tuple[str, dict]] = []

    def select_pipeline_raise(self, table: str, **_kwargs):
        if table == "institution_site_profiles":
            return [dict(row) for row in self.profiles]
        return [dict(row) for row in self.responses.get(table, [])]

    def select_service_raise(self, table: str, **_kwargs):
        assert table == "institutions"
        return [{"website_url": "https://synthetic.example/"}]

    def select_all_pipeline(self, table: str, filters: str = "", **_kwargs):
        self.calls.append((table, filters))
        return [dict(row) for row in self.responses.get(table, [])]

    def upsert(self, table: str, data: dict, **_kwargs):
        self.writes.append(("upsert", table, data))
        return {"id": data.get("id")}

    def patch(self, table: str, filters: str, data: dict, **_kwargs):
        self.writes.append(("patch", table, data))
        return True

    def patch_raise(self, table: str, filters: str, data: dict, **_kwargs):
        return self.patch(table, filters, data, **_kwargs)

    def rpc_raise(self, name: str, params: dict):
        self.rpc_calls.append((name, params))
        return True


def raw_row() -> dict:
    return {
        "id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "content_hash": CONTENT_SHA,
        "raw_html": RAW_HTML,
        "status": "pending",
    }


@pytest.mark.parametrize("reverse_profiles", [False, True])
def test_cleansing_profile_exclusions_are_global_or_scoped_to_their_owner(
    reverse_profiles: bool,
) -> None:
    utec_id = "50d8779c-54fd-437e-b941-e817e202e60c"
    pacifico_id = "a4fd99a6-d161-4854-bdc8-6b5f1bd8163e"
    profiles = [
        {
            "institution_id": utec_id,
            "pipeline_enabled": True,
            "exclusion_patterns": json.dumps([".pdf", "/noticias/", "/utec-only/", "re:utec-regex/"]),
        },
        {
            "institution_id": pacifico_id,
            "pipeline_enabled": True,
            "exclusion_patterns": [".pdf", "/maestrias/", "re:[", "re:(a+)+$"],
        },
    ]
    if reverse_profiles:
        profiles.reverse()
    worker = CleansingWorker(db_client=SelectAdapter({}, profiles=profiles))
    worker._get_institution_website = lambda _institution_id: ""
    worker._get_noise_patterns_for_inst = lambda _institution_id: []

    utec_maestria = "https://posgrado.utec.edu.pe/maestrias/programa"
    pacifico_maestria = "https://posgrado.pacifico.edu.pe/maestrias/programa"
    assert worker.is_invalid_course("Programa de maestría", "", utec_maestria, institution_id=utec_id) is None
    assert worker.is_invalid_course("Programa de maestría", "", pacifico_maestria, institution_id=pacifico_id) == "hard_db_exclusion:/maestrias/"

    assert worker.is_invalid_course("Noticias", "", "https://posgrado.utec.edu.pe/noticias/programa", institution_id=utec_id) == "hard_db_exclusion:/noticias/"
    assert worker.is_invalid_course("Programa", "", "https://posgrado.pacifico.edu.pe/noticias/programa", institution_id=pacifico_id) == "hard_db_exclusion:/noticias/"
    assert worker.is_invalid_course("Programa", "", "https://posgrado.utec.edu.pe/utec-only/programa", institution_id=utec_id) == "hard_db_exclusion:/utec-only/"
    assert worker.is_invalid_course("Programa", "", "https://posgrado.pacifico.edu.pe/utec-only/programa", institution_id=pacifico_id) is None
    assert worker.is_invalid_course("Programa", "", "https://posgrado.utec.edu.pe/utec-regex/programa", institution_id=utec_id) == "hard_db_exclusion:regex:utec-regex/"

    # The exact global default remains active for both profiles.
    assert worker.is_invalid_course("Documento", "", "https://posgrado.utec.edu.pe/plan.pdf", institution_id=utec_id) == "hard_db_exclusion:.pdf"
    assert worker.is_invalid_course("Documento", "", "https://posgrado.pacifico.edu.pe/plan.pdf", institution_id=pacifico_id) == "hard_db_exclusion:.pdf"


@pytest.mark.parametrize("operation", ["add", "modify", "delete"])
def test_third_profile_changes_preserve_utec_pacifico_classification_and_scope_its_rules(
    operation: str,
) -> None:
    utec_id = "50d8779c-54fd-437e-b941-e817e202e60c"
    pacifico_id = "a4fd99a6-d161-4854-bdc8-6b5f1bd8163e"
    third_id = "30000000-0000-0000-0000-000000000003"
    base_profiles = [
        {"institution_id": utec_id, "pipeline_enabled": True, "exclusion_patterns": ["/utec-only/"]},
        {"institution_id": pacifico_id, "pipeline_enabled": True, "exclusion_patterns": ["/maestrias/"]},
    ]
    third_profile = {
        "institution_id": third_id,
        "pipeline_enabled": True,
        "exclusion_patterns": ["/third-only/"],
    }
    initial_profiles = [*base_profiles, third_profile] if operation != "add" else list(base_profiles)
    changed_third_profile = {
        **third_profile,
        "exclusion_patterns": ["re:/maestrias/|/third-only/"],
    }
    if operation == "add":
        changed_profiles = [*base_profiles, changed_third_profile]
    elif operation == "modify":
        changed_profiles = [
            changed_third_profile if profile["institution_id"] == third_id else profile
            for profile in initial_profiles
        ]
    else:
        changed_profiles = [profile for profile in initial_profiles if profile["institution_id"] != third_id]

    utec_url = "https://posgrado.utec.edu.pe/maestrias/programa"
    pacifico_url = "https://posgrado.pacifico.edu.pe/maestrias/programa"

    def classify(profiles: list[dict], institution_id: str, url: str):
        worker = CleansingWorker(db_client=SelectAdapter({}, profiles=profiles))
        worker._get_institution_website = lambda _institution_id: ""
        worker._get_noise_patterns_for_inst = lambda _institution_id: []
        return worker.is_invalid_course("Programa de maestría", "", url, institution_id=institution_id)

    before = {
        (utec_id, utec_url): classify(initial_profiles, utec_id, utec_url),
        (pacifico_id, pacifico_url): classify(initial_profiles, pacifico_id, pacifico_url),
    }
    after = {
        (utec_id, utec_url): classify(changed_profiles, utec_id, utec_url),
        (pacifico_id, pacifico_url): classify(changed_profiles, pacifico_id, pacifico_url),
    }

    assert before == after
    assert after == {
        (utec_id, utec_url): None,
        (pacifico_id, pacifico_url): "hard_db_exclusion:/maestrias/",
    }
    if operation != "delete":
        assert classify(changed_profiles, third_id, utec_url) == "hard_db_exclusion:regex:/maestrias/|/third-only/"
        assert classify(
            changed_profiles,
            third_id,
            "https://catalog.third.example/third-only/programa",
        ) == "hard_db_exclusion:regex:/maestrias/|/third-only/"
        assert classify(
            changed_profiles,
            third_id,
            "https://catalog.third.example/utec-only/programa",
        ) is None
    else:
        assert classify(
            initial_profiles,
            third_id,
            "https://catalog.third.example/third-only/programa",
        ) == "hard_db_exclusion:/third-only/"


def test_foreign_profile_changes_leave_all_28_owner_classifications_unchanged() -> None:
    profiles = [
        {
            "institution_id": f"00000000-0000-0000-0000-{index:012d}",
            "pipeline_enabled": True,
            "exclusion_patterns": [f"/owner-{index}-only/"],
        }
        for index in range(1, 29)
    ]
    results = []
    for owner_index, profile in enumerate(profiles):
        owner_id = profile["institution_id"]
        foreign_index = (owner_index + 1) % len(profiles)
        foreign_id = profiles[foreign_index]["institution_id"]
        url = f"https://owner-{owner_index + 1}.example/fg2-policy-regression/course"
        before = CleansingWorker(
            db_client=SelectAdapter({}, profiles=profiles)
        )
        changed_profiles = [dict(candidate, exclusion_patterns=list(candidate["exclusion_patterns"])) for candidate in profiles]
        foreign_profile = next(item for item in changed_profiles if item["institution_id"] == foreign_id)
        foreign_profile["exclusion_patterns"].append("/fg2-policy-regression/")
        after = CleansingWorker(db_client=SelectAdapter({}, profiles=changed_profiles))
        before._get_institution_website = lambda _institution_id: ""
        after._get_institution_website = lambda _institution_id: ""
        before._get_noise_patterns_for_inst = lambda _institution_id: []
        after._get_noise_patterns_for_inst = lambda _institution_id: []
        decision_before = before.is_invalid_course("Programa válido", "", url, institution_id=owner_id)
        decision_after = after.is_invalid_course("Programa válido", "", url, institution_id=owner_id)
        results.append(decision_before is None and decision_after is None)

    assert len(results) == 28
    assert all(results)


@pytest.mark.parametrize("selected_identity_field", ["canonical_url", "effective_url", "url"])
def test_unmsm_admission_exclusion_runs_before_sibling_grouping(
    selected_identity_field: str,
) -> None:
    unmsm_id = "312d1aa3-69f2-4a46-87de-3f4f8f2d1352"
    allowed_url = "https://unmsm.edu.pe/formacion-academica/"
    admission_url = "https://unmsm.edu.pe/formacion-academica/admision"
    worker_db = SelectAdapter({}, profiles=[
        {
            "institution_id": unmsm_id,
            "pipeline_enabled": True,
            "exclusion_patterns": ["/admision/"],
        },
    ])
    worker = CleansingWorker(db_client=worker_db)
    worker._get_institution_website = lambda _institution_id: "https://unmsm.edu.pe/"
    worker._get_noise_patterns_for_inst = lambda _institution_id: []

    # Reproduce the old caller failure: the grouping identity erases /admision,
    # so evaluating exclusions only after cleanse_course_url misses the rule.
    assert worker._get_base_url(admission_url) == allowed_url
    assert worker.is_invalid_course(
        "Programa académico", "", worker._get_base_url(admission_url), institution_id=unmsm_id
    ) is None

    excluded_row = dict(
        raw_row(),
        institution_id=unmsm_id,
        url=admission_url if selected_identity_field == "url" else allowed_url,
        raw_name="Admisión académica",
    )
    if selected_identity_field == "effective_url":
        excluded_row["effective_url"] = admission_url
    elif selected_identity_field == "canonical_url":
        excluded_row["effective_url"] = allowed_url
        excluded_row["canonical_url"] = admission_url
    valid_sibling = dict(
        raw_row(),
        id="40000000-0000-0000-0000-000000000002",
        institution_id=unmsm_id,
        url=allowed_url,
        raw_name="Programa válido de formación académica",
    )

    processed = worker.process_batch([excluded_row, valid_sibling])

    assert processed == 1
    assert len(worker_db.rpc_calls) == 1
    rpc_name, rpc_params = worker_db.rpc_calls[0]
    assert rpc_name == "atomic_cleansing_promote"
    assert rpc_params["p_staging_ids"] == [valid_sibling["id"]]
    assert [item["staging_id"] for item in rpc_params["p_cleansed_data"]] == [valid_sibling["id"]]
    assert rpc_params["p_cleansed_data"][0]["url"] == allowed_url
    assert worker_db.writes == [
        (
            "patch",
            "staging_raw",
            {
                "status": "discarded",
                "metadata": {"discard_reason": "hard_db_exclusion:/admision/"},
            },
        )
    ]


def test_canonical_identity_has_priority_over_excluded_effective_and_requested_urls() -> None:
    unmsm_id = "312d1aa3-69f2-4a46-87de-3f4f8f2d1352"
    allowed_url = "https://unmsm.edu.pe/formacion-academica/"
    admission_url = "https://unmsm.edu.pe/formacion-academica/admision"
    worker_db = SelectAdapter({}, profiles=[
        {
            "institution_id": unmsm_id,
            "pipeline_enabled": True,
            "exclusion_patterns": ["/admision/"],
        },
    ])
    worker = CleansingWorker(db_client=worker_db)
    worker._get_institution_website = lambda _institution_id: "https://unmsm.edu.pe/"
    worker._get_noise_patterns_for_inst = lambda _institution_id: []
    canonical_wins = dict(
        raw_row(),
        institution_id=unmsm_id,
        url=admission_url,
        effective_url=admission_url,
        canonical_url=allowed_url,
        raw_name="Programa válido de formación académica",
    )

    assert worker.process_batch([canonical_wins]) == 1
    assert worker_db.rpc_calls[0][1]["p_cleansed_data"][0]["url"] == allowed_url
    assert worker_db.writes == []


def test_malformed_pucp_profile_fails_closed_without_blocking_another_owner() -> None:
    pucp_id = "f6b22a7f-62e8-4ef4-a91b-56096a6a7b6b"
    other_id = "00000000-0000-0000-0000-000000000009"
    worker_db = SelectAdapter({}, profiles=[
        {
            "institution_id": pucp_id,
            "pipeline_enabled": True,
            "exclusion_patterns": {"Count": 21, "value": ["/admision/"]},
        },
        {"institution_id": other_id, "pipeline_enabled": True, "exclusion_patterns": []},
    ])
    worker = CleansingWorker(db_client=worker_db)
    worker._get_institution_website = lambda _institution_id: ""
    worker._get_noise_patterns_for_inst = lambda _institution_id: []
    assert pucp_id not in worker.ready_inst_ids
    assert other_id in worker.ready_inst_ids

    malformed = dict(
        raw_row(),
        institution_id=pucp_id,
        url="https://www.pucp.edu.pe/programas/datos",
        raw_name="Programa PUCP de datos",
    )
    valid = dict(
        raw_row(),
        id="40000000-0000-0000-0000-000000000003",
        institution_id=other_id,
        url="https://other.example/programas/datos",
        raw_name="Programa válido de datos",
    )

    assert worker.process_batch([malformed, valid]) == 1
    assert worker_db.rpc_calls[0][1]["p_staging_ids"] == [valid["id"]]
    assert worker_db.writes == [
        (
            "patch",
            "staging_raw",
            {
                "status": "error",
                "metadata": {"processing_error": "invalid_profile_exclusion_policy"},
            },
        )
    ]


def test_all_discarded_reviewed_exact_cleansing_is_not_green_but_scheduler_noop_is_valid() -> None:
    utec_id = "50d8779c-54fd-437e-b941-e817e202e60c"
    worker_db = SelectAdapter({}, profiles=[
        {"institution_id": utec_id, "pipeline_enabled": True, "exclusion_patterns": ["/utec-only/"]},
    ])
    worker = CleansingWorker(db_client=worker_db)
    worker._get_institution_website = lambda _institution_id: ""
    worker._get_noise_patterns_for_inst = lambda _institution_id: []

    rejected_url = "https://posgrado.utec.edu.pe/utec-only/programa"
    row = dict(raw_row(), institution_id=utec_id, url=rejected_url, raw_name="Known Program")
    processed = worker.process_batch([row])
    assert processed == 0
    assert worker_db.writes == [
        ("patch", "staging_raw", {"status": "discarded", "metadata": {"discard_reason": "hard_db_exclusion:/utec-only/"}})
    ]

    payload = dict(cohort_manifest().payload)
    payload["approved_lot_selection"] = "reviewed_exact"
    payload["approved_lot_reference"] = "fixture-reviewed-progress"
    payload["approved_lot_sha256"] = "d" * 64
    payload["entries"] = [dict(payload["entries"][0], url_sha256=url_sha256(rejected_url))]
    manual_manifest = FG2CohortManifest.from_payload(payload)
    assert reviewed_exact_progress_missing(manual_manifest, processed)

    scheduled_manifest = cohort_manifest()
    assert not reviewed_exact_progress_missing(scheduled_manifest, 0)


def test_cleansing_unknown_or_missing_profile_identity_never_falls_back_to_another_profile() -> None:
    utec_id = "50d8779c-54fd-437e-b941-e817e202e60c"
    pacifico_id = "a4fd99a6-d161-4854-bdc8-6b5f1bd8163e"
    worker = CleansingWorker(db_client=SelectAdapter({}, profiles=[
        {"institution_id": utec_id, "pipeline_enabled": True, "exclusion_patterns": ["/utec-only/"]},
        {"institution_id": pacifico_id, "pipeline_enabled": True, "exclusion_patterns": ["/maestrias/"]},
        {"institution_id": "invalid", "pipeline_enabled": True, "exclusion_patterns": ["/foreign-invalid/"]},
    ]))
    worker._get_institution_website = lambda _institution_id: ""
    worker._get_noise_patterns_for_inst = lambda _institution_id: []

    foreign_urls = [
        "https://unknown.example/utec-only/programa",
        "https://unknown.example/maestrias/programa",
        "https://unknown.example/foreign-invalid/programa",
    ]
    assert [worker.is_invalid_course("Programa", "", url, institution_id="a4fd99a6-d161-4854-bdc8-6b5f1bd8163f") for url in foreign_urls] == [None, None, None]
    assert [worker.is_invalid_course("Programa", "", url, institution_id="") for url in foreign_urls] == [None, None, None]

    with pytest.raises(RuntimeError, match="invalid_institution_identity"):
        worker.process_batch([dict(raw_row(), institution_id=None)])
    with pytest.raises(RuntimeError, match="invalid_institution_identity"):
        worker.process_batch([dict(raw_row(), institution_id="not-a-uuid")])
    with pytest.raises(RuntimeError, match="missing_institution_site_profile"):
        worker.process_batch([dict(raw_row(), institution_id="00000000-0000-0000-0000-000000000003")])


def test_duplicate_cleansing_profiles_for_an_institution_fail_closed() -> None:
    profiles = [
        {"institution_id": INSTITUTION_ID, "pipeline_enabled": True, "exclusion_patterns": []},
        {"institution_id": INSTITUTION_ID.upper(), "pipeline_enabled": True, "exclusion_patterns": ["/foreign/"]},
    ]
    with pytest.raises(RuntimeError, match="duplicate_institution_site_profile"):
        CleansingWorker(db_client=SelectAdapter({}, profiles=profiles))


def test_cleansing_rejects_same_normalized_url_owned_by_multiple_institutions() -> None:
    profiles = [
        {"institution_id": INSTITUTION_ID, "pipeline_enabled": True, "exclusion_patterns": []},
        {"institution_id": "00000000-0000-0000-0000-000000000002", "pipeline_enabled": True, "exclusion_patterns": []},
    ]
    worker = CleansingWorker(db_client=SelectAdapter({}, profiles=profiles))
    with pytest.raises(RuntimeError, match="cross_institution_url_collision"):
        worker.process_batch([
            raw_row(),
            dict(raw_row(), id="40000000-0000-0000-0000-000000000002", institution_id="00000000-0000-0000-0000-000000000002"),
        ])


def test_reviewed_exact_requires_real_progress_but_schedule_and_recovery_noops_remain_valid() -> None:
    manifest = cohort_manifest()
    manifest.payload["approved_lot_selection"] = "reviewed_exact"
    assert reviewed_exact_progress_missing(manifest, 0)
    assert not reviewed_exact_progress_missing(manifest, 1)

    manifest.payload["approved_lot_selection"] = "rotation_prefix"
    assert not reviewed_exact_progress_missing(manifest, 0)

    manifest.payload["approved_lot_selection"] = "reviewed_exact"
    manifest.payload["recovery_source"] = {"mode": "enrichment_sync_only"}
    assert not reviewed_exact_progress_missing(manifest, 0)

    empty_payload = dict(manifest.payload)
    empty_payload.pop("recovery_source", None)
    empty_payload["entries"] = []
    empty_payload["approved_lot_selection"] = "rotation_prefix"
    empty_manifest = FG2CohortManifest.from_payload(empty_payload, allow_empty=True)
    assert not reviewed_exact_progress_missing(empty_manifest, 0)


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_cleansing_reads_only_manifest_staging_ids_and_rejects_queue_leak(result: str) -> None:
    manifest = cohort_manifest(result)
    database = SelectAdapter({"staging_raw": [raw_row()]})
    worker = CleansingWorker(db_client=database)
    rows = list(worker.stream_pending_staging(cohort_manifest=manifest))
    assert [row["id"] for row in rows] == [RAW_ID]
    assert database.calls == [("staging_raw", f"id=in.({RAW_ID})")]

    database.responses["staging_raw"].append(
        dict(raw_row(), id="40000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        list(worker.stream_pending_staging(cohort_manifest=manifest))


def test_empty_schedule_manifest_never_falls_back_to_global_worker_queues() -> None:
    payload = dict(cohort_manifest().payload)
    payload["entries"] = []
    manifest = FG2CohortManifest.from_payload(payload, allow_empty=True)
    database = SelectAdapter(
        {
            "staging_raw": [raw_row()],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
        }
    )
    cleansing = CleansingWorker(db_client=database)
    enrichment = EnrichmentWorker.__new__(EnrichmentWorker)
    enrichment.db = database
    enrichment.ready_inst_ids = {INSTITUTION_ID}
    sync = SyncVectorWorker.__new__(SyncVectorWorker)
    sync.db = database
    sync.ready_inst_ids = {INSTITUTION_ID}

    assert list(cleansing.stream_pending_staging(cohort_manifest=manifest)) == []
    assert enrichment.get_pending_cleansed(cohort_manifest=manifest) == []
    assert sync.get_pending_enriched(cohort_manifest=manifest) == []
    assert database.calls == []
    assert database.writes == []


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_enrichment_reads_only_cleansed_children_of_manifest_raw_ids(result: str) -> None:
    manifest = cohort_manifest(result)
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed]})
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    expected_cleansed = dict(
        cleansed,
        _fg2_expected_url_sha256=url_sha256(URL),
        _fg2_expected_raw_url_sha256=url_sha256(URL),
        _fg2_manifest_staging_id=RAW_ID,
        _fg2_manifest_content_sha256=CONTENT_SHA,
    )
    assert worker.get_pending_cleansed(cohort_manifest=manifest) == [expected_cleansed]
    assert database.calls == [
        ("cleansed_programs", f"status=eq.pending&staging_id=in.({RAW_ID})")
    ]

    database.responses["cleansed_programs"].append(
        dict(cleansed, id="50000000-0000-0000-0000-000000000099", staging_id="40000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        worker.get_pending_cleansed(cohort_manifest=manifest)


def test_enrichment_rejects_url_substitution_after_selection_before_provider_or_write() -> None:
    manifest = cohort_manifest()
    changed_url = "https://synthetic.example/program/substituted"
    row = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter(
        {
            "cleansed_programs": [row],
            "staging_raw": [
                {
                    "id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "processed",
                    "content_hash": CONTENT_SHA,
                }
            ],
        }
    )
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_cleansed(cohort_manifest=manifest)
    assert len(selected) == 1
    database.responses["cleansed_programs"][0]["url"] = changed_url
    database.responses["staging_raw"][0]["url"] = changed_url
    worker._fetch_sr_enrichment_data = lambda *_args: pytest.fail(
        "URL drift must stop before source lookup/provider work"
    )

    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        worker.enrich_record(selected[0])
    assert database.writes == []


@pytest.mark.parametrize("result", ["complete", "partial"])
def test_sync_reads_only_enriched_children_of_manifest_cleansed_ids(result: str) -> None:
    manifest = cohort_manifest(result)
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "enriched",
    }
    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed], "enriched_programs": [enriched]})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}

    assert worker.get_pending_enriched(cohort_manifest=manifest) == [
        dict(
            enriched,
            _fg2_approved_course_id="70000000-0000-0000-0000-000000000001",
            _fg2_expected_url_sha256=url_sha256(URL),
            _fg2_expected_raw_url_sha256=url_sha256(URL),
            _fg2_manifest_staging_id=RAW_ID,
            _fg2_manifest_cleansed_id=CLEANSED_ID,
            _fg2_manifest_content_sha256=CONTENT_SHA,
        )
    ]
    assert database.calls == [
        ("cleansed_programs", f"staging_id=in.({RAW_ID})"),
        ("enriched_programs", f"status=eq.pending&cleansed_id=in.({CLEANSED_ID})"),
    ]

    database.responses["enriched_programs"].append(
        dict(enriched, id="60000000-0000-0000-0000-000000000099", cleansed_id="50000000-0000-0000-0000-000000000099")
    )
    with pytest.raises(InvalidControlledRun, match="outside the frozen cohort"):
        worker.get_pending_enriched(cohort_manifest=manifest)


def test_sync_rejects_url_substitution_after_selection_before_course_writer() -> None:
    manifest = cohort_manifest()
    changed_url = "https://synthetic.example/program/substituted"
    database = SelectAdapter(
        {
            "staging_raw": [
                {
                    "id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "processed",
                    "content_hash": CONTENT_SHA,
                }
            ],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "enriched",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                }
            ],
        }
    )
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_enriched(cohort_manifest=manifest)
    assert len(selected) == 1
    database.responses["staging_raw"][0]["url"] = changed_url
    database.responses["cleansed_programs"][0]["url"] = changed_url
    database.responses["enriched_programs"][0]["url"] = changed_url
    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        worker.sync_to_production(selected[0])
    assert database.writes == []


def test_manifest_identity_accepts_cleansing_url_normalization_and_still_checks_raw_url() -> None:
    raw_url = "https://synthetic.example/program/presentacion/"
    cleansed_url = cleanse_course_url(raw_url)
    payload = dict(cohort_manifest().payload)
    payload["entries"] = [
        dict(
            payload["entries"][0],
            url_sha256=url_sha256(raw_url),
            cleansed_url_sha256=cleansed_url_sha256(raw_url),
        )
    ]
    manifest = FG2CohortManifest.from_payload(payload)
    raw = dict(raw_row(), url=raw_url, status="processed")
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": cleansed_url,
        "status": "pending",
    }
    database = SelectAdapter({"cleansed_programs": [cleansed], "staging_raw": [raw]})
    enrichment = EnrichmentWorker.__new__(EnrichmentWorker)
    enrichment.db = database
    enrichment.ready_inst_ids = {INSTITUTION_ID}

    selected_cleansed = enrichment.get_pending_cleansed(cohort_manifest=manifest)
    assert selected_cleansed[0]["url"] == cleansed_url
    enrichment._verify_fg2_manifest_url_identity(selected_cleansed[0])

    enriched = {
        "id": ENRICHED_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "url": cleansed_url,
        "status": "pending",
    }
    database.responses["cleansed_programs"][0]["status"] = "enriched"
    database.responses["enriched_programs"] = [enriched]
    sync = SyncVectorWorker.__new__(SyncVectorWorker)
    sync.db = database
    sync.ready_inst_ids = {INSTITUTION_ID}

    selected_enriched = sync.get_pending_enriched(cohort_manifest=manifest)
    assert selected_enriched[0]["url"] == cleansed_url
    sync._verify_fg2_manifest_url_identity(selected_enriched[0])

    database.responses["staging_raw"][0]["url"] = "https://synthetic.example/changed/"
    with pytest.raises(InvalidControlledRun, match="URL identity changed"):
        enrichment._verify_fg2_manifest_url_identity(selected_cleansed[0])


def test_controlled_sync_rejects_mock_enrichment_before_any_write() -> None:
    manifest = cohort_manifest()
    database = SelectAdapter(
        {
            "staging_raw": [dict(raw_row(), status="processed")],
            "cleansed_programs": [
                {
                    "id": CLEANSED_ID,
                    "staging_id": RAW_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "enriched",
                }
            ],
            "enriched_programs": [
                {
                    "id": ENRICHED_ID,
                    "cleansed_id": CLEANSED_ID,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                    "status": "pending",
                    "official_name": "Synthetic Program",
                    "is_mock_data": True,
                }
            ],
        }
    )
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.ready_inst_ids = {INSTITUTION_ID}
    selected = worker.get_pending_enriched(cohort_manifest=manifest)

    assert len(selected) == 1
    assert worker.sync_to_production(selected[0]) is False
    assert database.writes == []


def test_sync_rejects_unbounded_mock_enrichment_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "mock",
            "is_mock_data": True,
        }
    ) is False
    assert database.writes == []


def test_sync_rejects_mock_provider_label_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "smart-mock",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_sync_rejects_unbounded_unknown_provider_without_provider_flag(monkeypatch) -> None:
    monkeypatch.delenv("FG2_REQUIRE_REAL_PROVIDER", raising=False)
    monkeypatch.delattr(SyncVectorWorker, "_fg2_fixture_provider_allowed", raising=False)
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "fixture-provider",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_production_sync_rejects_mock_provider_even_when_flag_claims_real(monkeypatch) -> None:
    monkeypatch.setenv("FG2_REQUIRE_REAL_PROVIDER", "true")
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "mock",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_production_sync_rejects_unknown_provider_provenance_before_any_write(monkeypatch) -> None:
    monkeypatch.setenv("FG2_REQUIRE_REAL_PROVIDER", "true")
    database = SelectAdapter({})
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database

    assert worker.sync_to_production(
        {
            "id": ENRICHED_ID,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "status": "pending",
            "provider_used": "fixture-provider",
            "is_mock_data": False,
        }
    ) is False
    assert database.writes == []


def test_sync_provenance_allowlist_accepts_openai_identity() -> None:
    from scripts.core.sync_vector_worker import REAL_ENRICHMENT_PROVIDERS

    assert "openai" in REAL_ENRICHMENT_PROVIDERS


def test_enrichment_persists_openai_provider_identity_without_mock_provenance(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    enriched = {
        "official_name": "Synthetic OpenAI course",
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
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(enriched), "OpenAI")
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    assert worker.enrich_record({
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "clean_name": "Synthetic OpenAI course",
        "clean_description": "Synthetic public course fixture",
    }) is True

    function, params = worker.db.writes[0]
    assert function == "atomic_enrichment_promote"
    assert params["p_enriched_data"][0]["provider_used"] == "OpenAI"
    assert params["p_enriched_data"][0]["is_mock_data"] is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Remoto", "Remoto"),
        ("online", "Remoto"),
        ("Presencial", "Presencial"),
        ("Híbrido", "Híbrido"),
        ("hibrida", "Híbrido"),
        ("Semipresencial", "Híbrido"),
        (None, None),
        ("", None),
        ("No especificado", None),
        ("Presencial o remoto", None),
    ],
)
def test_fg2_modality_normalization_is_strict_and_rejects_ambiguity(value, expected) -> None:
    from scripts.shared.utils import normalize_course_modality

    assert normalize_course_modality(value) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Modalidad: Remoto", "Remoto"),
        ("Clases presenciales", "Presencial"),
        ("Modalidad híbrida", "Híbrido"),
        ("Sin información de modalidad", None),
        ("Clases presenciales o virtuales", None),
    ],
)
def test_cleansing_detects_only_explicit_unambiguous_modality(text, expected) -> None:
    from scripts.shared.utils import detect_course_modality

    assert detect_course_modality(text) == expected


@pytest.mark.parametrize(
    ("provider_value", "cleaned_value", "expected", "source"),
    [
        ("Remoto", "Presencial", "Remoto", "provider"),
        (None, "Presencial", "Presencial", "cleansed_programs"),
        ("Campus", "Híbrido", "Híbrido", "cleansed_programs"),
        (None, None, None, "unavailable"),
        ("No especificado", "No especificado", None, "unavailable"),
    ],
)
def test_enrichment_modality_selection_preserves_provider_or_uses_bound_cleansing(
    monkeypatch, provider_value, cleaned_value, expected, source
) -> None:
    from scripts.core import enrichment_worker

    raw = {**raw_row(), "status": "processed"}
    marker = {
        "version": 1,
        "source": "cleansing_text",
        "value": cleaned_value,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "source_url_sha256": url_sha256(URL),
        "cleansed_url_sha256": url_sha256(URL),
        "source_content_sha256": CONTENT_SHA,
    }
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "clean_name": "Synthetic course",
        "clean_description": "synthetic",
        "modality": cleaned_value,
        "metadata": {"modality_evidence": marker} if cleaned_value else {},
    }

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_pipeline_raise(self, table, **_kwargs):
            if table == "cleansed_programs":
                return [{**cleansed, "clean_name": "Synthetic course", "clean_description": "synthetic"}]
            if table == "staging_raw":
                return [raw]
            return []

        def select_service_raise(self, _table, **_kwargs):
            return []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    provider_result = {
        "official_name": "Synthetic course",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": None,
        "requirements": [],
        "graduate_profile": None,
        "target_audience": None,
        "objectives": None,
        "benefits": None,
        "certification": None,
        "curriculum_summary": {"pilares": []},
        "modality": provider_value,
        "primary_campus": None,
        "degree_type": "Curso",
        "start_date": None,
        "categories": ["Data"],
        "difficulty_level": None,
        "ai_summary": None,
    }
    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    provider_pre_extracted = []
    worker._fetch_sr_enrichment_data = lambda *_args: (
        {}, {}, {"mode": "Híbrido", "modality": "Híbrido", "category_hint": "Data"}
    )
    def call_provider(*_args, **kwargs):
        provider_pre_extracted.append(kwargs.get("pre_extracted"))
        return dict(provider_result), "OpenAI"

    worker._call_llm_for_pillars = call_provider
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    assert worker.enrich_record(cleansed) is True
    data = worker.db.writes[0][1]["p_enriched_data"][0]
    assert data["modality"] == expected
    assert data["metadata"]["field_provenance"]["modality"]["source"] == source
    assert data["is_mock_data"] is False
    assert provider_pre_extracted == [{"category_hint": "Data"}]


def test_enrichment_does_not_use_profile_mode_defaults_as_modality_evidence() -> None:
    from scripts.core.enrichment_worker import EnrichmentWorker

    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    profile = {
        "field_defaults": {"mode": "Presencial", "duration_months": 12},
        "url_type_rules": [{"pattern": "/curso/", "defaults": {"modality": "Remoto"}}],
    }

    config = worker._effective_extraction_config(profile, "https://example.test/curso/demo")

    assert "mode" not in config["field_defaults"]
    assert "modality" not in config["field_defaults"]
    assert "duration_months" in config["field_defaults"]


def test_enrichment_does_not_reuse_cleansing_modality_across_wrong_identity(monkeypatch) -> None:
    from scripts.core import enrichment_worker

    raw = raw_row()
    marker = {
        "version": 1,
        "source": "cleansing_text",
        "value": "Presencial",
        "staging_id": RAW_ID,
        "institution_id": "00000000-0000-0000-0000-000000000099",
        "source_url_sha256": url_sha256(URL),
        "cleansed_url_sha256": url_sha256(URL),
        "source_content_sha256": CONTENT_SHA,
    }
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "modality": "Presencial",
        "clean_name": "Synthetic course",
        "clean_description": "synthetic",
        "metadata": {"modality_evidence": marker},
    }

    class FixtureDB:
        writes = []

        def select_pipeline_raise(self, table, **_kwargs):
            return [{**cleansed, "clean_name": "Synthetic course", "clean_description": "synthetic"}] if table == "cleansed_programs" else [raw]

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (
        {"modality": None}, "OpenAI"
    )
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    with pytest.raises(InvalidControlledRun, match="modality provenance"):
        worker.enrich_record(cleansed)
    assert worker.db.writes == []


def test_scheduled_legacy_modality_without_evidence_stays_unverified(monkeypatch) -> None:
    """A scheduled cohort URL hash is not provenance for a legacy mode value."""
    from scripts.core import enrichment_worker

    raw = {**raw_row(), "status": "processed"}
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "clean_name": "Synthetic scheduled course",
        "clean_description": "synthetic",
        "modality": "Presencial",
        "metadata": {},
    }

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_all_pipeline(self, table, **_kwargs):
            assert table == "cleansed_programs"
            return [dict(cleansed)]

        def select_pipeline_raise(self, table, **_kwargs):
            if table == "cleansed_programs":
                return [dict(cleansed)]
            if table == "staging_raw":
                return [dict(raw)]
            return []

        def select_service_raise(self, _table, **_kwargs):
            return []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.ready_inst_ids = {INSTITUTION_ID}
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (
        {"official_name": "Synthetic scheduled course", "modality": None, "categories": []},
        "OpenAI",
    )
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    scheduled_row = worker.get_pending_cleansed(cohort_manifest=cohort_manifest())
    assert len(scheduled_row) == 1
    assert scheduled_row[0]["_fg2_expected_url_sha256"] == url_sha256(URL)
    assert "_fg2_authorized_modality_snapshot" not in scheduled_row[0]

    assert worker.enrich_record(scheduled_row[0]) is True
    data = worker.db.writes[0][1]["p_enriched_data"][0]
    modality_provenance = data["metadata"]["field_provenance"]["modality"]
    assert data["modality"] is None
    # The SQL RPC sets the pending row state; this RPC-input test asserts the
    # NULL value/provenance that Sync consumes.
    assert modality_provenance["source"] == "unverified_cleansing_source"
    assert modality_provenance["value"] is None
    assert modality_provenance["evidence"] is None


@pytest.mark.parametrize("drift_field", ["institution_id", "url"])
def test_recovery_rejects_course_identity_drift_even_with_valid_provider_modality(
    monkeypatch, drift_field
) -> None:
    """Recovery must recheck the approved course binding before any write."""
    from scripts.core import enrichment_worker

    raw = {**raw_row(), "status": "processed"}
    course_id = "70000000-0000-0000-0000-000000000001"
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "clean_name": "Synthetic recovery course",
        "clean_description": "synthetic",
        "modality": None,
        "metadata": {},
        "_fg2_expected_url_sha256": url_sha256(URL),
        "_fg2_expected_raw_url_sha256": url_sha256(URL),
        "_fg2_manifest_staging_id": RAW_ID,
        "_fg2_manifest_content_sha256": CONTENT_SHA,
        "_fg2_manifest_course_id": course_id,
    }

    class FixtureDB:
        def __init__(self):
            self.writes = []
            self.current_course = {
                "id": course_id,
                "institution_id": INSTITUTION_ID,
                "url": URL,
            }

        def select_pipeline_raise(self, table, **_kwargs):
            if table == "cleansed_programs":
                return [dict(cleansed)]
            if table == "staging_raw":
                return [dict(raw)]
            return []

        def select_service_raise(self, table, **_kwargs):
            if table == "courses":
                return [dict(self.current_course)]
            return []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    provider_calls = []

    def provider_returns_valid_modality(*_args, **_kwargs):
        provider_calls.append(True)
        # Simulate identity drift after the initial check/provider call but
        # before the mandatory pre-write revalidation.
        if drift_field == "institution_id":
            worker.db.current_course["institution_id"] = (
                "80000000-0000-0000-0000-000000000002"
            )
        else:
            worker.db.current_course["url"] = f"{URL}/different-course"
        return (
            {"official_name": "Synthetic recovery course", "modality": "Presencial", "categories": []},
            "OpenAI",
        )

    worker._call_llm_for_pillars = provider_returns_valid_modality
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    with pytest.raises(InvalidControlledRun, match="identity changed before write"):
        worker.enrich_record(dict(cleansed))
    assert provider_calls == [True]
    assert worker.db.writes == []


@pytest.mark.parametrize("selected_source", ["canonical_url", "effective_url", "url"])
@pytest.mark.parametrize(
    "drift_field", [None, "canonical_url", "effective_url", "url", "content_hash", "institution_id"]
)
def test_enrichment_modality_revalidates_current_cleansing_identity(selected_source, drift_field):
    from scripts.shared.utils import normalize_url

    raw = {
        **raw_row(),
        "status": "processed",
        "canonical_url": "https://canonical.synthetic.example/program/final/"
        if selected_source == "canonical_url" else None,
        "effective_url": "https://redirect.synthetic.example/program/effective/"
        if selected_source != "url" else None,
    }
    selected_url = normalize_url(raw.get("canonical_url") or raw.get("effective_url") or raw["url"])
    evidence = {
        "version": 1,
        "source": "cleansing_text",
        "value": "Presencial",
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "source_url_sha256": url_sha256(raw["url"]),
        "cleansed_url_sha256": url_sha256(selected_url),
        "source_content_sha256": CONTENT_SHA,
    }
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": selected_url,
        "status": "pending",
        "modality": "Presencial",
        "metadata": {"modality_evidence": evidence},
    }
    if drift_field:
        raw[drift_field] = {
            "canonical_url": "https://foreign.synthetic.example/program/changed",
            "effective_url": "https://redirect.synthetic.example/program/changed",
            "url": "https://synthetic.example/program/changed-original",
            "content_hash": "d" * 64,
            "institution_id": "00000000-0000-0000-0000-000000000099",
        }[drift_field]

    class FixtureDB:
        def select_pipeline_raise(self, table, **kwargs):
            row = cleansed if table == "cleansed_programs" else raw
            return [{key: row.get(key) for key in kwargs["columns"].split(",")}]

    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = FixtureDB()
    # A changed effective URL is irrelevant when a canonical URL still wins.
    should_reject = drift_field is not None and not (
        drift_field == "effective_url" and selected_source == "canonical_url"
    )
    if should_reject:
        with pytest.raises(InvalidControlledRun, match="provenance changed before write"):
            worker._resolve_modality(cleansed, None)
    else:
        assert worker._resolve_modality(cleansed, None) == (
            "Presencial", "cleansed_programs", evidence
        )


def test_enrichment_uses_reviewed_approved_lot_modality_snapshot_for_legacy_row(monkeypatch) -> None:
    from scripts.core import enrichment_worker
    from scripts.shared.utils import course_modality_sha256

    raw = {**raw_row(), "status": "processed"}
    course_id = "70000000-0000-0000-0000-000000000001"
    approved_lot_reference = "synthetic-approved-lot"
    approved_lot_sha256 = "a" * 64
    authorized_snapshot = {
        "version": 1,
        "authorization_basis": "approved_lot_exact_digest",
        "approved_lot_reference": approved_lot_reference,
        "approved_lot_sha256": approved_lot_sha256,
        "course_id": course_id,
        "staging_id": RAW_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "cleansed_url_sha256": url_sha256(URL),
        "value": "Online",
        "value_sha256": course_modality_sha256("Online"),
    }
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "clean_name": "Synthetic course",
        "clean_description": "synthetic",
        "modality": "Online",
        "metadata": {},
        "_fg2_expected_url_sha256": url_sha256(URL),
        "_fg2_expected_raw_url_sha256": url_sha256(URL),
        "_fg2_manifest_staging_id": RAW_ID,
        "_fg2_manifest_content_sha256": CONTENT_SHA,
        "_fg2_expected_cleansed_modality_sha256": course_modality_sha256("Online"),
        "_fg2_manifest_course_id": course_id,
        "_fg2_expected_approved_lot_reference": approved_lot_reference,
        "_fg2_expected_approved_lot_sha256": approved_lot_sha256,
        "_fg2_authorized_modality_snapshot": authorized_snapshot,
    }

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_pipeline_raise(self, table, **_kwargs):
            if table == "cleansed_programs":
                return [cleansed]
            if table == "staging_raw":
                return [raw]
            return []

        def select_service_raise(self, table, **_kwargs):
            if table == "courses":
                return [{
                    "id": course_id,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                }]
            return []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    provider_result = {
        "official_name": "Synthetic course",
        "duration_text": "6 meses",
        "duration_months": 6,
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
        "degree_type": "Curso",
        "start_date": None,
        "categories": ["Data"],
        "difficulty_level": None,
        "ai_summary": None,
    }
    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (dict(provider_result), "OpenAI")
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    worker._ensure_canary_enriched_metadata = lambda *_args: None
    worker._verify_canary_enriched_row = lambda *_args: None
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    assert worker.enrich_record(cleansed) is True
    data = worker.db.writes[0][1]["p_enriched_data"][0]
    provenance = data["metadata"]["field_provenance"]["modality"]
    assert data["modality"] == "Remoto"
    assert provenance["source"] == "cleansed_programs"
    assert provenance["evidence"]["source"] == "approved_lot_snapshot"
    assert provenance["evidence"]["authorization_basis"] == "approved_lot_exact_digest"
    assert provenance["evidence"]["approved_lot_sha256"] == approved_lot_sha256
    assert provenance["evidence"]["cleansed_modality_sha256"] == course_modality_sha256("Online")


def test_enrichment_rejects_cleansed_modality_drift_from_recovery_lot(monkeypatch) -> None:
    from scripts.core import enrichment_worker
    from scripts.shared.utils import course_modality_sha256

    raw = {**raw_row(), "status": "processed"}
    course_id = "70000000-0000-0000-0000-000000000001"
    approved_lot_reference = "synthetic-approved-lot"
    approved_lot_sha256 = "a" * 64
    authorized_snapshot = {
        "version": 1,
        "authorization_basis": "approved_lot_exact_digest",
        "approved_lot_reference": approved_lot_reference,
        "approved_lot_sha256": approved_lot_sha256,
        "course_id": course_id,
        "staging_id": RAW_ID,
        "cleansed_id": CLEANSED_ID,
        "institution_id": INSTITUTION_ID,
        "cleansed_url_sha256": url_sha256(URL),
        "value": "Remoto",
        "value_sha256": course_modality_sha256("Remoto"),
    }
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "clean_name": "Synthetic course",
        "clean_description": "synthetic",
        "modality": "Remoto",
        "metadata": {},
        "_fg2_expected_url_sha256": url_sha256(URL),
        "_fg2_expected_raw_url_sha256": url_sha256(URL),
        "_fg2_manifest_staging_id": RAW_ID,
        "_fg2_manifest_content_sha256": CONTENT_SHA,
        "_fg2_expected_cleansed_modality_sha256": course_modality_sha256("Remoto"),
        "_fg2_manifest_course_id": course_id,
        "_fg2_expected_approved_lot_reference": approved_lot_reference,
        "_fg2_expected_approved_lot_sha256": approved_lot_sha256,
        "_fg2_authorized_modality_snapshot": authorized_snapshot,
    }

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_pipeline_raise(self, table, **_kwargs):
            if table == "cleansed_programs":
                return [{**cleansed, "modality": "Presencial"}]
            return [raw]

        def select_service_raise(self, table, **_kwargs):
            if table == "courses":
                return [{
                    "id": course_id,
                    "institution_id": INSTITUTION_ID,
                    "url": URL,
                }]
            return []

        def rpc_raise(self, function, params):
            self.writes.append((function, params))
            return [{"success": True}]

    worker = enrichment_worker.EnrichmentWorker.__new__(enrichment_worker.EnrichmentWorker)
    worker.db = FixtureDB()
    worker.profiles = []
    worker.require_real_provider = True
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    worker._call_llm_for_pillars = lambda *_args, **_kwargs: (
        {"official_name": "Synthetic course", "modality": None, "categories": []},
        "OpenAI",
    )
    worker._merge_pre_extracted = lambda result, _pre_extracted: result
    monkeypatch.setattr(enrichment_worker, "_mark_canary_metadata", lambda metadata: metadata)

    with pytest.raises(InvalidControlledRun, match="identity changed before write"):
        worker.enrich_record(cleansed)
    assert worker.db.writes == []


def test_enrichment_rejects_authorized_modality_snapshot_for_foreign_identity() -> None:
    from scripts.core import enrichment_worker
    from scripts.shared.utils import course_modality_sha256

    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    cleansed = {
        "id": CLEANSED_ID,
        "staging_id": RAW_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "modality": "Presencial",
        "metadata": {},
        "_fg2_expected_url_sha256": url_sha256(URL),
        "_fg2_manifest_staging_id": RAW_ID,
        "_fg2_manifest_course_id": "70000000-0000-0000-0000-000000000001",
        "_fg2_expected_approved_lot_reference": "synthetic-approved-lot",
        "_fg2_expected_approved_lot_sha256": "a" * 64,
        "_fg2_expected_cleansed_modality_sha256": course_modality_sha256("Presencial"),
        "_fg2_authorized_modality_snapshot": {
            "version": 1,
            "authorization_basis": "approved_lot_exact_digest",
            "approved_lot_reference": "synthetic-approved-lot",
            "approved_lot_sha256": "a" * 64,
            "course_id": "70000000-0000-0000-0000-000000000099",
            "staging_id": RAW_ID,
            "cleansed_id": CLEANSED_ID,
            "institution_id": INSTITUTION_ID,
            "cleansed_url_sha256": url_sha256(URL),
            "value": "Presencial",
            "value_sha256": course_modality_sha256("Presencial"),
        },
    }

    with pytest.raises(InvalidControlledRun, match="authorized modality snapshot"):
        worker._resolve_modality(cleansed, None)


def test_sync_accepts_openai_provenance_and_preserves_nonpublic_new_course(monkeypatch) -> None:
    from scripts.core import sync_vector_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_service_raise(self, table, **_kwargs):
            return []

        def select_all_service(self, _table, **_kwargs):
            return []

        def upsert(self, table, data, **_kwargs):
            self.writes.append(("upsert", table, dict(data)))
            return [{"id": "70000000-0000-0000-0000-000000000001", "url": data["url"], **data}]

        def rpc_raise(self, function, params):
            self.writes.append(("rpc", function, params))
            return [{"success": True}]

        def patch_exact_one_raise(self, table, filters, data, expected_id):
            self.writes.append(("patch", table, dict(data)))
            return {"id": expected_id, **data}

    database = FixtureDB()
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.profiles = [{
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": False,
        "noise_patterns": [],
        "field_defaults": {"mode": "Presencial"},
    }]
    worker.ready_inst_ids = {INSTITUTION_ID}
    worker.default_noise_patterns = []
    worker._fg2_course_inventory = None
    monkeypatch.setattr(sync_vector_worker, "is_safe_public_url", lambda _url: True)

    assert worker.sync_to_production({
        "id": ENRICHED_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "official_name": "Synthetic OpenAI course",
        "provider_used": "OpenAI",
        "is_mock_data": False,
        "degree_type": "Curso",
        "duration_months": 6,
        "categories": ["Data"],
    }) is True

    course_write = next(payload for operation, table, payload in database.writes if operation == "upsert" and table == "courses")
    assert course_write["provider_used"] == "OpenAI"
    assert course_write["is_mock_data"] is False
    assert course_write["is_active"] is False
    assert course_write["mode"] == "Presencial"  # legacy rows retain configured fallback


@pytest.mark.parametrize("modality_source", ["unavailable", "unverified_cleansing_source", "unrecognized_source"])
def test_sync_keeps_unresolved_modality_pending_despite_profile_defaults(monkeypatch, modality_source) -> None:
    from scripts.core import sync_vector_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def select_service_raise(self, _table, **_kwargs):
            return []

        def select_all_service(self, _table, **_kwargs):
            return []

        def upsert(self, table, data, **_kwargs):
            self.writes.append(("upsert", table, dict(data)))
            return [{"id": "70000000-0000-0000-0000-000000000002", "url": data["url"], **data}]

        def rpc_raise(self, function, params):
            self.writes.append(("rpc", function, params))
            return [{"success": True}]

        def patch_exact_one_raise(self, table, filters, data, expected_id):
            self.writes.append(("patch", table, dict(data)))
            return {"id": expected_id, **data}

    database = FixtureDB()
    worker = SyncVectorWorker.__new__(SyncVectorWorker)
    worker.db = database
    worker.profiles = [{
        "institution_id": INSTITUTION_ID,
        "pipeline_enabled": True,
        "production_enabled": False,
        "noise_patterns": [],
        "field_defaults": {"mode": "Presencial"},
        "section_mode_map": {"/": "Híbrido"},
    }]
    worker.ready_inst_ids = {INSTITUTION_ID}
    worker.default_noise_patterns = []
    worker._fg2_course_inventory = None
    worker._verify_canary_course_marker = lambda _url: None
    monkeypatch.setattr(sync_vector_worker, "is_safe_public_url", lambda _url: True)

    assert worker.sync_to_production({
        "id": ENRICHED_ID,
        "institution_id": INSTITUTION_ID,
        "url": URL,
        "status": "pending",
        "official_name": "Synthetic course",
        "provider_used": "OpenAI",
        "is_mock_data": False,
        "degree_type": "Curso",
        "duration_text": "6 meses",
        "duration_months": 6,
        "categories": ["Data"],
        "modality": None,
        "metadata": {"field_provenance": {"modality": {"source": modality_source, "value": None}}},
    }) is True

    course_write = next(
        payload for operation, table, payload in database.writes
        if operation == "upsert" and table == "courses"
    )
    assert course_write["mode"] is None
    quality_call = next(
        params for operation, function, params in database.writes
        if operation == "rpc" and function == "h2_update_course_quality"
    )
    assert "mode" in quality_call["p_missing_fields"]


def test_controlled_enrichment_rejects_mock_provider_name() -> None:
    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker._mock_only = False
    worker.require_real_provider = True

    class MockNamedProvider:
        @staticmethod
        def call_with_fallback(_prompt, _clean_fn, validate_fn=None):
            return ({"official_name": "Synthetic program"}, "smart-mock")

    worker.orchestrator = MockNamedProvider()

    with pytest.raises(ControlledEnrichmentUnavailable):
        worker._call_llm_for_pillars("Synthetic program", "Synthetic description")


@pytest.mark.parametrize(
    "cloudflare_payload",
    ["{}", "[]", '{"official_name":"X","duration_months":"six"}',
     '{"official_name":"X","unexpected":"field"}'],
)
def test_invalid_provider_schema_aborts_controlled_enrichment_before_writes(
    cloudflare_payload: str,
) -> None:
    import logging

    from scripts.core import enrichment_worker

    class FixtureDB:
        def __init__(self):
            self.writes = []

        def rpc_raise(self, function, _params):
            self.writes.append(function)
            return [{"success": True}]

    worker = EnrichmentWorker.__new__(EnrichmentWorker)
    worker.db = FixtureDB()
    worker.require_real_provider = True
    worker._mock_only = False
    worker.profiles = []
    worker._fetch_sr_enrichment_data = lambda *_args: ({}, {}, {})
    providers = [
        enrichment_worker.LLMProvider("OpenAI", lambda _prompt: "{}", lambda: True),
        enrichment_worker.LLMProvider(
            "Cloudflare", lambda _prompt: cloudflare_payload, lambda: True
        ),
    ]
    worker.orchestrator = enrichment_worker.ProviderOrchestrator(
        providers, logging.getLogger("fg2-invalid-provider-schema-test")
    )
    worker.orchestrator.run_health_checks()

    with pytest.raises(ControlledEnrichmentUnavailable):
        worker.enrich_record({
            "id": CLEANSED_ID,
            "staging_id": None,
            "institution_id": INSTITUTION_ID,
            "url": URL,
            "clean_name": "Synthetic course",
            "clean_description": "Synthetic description",
        })

    assert worker.db.writes == []
