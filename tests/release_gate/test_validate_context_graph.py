from pathlib import Path

from scripts.maintenance.validate_context_graph import validate_context_graph


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_context_graph_accepts_connected_notes(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "- [[area/_index]]\n")
    _write(root / "area/_index.md", "- [[note]]\n")
    _write(root / "area/note.md", "# Note\n")

    assert validate_context_graph(root) == ([], [])


def test_validate_context_graph_reports_missing_links(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "- [[missing_note]]\n")

    assert validate_context_graph(root) == (["00_INDICE.md: [[missing_note]]"], [])


def test_validate_context_graph_reports_orphans(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "# Index\n")
    _write(root / "area/orphan.md", "# Orphan\n")

    assert validate_context_graph(root) == ([], ["area/orphan.md"])


def test_validate_context_graph_ignores_templates_and_placeholders(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "- [[_plantilla_tarea]]\n")
    _write(root / "_plantilla_tarea.md", "- [[estimaciones/est_XXX]]\n")

    assert validate_context_graph(root) == ([], [])


def test_validate_context_graph_rejects_disconnected_cycles(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "# Index\n")
    _write(root / "area/a.md", "- [[b]]\n")
    _write(root / "area/b.md", "- [[a]]\n")

    missing, orphans = validate_context_graph(root)

    assert missing == []
    assert orphans == ["area/a.md", "area/b.md"]


def test_validate_context_graph_rejects_out_of_vault_relative_links(tmp_path):
    root = tmp_path / ".context"
    _write(root / "00_INDICE.md", "- [[../README]]\n")
    _write(tmp_path / "README.md", "# Outside\n")

    missing, orphans = validate_context_graph(root)

    assert missing == ["00_INDICE.md: [[../README]]"]
    assert orphans == []
