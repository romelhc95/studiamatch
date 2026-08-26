from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = {
    ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md": {
        "must_include": [
            "# Acta Ejecutiva Canonica Hito 002",
            "Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT`",
            "Veredicto PR: `MERGED_TO_CERTIFICACION_CI_GREEN`",
            "Validacion Contra Fuente Cliente",
            "SRC-REQ-002",
            "ADENDA-REQ-EST-001-001",
            "Grado de evidencia: `A`",
            "H2-CA2",
            "H2-CA3",
            "PASS_IN_DEVELOPMENT",
            "350",
            "131",
            "219",
            "NOOP=350",
            "private_column_count=0",
            "total_columns=28",
            "security_invoker=true",
            "91 passed",
            "h2_pg17_harness_ok",
            "APPROVED_AND_MERGED_TO_CERTIFICACION",
            "MERGED_TO_CERTIFICACION_CI_GREEN",
            "no autoriza Supabase Pro",
        ],
        "client_language": [
            "Resumen Para Cliente",
            "Resultado comprensible",
            "Lectura Para Cliente",
            "programas incompletos",
            "no se publican automaticamente",
        ],
    },
    ".context/matrices/matriz_hito_002.md": {
        "must_include": [
            "Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT`",
            "Veredicto PR: `MERGED_TO_CERTIFICACION_CI_GREEN`",
            "Fuente cliente validada: `SRC-REQ-002` via `ADENDA-REQ-EST-001-001`",
            "Grado de evidencia: `A`",
            "Traduccion para cliente",
            "Modelo editorial separado",
            "Estados editoriales y de calidad",
            "Campos faltantes",
            "Proteccion de datos manuales",
            "Privacidad de superficie publica",
            "Conservacion de incompletos",
            "Idempotencia de backfill",
            "Escalabilidad de lote",
            "Validacion automatizada",
            "PR protegido a desarrollo",
            "Campos privados expuestos | 0",
        ],
        "client_language": [
            "El negocio puede revisar",
            "Se sabe exactamente que dato falta",
            "El publico no ve estados internos",
            "Ningun programa se pierde",
            "La entrega esta respaldada por pruebas repetibles",
        ],
    },
}


def grade_document(text: str, required_terms: list[str], client_terms: list[str]) -> tuple[int, str]:
    checks = required_terms + client_terms
    matched = sum(1 for term in checks if term in text)
    score = round((matched / len(checks)) * 100)
    if score >= 90:
        return score, "A"
    if score >= 80:
        return score, "B"
    if score >= 70:
        return score, "C"
    return score, "F"


def test_h2_client_evidence_documents_reach_grade_a() -> None:
    results = []

    for relative_path, rules in REQUIRED_DOCS.items():
        path = ROOT / relative_path
        assert path.exists(), f"missing canonical H2 evidence document: {relative_path}"
        text = path.read_text(encoding="utf-8")

        score, grade = grade_document(text, rules["must_include"], rules["client_language"])
        results.append(f"{relative_path}: {score}/100 grade {grade}")

        assert grade == "A", "; ".join(results)
        assert "IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT" in text
        assert "MERGED_TO_CERTIFICACION_CI_GREEN" in text
        assert "Grado de evidencia: `A`" in text


def test_h2_client_evidence_does_not_overstate_delivery_scope() -> None:
    evidence = (ROOT / ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md").read_text(
        encoding="utf-8"
    )

    assert "No acredita" in evidence and "produccion" in evidence
    assert "no autoriza Supabase Pro" in evidence
    assert "writers" in evidence
    assert "schedules" in evidence


def test_h2_matrix_links_technical_controls_to_client_meaning() -> None:
    matrix = (ROOT / ".context/matrices/matriz_hito_002.md").read_text(encoding="utf-8")

    assert "| Unidad | Control | Estado | Evidencia verificable | Traduccion para cliente |" in matrix
    assert matrix.count("PASS_IN_DEVELOPMENT") >= 15
    assert "H2-CA2" in matrix
    assert "H2-CA3" in matrix


def test_h2_client_evidence_records_merged_pr_state() -> None:
    evidence = (ROOT / ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md").read_text(
        encoding="utf-8"
    )
    matrix = (ROOT / ".context/matrices/matriz_hito_002.md").read_text(encoding="utf-8")

    assert "PR #458" in evidence
    assert "0c9e40f81f2a38141c9c2af170e26ab594b7533d" in evidence
    assert "4f7061585202301760d8068e13edc5c93b0f94e2" in evidence
    assert "0ed6afeec741c698f1111c2ea27357160fa77279" in evidence
    assert "MERGED_TO_CERTIFICACION_CI_GREEN" in evidence
    assert "MERGED_TO_CERTIFICACION_CI_GREEN" in matrix
