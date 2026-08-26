import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIREMENT_ID = "REQ-EST-001"
CLIENT_SOURCE_ID = "SRC-REQ-002"
CLIENT_SOURCE_DOCX = "SRC-REQ-002-DOCX"
CLIENT_SOURCE_HOME = "SRC-REQ-002-HOME"
CLIENT_SOURCE_RESULTADOS = "SRC-REQ-002-RESULTADOS"
SANITIZED_ATTESTATION_ID = "ADENDA-REQ-EST-001-001"
SANITIZED_ATTESTATION_PATH = ".context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md"
CLOSED_H2_STATE = "MERGED_TO_CERTIFICACION_CI_GREEN"
SOURCE_HASHES = {
    "Studiamatch_MVP_Requerimientos_v5.docx": "3537820F93F3A6880BBA22109C020CEDB4334F1AFD905ACEA70E809C9748B107",
    "studiamatch_home.html": "3E84696C000A9F9875853145C8C2CF227E606A5B5F8527184328629C3B1A135D",
    "studiamatch_resultados.html": "9C2CA7660B412A63B22B355F5345F4C28AFC73477C1DC6E9D04F770AECD1C32C",
}


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def test_closing_rule_requires_client_source_validation() -> None:
    agents = read("AGENTS.md")
    state = read(".context/estado_del_proyecto.md")
    plan = read(".context/operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md")

    required_terms = [
        "documento privado del cliente",
        "atestacion sanitizada versionada",
        "El documento privado no se versiona",
        "criterios de aceptacion",
        "antes de iniciar",
        "cualquier nuevo desarrollo con requerimiento cliente",
    ]

    for term in required_terms:
        assert term in agents
        assert term in state

    assert "fuente privada cliente" in plan
    assert "documento privado no se versiona" in plan
    assert "no se ejecuta el hito siguiente" in plan
    assert "cualquier nuevo desarrollo con requerimiento cliente" in plan


def test_client_source_gate_is_generic_for_new_client_development() -> None:
    agents = read("AGENTS.md")
    state = read(".context/estado_del_proyecto.md")
    plan = read(".context/operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md")

    for text in [agents, state, plan]:
        assert "cualquier nuevo desarrollo con requerimiento cliente" in text
        assert "antes de iniciar" in text
        assert "al cerrar" in text
        assert "atestacion sanitizada versionada" in text
        assert "no se versiona" in text


def test_required_pillars_include_functionality_for_critical_changes() -> None:
    agents = read("AGENTS.md")
    state = read(".context/estado_del_proyecto.md")
    pr_template = read(".github/pull_request_template.md")

    for text in [agents, state]:
        assert "funcionalidad" in text.lower()
        assert "escalabilidad" in text.lower()
        assert "seguridad" in text.lower()
        assert "mantenimiento" in text.lower()
        assert "calidad" in text.lower()
        assert "rendimiento" in text.lower()

    assert "| Funcionalidad | `PENDIENTE/APROBADO` |" in pr_template


def test_h2_closed_evidence_validates_against_sanitized_client_attestation() -> None:
    attestation = read(SANITIZED_ATTESTATION_PATH)
    evidence = read(".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md")
    hito = read(".context/hitos/hito_002.md")
    task = read(".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md")
    matrix = read(".context/matrices/matriz_hito_002.md")

    assert SANITIZED_ATTESTATION_ID in attestation
    assert CLIENT_SOURCE_ID in attestation
    assert CLIENT_SOURCE_DOCX in attestation
    assert CLIENT_SOURCE_HOME in attestation
    assert CLIENT_SOURCE_RESULTADOS in attestation
    assert REQUIREMENT_ID in attestation
    assert "CA2 completo y CA3" in attestation
    assert "schema editorial/calidad" in attestation
    assert "pipeline tolerante a datos parciales" in attestation
    assert "marcado pendiente/completo" in attestation

    for text in [evidence, hito, task, matrix]:
        assert CLOSED_H2_STATE in text
        assert CLIENT_SOURCE_ID in text
        assert SANITIZED_ATTESTATION_ID in text

    assert "PASS_CLIENT_SOURCE_ATTESTED" in matrix
    assert "La fuente privada no se versiona" in evidence


