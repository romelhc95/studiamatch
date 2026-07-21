import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_crear_tarea():
    module_path = ROOT / ".context/crear_tarea.py"
    spec = importlib.util.spec_from_file_location("crear_tarea", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_crear_tarea_groups_tasks_by_requirement(tmp_path, monkeypatch):
    crear_tarea = _load_crear_tarea()
    backlog_dir = tmp_path / "backlog_tareas"
    monkeypatch.setattr(crear_tarea, "BACKLOG_DIR", backlog_dir)

    ruta = crear_tarea.crear_tarea(
        est_ref="EST-999",
        fase="1",
        titulo="Ajuste de catalogo",
        requerimiento="Req Catalogo Hito 2",
        hito="Hito 2",
        archivos=["scripts/core/sync_vector_worker.py"],
    )

    assert ruta.parent == backlog_dir / "req_catalogo_hito_2"
    assert ruta.name == "tarea_001_ajuste_de_catalogo.md"
    assert (ruta.parent / "_index.md").exists()
    contenido = ruta.read_text(encoding="utf-8")
    assert "requerimiento: req_catalogo_hito_2" in contenido
    assert "[[../../estimaciones/est_999]]" in contenido


def test_siguiente_id_is_recursive(tmp_path, monkeypatch):
    crear_tarea = _load_crear_tarea()
    backlog_dir = tmp_path / "backlog_tareas"
    (backlog_dir / "req_a").mkdir(parents=True)
    (backlog_dir / "req_b").mkdir(parents=True)
    (backlog_dir / "req_a/tarea_001_a.md").write_text("", encoding="utf-8")
    (backlog_dir / "req_b/tarea_007_b.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(crear_tarea, "BACKLOG_DIR", backlog_dir)

    assert crear_tarea._siguiente_id() == "008"


def test_requerimiento_slug_rejects_path_traversal_by_sanitizing():
    crear_tarea = _load_crear_tarea()

    assert crear_tarea._slug_requerimiento("../../x") == "x"
    assert crear_tarea._slug_requerimiento("C:\\Users\\Romel\\secret") == "c_users_romel_secret"
    assert crear_tarea._slug_requerimiento("Req Catalogo Hito 2") == "req_catalogo_hito_2"
