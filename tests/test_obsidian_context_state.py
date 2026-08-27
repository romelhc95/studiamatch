from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

POST_H2_MERGE_STATE = "H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED"
POST_H2_PHASE_STATE = "H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED"
H2_MERGE_COMMIT = "0c9e40f81f2a38141c9c2af170e26ab594b7533d"
H2_CONTEXT_GATE_COMMIT = "4f7061585202301760d8068e13edc5c93b0f94e2"
H2_CERTIFICATION_MERGE_COMMIT = "0ed6afeec741c698f1111c2ea27357160fa77279"
H2_COMPAT_DEVELOPMENT_MERGE_COMMIT = "e8376035d8d5c3e1b7893cbb1ede14f735ccd05d"
H2_COMPAT_CERTIFICATION_MERGE_COMMIT = "2d499324bb21e750d9bc7c94cb80e7a193062b50"
NEXT_GATE = "PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN"

OBSOLETE_POST_MERGE_TOKENS = [
    "DOCUMENTATION_AUTHORITY_ACTIVE_DB_BLOCKED",
    "PR_DOCUMENTAL_A_DESARROLLO",
    "PR_H2_A_DESARROLLO",
    "FREE_H2_PUBLIC_SURFACE_VALIDATED_PR_READY",
    "GO_TECHNICAL_FOR_PROTECTED_PR",
    "H2_MERGED_TO_DESARROLLO_CI_GREEN",
    "MERGED_TO_DESARROLLO_CI_GREEN",
    "PROMOTE_DESARROLLO_TO_CERTIFICACION_FOR_H2",
    "CERTIFICATION_PROMOTION_PR_REVIEW_AND_DEPLOY_VALIDATION",
]

