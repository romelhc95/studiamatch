from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = {
    ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md": {
        "must_include": [
            "# Acta Ejecutiva Canonica Hito 002",
            "Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT`",
            "Veredicto PR: `GO_TECHNICAL_FOR_PROTECTED_PR`",
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
            "GO tecnico para PR",
            "GO_TECHNICAL_FOR_PROTECTED_PR",
            "no acredita merge",
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
            "Veredicto PR: `GO_TECHNICAL_FOR_PROTECTED_PR`",
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
            "Aprobacion tecnica para PR",
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
        assert "GO_TECHNICAL_FOR_PROTECTED_PR" in text
        assert "Grado de evidencia: `A`" in text


def test_h2_client_evidence_does_not_overstate_delivery_scope() -> None:
    evidence = (ROOT / ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md").read_text(
        encoding="utf-8"
    )

    assert "No acredita merge" in evidence
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