def test_sanitized_client_attestation_records_private_source_inventory() -> None:
    attestation = read(SANITIZED_ATTESTATION_PATH)

    assert "Inventario Sanitizado De Fuente Cliente" in attestation
    assert "Criterios De Aceptacion Sprint 1 Sanitizados" in attestation
    assert "Reglas Sanitizadas De Mockups Oficiales" in attestation
    assert "No se copian, no se versionan y no se exponen en PRs" in attestation

    for artifact, source_hash in SOURCE_HASHES.items():
        assert artifact in attestation
        assert source_hash in attestation


def test_private_source_files_match_sanitized_attestation_when_available() -> None:
    source_dir = os.environ.get("STUDIAMATCH_PRIVATE_SOURCE_DIR")
    if not source_dir:
        return

    base = Path(source_dir)
    assert base.exists(), f"private source directory does not exist: {base}"

    for artifact, expected_hash in SOURCE_HASHES.items():
        path = base / artifact
        assert path.exists(), f"missing private source artifact: {artifact}"
        assert sha256_file(path) == expected_hash


def test_sanitized_client_attestation_maps_all_sprint_1_acceptance_criteria() -> None:
    attestation = read(SANITIZED_ATTESTATION_PATH)

    for index in range(1, 14):
        assert f"`CA{index}`" in attestation

    assert "`CA2` | Cambios Supabase" in attestation
    assert "estado editorial/calidad" in attestation
    assert "fuentes por campo" in attestation
    assert "timestamps" in attestation
    assert "fecha de inicio" in attestation
    assert "base de leads/patrocinio" in attestation
    assert "`CA3` | Deteccion de campos vacios" in attestation
    assert "registros incompletos marcados pendientes" in attestation
    assert "sin detener pipeline" in attestation
    assert "`HITO-002` | Implementado y promovido a `certificacion`" in attestation


def test_next_hito_pre_start_gate_is_backed_by_client_source_mapping() -> None:
    attestation = read(SANITIZED_ATTESTATION_PATH)
    plan = read(".context/operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md")
    backlog_index = read(".context/backlog_tareas/req_est_001_sprint_1/_index.md")
    state = read(".context/estado_del_proyecto.md")

    hito3 = read(".context/hitos/hito_003.md")
    task3 = read(".context/backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md")
    matrix3 = read(".context/matrices/matriz_hito_003.md")
    evidence3 = read(".context/evidencias_cliente/sprint_1/evidencia_hito_003.md")

    assert "H2_CERTIFICATION_QA_READ_ONLY_PASSED" in state
    assert "| H3 | Administracion editorial autenticada | CA4 | H2 aceptado |" in plan
    assert "| [HITO-003](../../hitos/hito_003.md) | `H3-CA4` | Panel admin despues de H2 aceptado. |" in backlog_index
    assert "`CA4` | Panel `/admin`" in attestation
    assert "cola de pendientes" in attestation
    assert "edicion manual" in attestation
    assert "publicacion" in attestation
    assert CLIENT_SOURCE_ID in attestation
    assert SANITIZED_ATTESTATION_ID in attestation

    for text in [hito3, task3, matrix3, evidence3]:
        assert "PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION" in text
        assert "H3-CA4" in text
        assert CLIENT_SOURCE_ID in text
        assert SANITIZED_ATTESTATION_ID in text


def test_closed_h2_does_not_expose_private_client_document() -> None:
    evidence = read(".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md")
    hito = read(".context/hitos/hito_002.md")
    matrix = read(".context/matrices/matriz_hito_002.md")

    for text in [evidence, hito, matrix]:
        assert "precio" not in text.lower()
        assert "condiciones de pago" not in text.lower()
        assert "firma" not in text.lower()
        assert "datos bancarios" not in text.lower()