CANONICAL_DOCS = [
    ".context/estado_del_proyecto.md",
    ".context/hitos/hito_002.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md",
    ".context/matrices/matriz_hito_002.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md",
    ".context/operaciones/h2_production_remediation_plan.md",
    ".context/operaciones/estandar_prompts_retroalimentados.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_obsidian_context_graph_records_h2_post_merge_state() -> None:
    state = read(".context/estado_del_proyecto.md")
    hito = read(".context/hitos/hito_002.md")
    task = read(".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md")
    evidence = read(".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md")
    matrix = read(".context/matrices/matriz_hito_002.md")
    tracking = read(".context/seguimiento/seguimiento_sprint_1_h2_h5.md")

    assert POST_H2_PHASE_STATE in state
    assert f"| `HITO-002` | `{POST_H2_MERGE_STATE}` | `TASK-H2-001` |" in state
    assert f"| Estado | `{POST_H2_MERGE_STATE}` |" in hito
    assert f"| Estado | `{POST_H2_MERGE_STATE}` |" in task
    assert "Estado: `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`" in evidence
    assert "Veredicto PR: `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE`" in evidence
    assert "Veredicto PR: `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE`" in matrix
    assert "GO_AFTER_FREE_MIGRATION" in evidence
    assert "PASS_AFTER_FREE_MIGRATION" in matrix
    assert H2_MERGE_COMMIT in evidence
    assert H2_CONTEXT_GATE_COMMIT in evidence
    assert H2_CERTIFICATION_MERGE_COMMIT in evidence
    assert H2_MERGE_COMMIT in tracking
    assert H2_CONTEXT_GATE_COMMIT in tracking
    assert H2_CERTIFICATION_MERGE_COMMIT in tracking
    assert H2_COMPAT_DEVELOPMENT_MERGE_COMMIT in state
    assert H2_COMPAT_DEVELOPMENT_MERGE_COMMIT in tracking
    assert H2_COMPAT_CERTIFICATION_MERGE_COMMIT in state
    assert H2_COMPAT_CERTIFICATION_MERGE_COMMIT in tracking
    assert NEXT_GATE in state
    assert NEXT_GATE in tracking


def test_obsidian_context_graph_has_no_obsolete_post_h2_states() -> None:
    failures = []

    for relative_path in CANONICAL_DOCS:
        text = read(relative_path)
        for token in OBSOLETE_POST_MERGE_TOKENS:
            if token in text:
                failures.append(f"{relative_path}: obsolete token {token}")

    assert not failures, "; ".join(failures)


def test_obsidian_context_graph_links_are_existing_files() -> None:
    state = read(".context/estado_del_proyecto.md")

    assert "backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md" not in state
    assert (ROOT / ".context/hitos/hito_002.md").exists()
    assert (ROOT / ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md").exists()
    assert (ROOT / ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md").exists()


def test_certification_readonly_qa_is_defined_before_main_promotion() -> None:
    qa = read(".context/operaciones/h2_h3_certification_readonly_qa.md")
    state = read(".context/estado_del_proyecto.md")
    tracking = read(".context/seguimiento/seguimiento_sprint_1_h2_h5.md")

    required_terms = [
        "GO_FOR_MAIN_PROMOTION_PREFLIGHT_ONLY",
        "PASS_CERTIFICATION_READ_ONLY_QA",
        "Funcionalidad publica",
        "Contrato frontend H2",
        "Privacidad H2",
        "Pipeline H2",
        "H3 prearranque",
        "Fuente cliente",
        "Seguridad",
        "GO/NO-GO",
        "promocion `certificacion -> main`",
    ]

    for term in required_terms:
        assert term in qa

    assert "operaciones/h2_h3_certification_readonly_qa.md" in state
    assert "QA read-only H2/H3" in tracking


def test_h2_production_remediation_plan_blocks_main_until_expand() -> None:
    plan = read(".context/operaciones/h2_production_remediation_plan.md")
    state = read(".context/estado_del_proyecto.md")

    required_terms = [
        "NO_GO_FOR_MAIN_UNTIL_PRO_EXPAND_COMPAT_VERIFIED",
        "PLAN_READY_NO_PRO_APPLY_NO_MAIN_PROMOTION",
        "224",
        "expand -> compatibilidad -> deploy -> contract",
        "db_migrate.py",
        "db-sync-to-pro.yml",
        "manifest",
        "backup/PITR",
        "courses_public_effective",
        "Legacy Pro",
        "No degradacion funcional",
    ]

    for term in required_terms:
        assert term in plan

    assert "operaciones/h2_production_remediation_plan.md" in state
    assert "Pro, `main`, writers, schedules" in plan


def test_prompt_retroalimentado_standard_is_authoritative() -> None:
    agents = read("AGENTS.md")
    state = read(".context/estado_del_proyecto.md")
    standard = read(".context/operaciones/estandar_prompts_retroalimentados.md")

    required_terms = [
        "PROMPT_RETROALIMENTADO_REQUIRED",
        "analizar, implementar, validar",
        "JIT, push, PR, merge, deploy",
        "Supabase writes",
        "evidencia canonica",
        "HIGH/CRITICAL",
        "waiver requiere causa",
    ]

    for text in (agents, state, standard):
        for term in required_terms:
            assert term in text

    assert "operaciones/estandar_prompts_retroalimentados.md" in state


def test_pull_request_template_is_authoritative_and_evidence_driven() -> None:
    agents = read("AGENTS.md")
    state = read(".context/estado_del_proyecto.md")
    standard = read(".context/operaciones/estandar_prompts_retroalimentados.md")
    template = read(".github/pull_request_template.md")

    required_authority_terms = [
        ".github/pull_request_template.md",
        "validaciones necesarias",
        "resultados reales",
        "placeholders",
        "riesgo residual",
    ]
    required_template_sections = [
        "## Resumen",
        "## Avances Del Cambio",
        "## Pilares Obligatorios",
        "## Transicion Transparente",
        "## Evidencia Para Cliente",
        "## Validaciones",
        "## Seguridad Y Datos",
        "## Alcance Y Limites",
        "## Checklist Tecnico",
        "Credential scan",
        "Python tests",
        "ESLint",
        "TypeScript",
        "Static build",
        "security-auditor",
    ]

    for text in (agents, state, standard):
        for term in required_authority_terms:
            assert term in text

    for section in required_template_sections:
        assert section in template

    assert "Completar esta tabla solo con resultados realmente ejecutados" in template
