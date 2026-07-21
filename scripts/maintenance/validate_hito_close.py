#!/usr/bin/env python3
"""Mechanical close gate for StudIAMatch milestones.

This script intentionally validates repo artifacts instead of trusting an AI
summary. It is conservative: if docs, git state, workflows, or migrations are
inconsistent, the milestone remains observed until a human or follow-up task
resolves the mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAX_DETAIL_CHARS = 6000


HITO_CONFIG = {
    1: {
        "allowed_staged_exact": {
            ".context/backlog_tareas/_plantilla_tarea.md",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1_orquestacion_fg2_fg3_schema_base_y_seguridad.md",
            ".context/changelog/2026-07-12.md",
            ".context/crear_tarea.py",
            ".context/evidencias/_plantilla_informe_cumplimiento.md",
            ".context/evidencias/hito_1_informe_cumplimiento.md",
            ".context/operaciones/flujo_requerimientos.md",
            ".context/prompts/system_prompt_base.md",
            ".github/pull_request_template.md",
            ".github/workflows/fg1_inventory.yml",
            ".github/workflows/fg3_integrity.yml",
            "db/migrations/20260712_hito1_editorial_quality_contract.sql",
            "scripts/core/master_orchestrator.py",
            "scripts/maintenance/validate_hito_close.py",
            "tests/test_hito_governance.py",
        },
        "allowed_staged_regex": [
            r"^\.context/evidencias/hito_1_qa_gate_report_\d{8}_\d{6}\.md$",
            r"^\.context/evidencias/hito_1_qa_gate_report_\d{8}\.md$",
        ],
        "schema_terms_forbidden": {
            "pdt": "Use the real data_quality_status value 'pendiente', not an alias.",
            "en_revision": "Use the real publication_status value 'pendiente_revision', not an alias.",
        },
        "required_doc_terms": [
            "pendiente_revision",
            "data_quality_status",
            "pendiente",
            "completo",
            "publication_status",
        ],
        "required_staged_exact": {
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1_orquestacion_fg2_fg3_schema_base_y_seguridad.md",
            ".context/changelog/2026-07-12.md",
            ".context/evidencias/hito_1_informe_cumplimiento.md",
        },
        "dml_approvers": {"Usuario/PM", "SDLC-Chief"},
    }
}


class Gate:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def git_lines(args: list[str]) -> list[str]:
    result = run_git(args)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str:
    result = run_git(["show", f":{rel(path)}"])
    if result.returncode != 0:
        raise FileNotFoundError(f"No indexed content for {rel(path)}")
    return result.stdout


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def find_tasks(hito: int) -> list[Path]:
    pattern = re.compile(rf"^\.context/backlog_tareas/(?:[^/]+/)?tarea_.*_hito_{hito}_.*\.md$")
    return [ROOT / path for path in git_lines(["ls-files"]) if pattern.match(path)]


def find_evidence(hito: int) -> Path:
    return ROOT / ".context" / "evidencias" / f"hito_{hito}_informe_cumplimiento.md"


def extract_changelog_blocks(hito: int) -> list[tuple[Path, str]]:
    blocks: list[tuple[Path, str]] = []
    pattern = re.compile(rf"^##+\s+Hito\s+{hito}\b", re.IGNORECASE | re.MULTILINE)
    paths = [ROOT / path for path in git_lines(["ls-files", ".context/changelog/*.md"])]
    for path in paths:
        text = read_text(path)
        match = pattern.search(text)
        if not match:
            continue
        next_heading = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
        end = match.end() + next_heading.start() if next_heading else len(text)
        blocks.append((path, text[match.start() : end]))
    return blocks


def is_tracked(path: Path) -> bool:
    result = run_git(["ls-files", "--error-unmatch", rel(path)])
    return result.returncode == 0


def check_git_state(gate: Gate) -> None:
    diff_check = run_git(["diff", "--cached", "--check", "--", ":(exclude).agents/**"])
    if diff_check.returncode != 0:
        output = (diff_check.stdout + diff_check.stderr).strip()
        if len(output) > MAX_DETAIL_CHARS:
            output = output[:MAX_DETAIL_CHARS] + "\n... output truncated; run git diff --cached --check for full details"
        gate.error("git diff --cached --check failed:\n" + output)

    status = run_git(["status", "--porcelain"])
    relevant_untracked = []
    for line in status.stdout.splitlines():
        if not line.startswith("?? "):
            continue
        path = line[3:]
        if path.startswith(("db/migrations/", ".context/", "scripts/core/", "scripts/maintenance/")):
            relevant_untracked.append(path)
    if relevant_untracked:
        gate.error("Relevant untracked files must be added or removed before close: " + ", ".join(relevant_untracked))

    unstaged = git_lines(["diff", "--name-only"])
    if unstaged:
        gate.error("Tracked files have unstaged changes; stage or revert them before validation: " + ", ".join(unstaged))


def is_allowed_staged_file(path: str, hito: int) -> bool:
    config = HITO_CONFIG.get(hito)
    if not config:
        return False
    if path in config["allowed_staged_exact"]:
        return True
    return any(re.match(pattern, path) for pattern in config["allowed_staged_regex"])


def check_staged_scope(gate: Gate, hito: int) -> None:
    if hito not in HITO_CONFIG:
        gate.error(f"Hito {hito} has no explicit staged scope configuration; refusing to validate open-ended scope.")
        return
    staged = git_lines(["diff", "--cached", "--name-only"])
    if not staged:
        gate.error("No staged files found. Hito closure must validate the exact files intended for commit/PR.")
        return

    out_of_scope = [path for path in staged if not is_allowed_staged_file(path, hito)]
    if out_of_scope:
        gate.error(
            "Staged files outside Hito "
            + str(hito)
            + " scope must be unstaged or moved to a separate commit: "
            + ", ".join(out_of_scope)
        )
    missing_required = sorted(HITO_CONFIG[hito]["required_staged_exact"] - set(staged))
    if missing_required:
        gate.error("Current-close artifacts must be staged: " + ", ".join(missing_required))


def check_required_files(gate: Gate, hito: int, task_paths: list[Path], evidence_path: Path) -> tuple[str, str, Path | None]:
    task_text = ""
    evidence_text = ""
    task_path = task_paths[0] if len(task_paths) == 1 else None
    if not task_paths:
        gate.error(f"No task file found for hito {hito} in .context/backlog_tareas")
    elif len(task_paths) > 1:
        gate.error(f"Multiple task files found for Hito {hito}; configure explicit task aggregation before closing: " + ", ".join(rel(path) for path in task_paths))
    else:
        task_text = read_text(task_path)
    if not is_tracked(evidence_path):
        gate.error(f"Missing evidence report: {rel(evidence_path)}")
    else:
        evidence_text = read_text(evidence_path)
    return task_text, evidence_text, task_path


def check_sections(gate: Gate, text: str, path: Path, sections: list[str]) -> None:
    for section in sections:
        if section not in text:
            gate.error(f"{rel(path)} is missing required section: {section}")


def section_text(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    following = re.search(r"(?m)^##\s+", text[start + len(heading) :])
    end = start + len(heading) + following.start() if following else len(text)
    return text[start:end]


def check_ca_execution(gate: Gate, task_text: str, evidence_text: str) -> None:
    cas_match = re.search(r'^cas:\s*["\']?([^"\'\n]+)', task_text, re.IGNORECASE | re.MULTILINE)
    declared = sorted(set(re.findall(r"CA\d+", cas_match.group(1), re.IGNORECASE))) if cas_match else []
    task_matrix = section_text(task_text, "## Matriz CA -> pruebas/evidencia")
    evidence_matrix = section_text(evidence_text, "## 5. Matriz De Pruebas Por Criterio De Aceptacion")
    if re.search(r"pendiente|por definir", task_matrix, re.IGNORECASE):
        gate.error("Task CA test matrix still contains placeholders")
    for ca in declared:
        if not re.search(rf"\|\s*{re.escape(ca)}(?:\s+parcial|\s+preparacion)?\s*\|", task_matrix, re.IGNORECASE):
            gate.error(f"Task test matrix is missing declared criterion {ca}")
        evidence_rows = [line for line in evidence_matrix.splitlines() if re.search(rf"\|\s*{re.escape(ca)}\b", line, re.IGNORECASE)]
        if not evidence_rows or not all(re.search(r"\|\s*(?:OK(?:\s+documental)?|no aplica\s+justificado)\s*\|\s*$", row, re.IGNORECASE) for row in evidence_rows):
            gate.error(f"Evidence test matrix requires OK or no aplica justificado for {ca}; observado is blocking")
    for heading in ("## Validaciones requeridas", "## Evidencia requerida", "## Checklist de cierre"):
        if "- [ ]" in section_text(task_text, heading):
            gate.error(f"Task section still has unchecked closure items: {heading}")
    delivery = section_text(evidence_text, "## 9. Estado Para Entrega")
    if "- [ ]" in delivery:
        gate.error("Evidence delivery checklist still has unchecked items")


def markdown_cells(line: str) -> int:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return 0
    return len([cell for cell in stripped.split("|")[1:-1]])


def check_markdown_tables(gate: Gate, path: Path, text: str) -> None:
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1], start=1):
        if "|" not in line or "|" not in lines[index]:
            continue
        if not re.match(r"^\s*\|?\s*:?-{3,}:?", lines[index]):
            continue
        header_cells = markdown_cells(line)
        separator_cells = markdown_cells(lines[index])
        if header_cells and separator_cells and header_cells != separator_cells:
            gate.error(
                f"Malformed markdown table in {rel(path)}:{index}: "
                f"header has {header_cells} columns, separator has {separator_cells}"
            )


def check_referenced_migrations(gate: Gate, text: str) -> None:
    for match in sorted(set(re.findall(r"db/migrations/[A-Za-z0-9_./-]+\.sql", text))):
        if "YYYYMMDD" in match:
            continue
        path = ROOT / match
        if not is_tracked(path):
            gate.error(f"Referenced migration does not exist: {match}")


def check_doc_contradictions(gate: Gate, hito: int, task_text: str, evidence_text: str) -> None:
    close_claim = re.search(r"estado:\s*completad[oa]", task_text, re.IGNORECASE) or re.search(
        r"listo\s+para\s+PR|Hito listo para PR|Implementado\s+[—-]\s+listo", evidence_text, re.IGNORECASE
    )
    changelog_blocks = extract_changelog_blocks(hito)
    if not changelog_blocks:
        gate.error(f"No changelog block found for Hito {hito}")
        return

    stale_terms = re.compile(
        r"observado|NO-GO|no listo|requiere ajuste|antes de PR listo|ST-0?9\s+a\s+ST-12\s+pendientes",
        re.IGNORECASE,
    )
    for path, block in changelog_blocks:
        if close_claim and stale_terms.search(block):
            gate.error(
                f"{rel(path)} still contains observed/pending language for Hito {hito} "
                "while task/evidence claims ready or completed"
            )


def check_schema_doc_consistency(gate: Gate, hito: int, task_text: str, evidence_text: str, changelog_text: str) -> None:
    config = HITO_CONFIG.get(hito)
    if not config:
        return
    combined = "\n".join([task_text, evidence_text, changelog_text])
    lower = combined.lower()
    for term, reason in config["schema_terms_forbidden"].items():
        if re.search(rf"\b{re.escape(term.lower())}\b", lower):
            gate.error(f"Documentation uses schema alias '{term}'. {reason}")
    for term in config["required_doc_terms"]:
        if term.lower() not in lower:
            gate.error(f"Documentation is missing required schema term '{term}' for Hito {hito}.")


def staged_scope_hash(hito: int) -> str:
    qa_pattern = re.compile(rf"^\.context/evidencias/hito_{hito}_qa_gate_report_")
    lines: list[str] = []
    for path in sorted(git_lines(["diff", "--cached", "--name-only"])):
        if qa_pattern.match(path):
            continue
        if path == f".context/evidencias/hito_{hito}_informe_cumplimiento.md":
            content = read_text(ROOT / path)
            qa_link_row = re.compile(
                rf"^\|\s*QA Gate obligatorio\s*\|\s*(?:GO|NO-GO|Pendiente)\s*\|\s*`?\.context/evidencias/hito_{hito}_qa_gate_report_\d{{8}}(?:_\d{{6}})?\.md`?.*\|\s*$",
                re.IGNORECASE,
            )
            template_row = re.compile(
                rf"^\|\s*Gate mecanico de cierre\s*\|\s*Pendiente / OK / NO-GO\s*\|.*hito_{hito}_qa_gate_report_(?:YYYYMMDD_HHMMSS|\d{{8}}_\d{{6}})\.md.*\|\s*$",
                re.IGNORECASE,
            )
            canonical_lines: list[str] = []
            for line in content.splitlines():
                if qa_link_row.fullmatch(line):
                    continue
                if template_row.fullmatch(line):
                    line = re.sub(
                        rf"hito_{hito}_qa_gate_report_(?:YYYYMMDD_HHMMSS|\d{{8}}_\d{{6}})\.md",
                        f"hito_{hito}_qa_gate_report_<BOUND>.md",
                        line,
                    )
                canonical_lines.append(line)
            content = "\n".join(canonical_lines)
            lines.append(f"{path}\0{hashlib.sha256(content.encode('utf-8')).hexdigest()}")
        else:
            entry = run_git(["ls-files", "-s", "--", path]).stdout.strip()
            if entry:
                lines.append(f"{path}\0{entry}")
            else:
                lines.append(f"{path}\0DELETED")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def check_gate_report_link(gate: Gate, hito: int, evidence_text: str) -> None:
    report_refs = sorted(set(re.findall(rf"\.context/evidencias/hito_{hito}_qa_gate_report_\d{{8}}(?:_\d{{6}})?\.md", evidence_text)))
    if not report_refs:
        gate.error(
            f"Evidence report must reference a QA gate report for Hito {hito}: "
            f".context/evidencias/hito_{hito}_qa_gate_report_YYYYMMDD_HHMMSS.md"
        )
        return

    staged = set(git_lines(["diff", "--cached", "--name-only"]))
    has_go_report = False
    for report_ref in report_refs:
        path = ROOT / report_ref
        if report_ref not in staged:
            gate.error(f"Referenced QA gate report must be staged for the current close: {report_ref}")
            continue
        if not is_tracked(path):
            gate.error(f"Referenced QA gate report is not staged/tracked: {report_ref}")
            continue
        report_text = read_text(path)
        if not re.search(r"\*\*Veredicto:\*\*\s+GO\b", report_text):
            continue
        hash_match = re.search(r"\*\*Staged scope SHA256:\*\*\s+`([0-9a-f]{64})`", report_text)
        if not hash_match or hash_match.group(1) != staged_scope_hash(hito):
            gate.error(f"QA gate report is stale or not bound to the current staged scope: {report_ref}")
            continue
        has_go_report = True

    if not has_go_report:
        gate.error(f"Evidence report must reference at least one QA gate report with Veredicto: GO for Hito {hito}")


def check_workflow_claims(gate: Gate, combined_docs: str) -> None:
    mentions_fg3_manual = re.search(r"FG3.*(manual-only|desactivad|no se reactiva)", combined_docs, re.IGNORECASE | re.DOTALL)
    workflow = ROOT / ".github" / "workflows" / "fg3_integrity.yml"
    if not mentions_fg3_manual or not is_tracked(workflow):
        return
    text = read_text(workflow)
    schedule_active = re.search(r"(?m)^\s+schedule:\s*$", text) and re.search(r"(?m)^\s+-\s+cron:\s*['\"]", text)
    if schedule_active:
        gate.error(
            f"{rel(workflow)} has an active schedule, but Hito docs claim FG3 is manual-only/desactivated"
        )


def check_dml_exception(gate: Gate, hito: int, task_text: str, evidence_text: str, changelog_text: str) -> None:
    migration_refs = [path for path in git_lines(["diff", "--cached", "--name-only", "--", "db/migrations/*.sql"])]
    operational = r'(?:"?public"?\s*\.\s*)?"?(?:courses|staging_raw|cleansed_programs|enriched_programs)"?'
    dml = re.compile(rf"\b(?:INSERT\s+INTO|UPDATE(?:\s+ONLY)?|DELETE\s+FROM|MERGE\s+INTO|TRUNCATE(?:\s+TABLE)?|COPY)\s+{operational}\b", re.IGNORECASE)
    for ref in migration_refs:
        path = ROOT / ref
        sql = read_text(path)
        dynamic_dml = re.search(r"\bEXECUTE\b", sql, re.IGNORECASE) and re.search(operational, sql, re.IGNORECASE)
        if dml.search(sql) or dynamic_dml:
            combined = task_text + "\n" + evidence_text + "\n" + changelog_text
            approvers = "|".join(re.escape(value) for value in HITO_CONFIG[hito]["dml_approvers"])
            marker = re.compile(
                rf"DML_EXCEPTION:\s*{re.escape(ref)}\s*\|\s*APPROVER:\s*(?:{approvers})\s*\|\s*JUSTIFICATION:\s*\S.+$",
                re.IGNORECASE | re.MULTILINE,
            )
            if not marker.search(combined):
                gate.error(
                    f"{ref} changes operational data and requires a migration-specific marker: "
                    f"DML_EXCEPTION: {ref} | APPROVER: <name> | JUSTIFICATION: <reason>"
                )
            if "Sin datos operativos" in changelog_text:
                gate.error(f"{ref} changes operational data but changelog still says 'Sin datos operativos'")


def validate_hito(hito: int, verify_report: bool = False) -> Gate:
    gate = Gate()
    task_paths = find_tasks(hito)
    evidence_path = find_evidence(hito)
    task_text, evidence_text, task_path = check_required_files(gate, hito, task_paths, evidence_path)
    changelog_text = "\n".join(block for _, block in extract_changelog_blocks(hito))

    check_git_state(gate)
    check_staged_scope(gate, hito)

    if task_path and task_text:
        check_sections(
            gate,
            task_text,
            task_path,
            [
                "## Matriz CA -> pruebas/evidencia",
                "## Validaciones requeridas",
                "## Evidencia requerida",
                "## Checklist de cierre",
                "## Resultado",
            ],
        )
        check_markdown_tables(gate, task_path, task_text)
        check_referenced_migrations(gate, task_text)

    if is_tracked(evidence_path) and evidence_text:
        check_sections(
            gate,
            evidence_text,
            evidence_path,
            [
                "## 3. Matriz De Cumplimiento Por Criterio De Aceptacion",
                "## 5. Matriz De Pruebas Por Criterio De Aceptacion",
                "## 7. Evidencia De Validacion",
                "## 9. Estado Para Entrega",
            ],
        )
        check_markdown_tables(gate, evidence_path, evidence_text)
        check_referenced_migrations(gate, evidence_text)

    check_doc_contradictions(gate, hito, task_text, evidence_text)
    check_ca_execution(gate, task_text, evidence_text)
    check_schema_doc_consistency(gate, hito, task_text, evidence_text, changelog_text)
    if verify_report:
        check_gate_report_link(gate, hito, evidence_text)
    check_workflow_claims(gate, task_text + "\n" + evidence_text + "\n" + changelog_text)
    check_dml_exception(gate, hito, task_text, evidence_text, changelog_text)
    return gate


def build_report(hito: int, gate: Gate, command: str, generated_at: datetime) -> str:
    status = "NO-GO" if gate.errors else "GO"
    lines = [
        f"# QA Gate Report — Hito {hito}",
        "",
        "## Resultado",
        f"- **Veredicto:** {status}",
        f"- **Comando:** `{command}`",
        f"- **Generado:** {generated_at.isoformat(timespec='seconds')}",
        f"- **Staged scope SHA256:** `{staged_scope_hash(hito)}`",
        "",
    ]

    if gate.errors:
        lines.extend(["## Hallazgos Bloqueantes", ""])
        for index, error in enumerate(gate.errors, start=1):
            lines.append(f"{index}. {error}")
        lines.append("")

    if gate.warnings:
        lines.extend(["## Advertencias", ""])
        for index, warning in enumerate(gate.warnings, start=1):
            lines.append(f"{index}. {warning}")
        lines.append("")

    if not gate.errors and not gate.warnings:
        lines.extend(["## Hallazgos", "", "No se detectaron hallazgos mecanicos.", ""])

    lines.extend(
        [
            "## Regla De Uso",
            "Este reporte es evidencia obligatoria del gate mecanico. Si el veredicto es NO-GO, el hito no puede marcarse como completado ni listo para PR.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(hito: int, gate: Gate, command: str) -> Path:
    now = datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = ROOT / ".context" / "evidencias" / f"hito_{hito}_qa_gate_report_{stamp}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_report(hito, gate, command, now), encoding="utf-8", newline="\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that a hito can be closed without artifact contradictions.")
    parser.add_argument("--hito", type=int, required=True, help="Milestone number to validate, e.g. 1")
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate a candidate timestamped report. Stage and link it, then rerun without this flag for final GO.",
    )
    args = parser.parse_args()

    gate = validate_hito(args.hito, verify_report=not args.generate_report)
    command = "python3 scripts/maintenance/validate_hito_close.py --hito " + str(args.hito)
    if args.generate_report:
        command += " --generate-report"
    report_path = write_report(args.hito, gate, command) if args.generate_report else None

    print(f"HITO {args.hito} CLOSE GATE")
    if report_path:
        print(f"Report: {rel(report_path)}")
    if gate.warnings:
        print("\nWARNINGS:")
        for warning in gate.warnings:
            print(f"- {warning}")
    if gate.errors:
        print("\nNO-GO:")
        for error in gate.errors:
            print(f"- {error}")
        return 1

    if args.generate_report:
        print("\nCANDIDATE GO: stage/link the report and rerun without --generate-report")
        return 0
    print("\nGO: hito close gate passed with staged report verification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
