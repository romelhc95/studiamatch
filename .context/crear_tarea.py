r"""
Script: crear_tarea.py
Uso:   python .context/crear_tarea.py --est EST-001 --fase 80 --titulo "Agregar X" --requerimiento req_catalogo
       python .context/crear_tarea.py --est est_001 --requerimiento req_hito_1 --fase 1 --titulo "Paquete 1" --hito "Hito 1" --paquete "Paquete 1" --cas "CA1, CA2" --fecha-inicio 2026-07-11 --fecha-limite 2026-07-25 --despliegue "2026-07-27 09:00 PET" --skill-principal frontend-design --subespecialidad "Frontend Next.js 16" --skill-apoyo security-auditor --entregable "PR a desarrollo" --criterio "Criterio verificable"
       python .context/crear_tarea.py --listar
       python .context/crear_tarea.py --completar TAREA-003

Crea/actualiza archivos de tarea en .context/backlog_tareas/<requerimiento>/ siguiendo la plantilla.
Ejecutar desde la raiz del repo (C:\Users\Romel\Proyectos\studiamatch).
"""
import argparse
import re
from pathlib import Path
from datetime import date, datetime

CONTEXT_DIR = Path(__file__).resolve().parent
BACKLOG_DIR = CONTEXT_DIR / "backlog_tareas"
PLANTILLA = BACKLOG_DIR / "_plantilla_tarea.md"

def _siguiente_id():
    """Calcula el siguiente ID de tarea basado en archivos existentes."""
    max_id = 0
    for f in BACKLOG_DIR.rglob("tarea_*.md"):
        m = re.match(r"tarea_(\d{3})_.*\.md", f.name)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return f"{max_id + 1:03d}"


def _slug_titulo(titulo):
    """Convierte titulo en slug para nombre de archivo."""
    slug = titulo.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug[:60].strip("_") or "sin_titulo"


def _normalizar_est_ref(est_ref):
    """Normaliza EST-001 a est_001 para enlaces Obsidian/archivo."""
    return est_ref.strip().lower().replace("-", "_")


def _slug_requerimiento(valor):
    slug = (valor or "").strip().lower().replace("-", "_")
    slug = re.sub(r"[^a-z0-9_]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "req_sin_nombre"


def _ensure_requerimiento_index(req_dir, requerimiento, est_ref_normalizada):
    index = req_dir / "_index.md"
    if index.exists():
        return
    hoy = date.today().isoformat()
    index.write_text(
        f"""# Backlog — {requerimiento}

## Contexto
- **Estimacion de referencia:** [[../../estimaciones/{est_ref_normalizada}]]
- **Creado:** {hoy}

## Reglas
- Este directorio contiene solo tareas del requerimiento `{requerimiento}`.
- No mezclar tareas de otros requerimientos.
- Las tareas one-shot o descartadas deben documentarse y moverse a `desestimado/` si no son recurrentes.
""",
        encoding="utf-8",
    )


def _lista_markdown(items, fallback="Por definir"):
    if not items:
        return f"- [ ] {fallback}"
    return "\n".join(f"- [ ] {item}" for item in items)


def _valor(valor, fallback="Por definir"):
    return valor if valor else fallback


def crear_tarea(
    est_ref,
    fase,
    titulo,
    requerimiento=None,
    prioridad="alta",
    hito=None,
    paquete=None,
    cas=None,
    fecha_inicio=None,
    fecha_limite=None,
    despliegue=None,
    responsable="IA implementadora",
    revisor="security-auditor",
    aprobador="Usuario/PM",
    skill_principal="general",
    subespecialidad=None,
    skills_apoyo=None,
    gate_obligatorio="security-auditor",
    entregable=None,
    criterios=None,
    archivos=None,
    dependencias=None,
):
    tarea_id = _siguiente_id()
    nombre_archivo = f"tarea_{tarea_id}_{_slug_titulo(titulo)}.md"
    hoy = date.today().isoformat()
    est_ref_normalizada = _normalizar_est_ref(est_ref)
    req_slug = _slug_requerimiento(requerimiento or est_ref_normalizada)
    req_dir = BACKLOG_DIR / req_slug
    req_dir.mkdir(parents=True, exist_ok=True)
    _ensure_requerimiento_index(req_dir, req_slug, est_ref_normalizada)
    ruta = req_dir / nombre_archivo
    cas_valor = _valor(cas, "Por definir")
    skills_apoyo_valor = ", ".join(skills_apoyo) if skills_apoyo else "Por definir"
    criterios_md = _lista_markdown(criterios, "Criterios derivados de la estimacion aprobada")
    archivos_md = "\n".join(f"| `{a}` | Por definir |" for a in archivos) if archivos else "| Por definir | Por definir |"
    dependencias_md = "\n".join(f"- {d}" for d in dependencias) if dependencias else "- Sin dependencias registradas"

    contenido = f"""---
id: TAREA-{tarea_id}
fase: {fase}
estado: pendiente
prioridad: {prioridad}
estimacion_ref: {est_ref_normalizada}
requerimiento: {req_slug}
hito: {_valor(hito)}
paquete: {_valor(paquete)}
cas: "{cas_valor}"
fecha_inicio: {_valor(fecha_inicio)}
fecha_limite: {_valor(fecha_limite)}
despliegue: "{_valor(despliegue)}"
responsable: {responsable}
revisor: {revisor}
aprobador: {aprobador}
skill_principal: {skill_principal}
subespecialidad: {_valor(subespecialidad)}
skills_apoyo: "{skills_apoyo_valor}"
gate_obligatorio: {gate_obligatorio}
entregable: "{_valor(entregable)}"
creado: {hoy}
tags: []
---

# Tarea {tarea_id}: {titulo}

## Contexto
Estimacion de referencia: [[../../estimaciones/{est_ref_normalizada}]]

- **Requerimiento:** {req_slug}
- **Hito:** {_valor(hito)}
- **Paquete:** {_valor(paquete)}
- **CAs cubiertos:** {cas_valor}
- **Responsable de ejecucion:** {responsable}
- **Revisor obligatorio:** {revisor}
- **Aprobador:** {aprobador}
- **Entregable:** {_valor(entregable)}

## Skills y sub-especialidad
- **Skill principal:** {skill_principal}
- **Sub-especialidad tecnica:** {_valor(subespecialidad)}
- **Skills de apoyo:** {skills_apoyo_valor}
- **Gate obligatorio:** {gate_obligatorio}

## Plazos
- **Inicio comprometido:** {_valor(fecha_inicio)}
- **Fecha limite de construccion:** {_valor(fecha_limite)}
- **Despliegue objetivo:** {_valor(despliegue)}

## Dependencias
{dependencias_md}

## Criterios de Aceptacion
{criterios_md}

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
{archivos_md}

## Plan de ejecucion
1. Confirmar alcance contra la estimacion aprobada.
2. Implementar el cambio minimo que satisfaga los criterios.
3. Ejecutar validaciones aplicables en el contenedor Docker.
4. Invocar revision de seguridad antes de commit/PR.
5. Registrar resultado en changelog.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
"""
    with open(ruta, "w", encoding="utf-8") as fp:
        fp.write(contenido)
    print(f"Creada: backlog_tareas/{req_slug}/{nombre_archivo}")
    print(f"  ID: TAREA-{tarea_id} | Fase: {fase} | Est: {est_ref_normalizada} | Req: {req_slug}")
    return ruta


def listar_tareas():
    tareas = sorted(
        [f for f in BACKLOG_DIR.rglob("tarea_*.md")]
    )
    if not tareas:
        print("No hay tareas en backlog.")
        return
    print(f"{'Archivo':<70} {'Estado':<12} {'Fase':<6}")
    print("-" * 88)
    for t in tareas:
        ruta = t
        with open(ruta, encoding="utf-8") as fp:
            contenido = fp.read()
        estado = re.search(r"estado:\s*(\w+)", contenido)
        fase = re.search(r"fase:\s*(\w+)", contenido)
        rel = ruta.relative_to(BACKLOG_DIR).as_posix()
        print(f"{rel:<70} {estado.group(1) if estado else '?':<12} {fase.group(1) if fase else '?':<6}")


def completar_tarea(tarea_id):
    tarea_num = tarea_id.replace("TAREA-", "")
    for f in BACKLOG_DIR.rglob("tarea_*.md"):
        if f.name.startswith(f"tarea_{tarea_num}_") and f.name.endswith(".md"):
            ruta = f
            with open(ruta, encoding="utf-8") as fp:
                contenido = fp.read()
            contenido = contenido.replace("estado: pendiente", "estado: completada")
            contenido = contenido.replace("estado: en_progreso", "estado: completada")
            hoy = date.today().isoformat()
            contenido += f"\n\n## Completada\n- **Fecha**: {hoy}\n- **IA**: [nombre del modelo]"
            with open(ruta, "w", encoding="utf-8") as fp:
                fp.write(contenido)
            rel = f.relative_to(BACKLOG_DIR).as_posix()
            print(f"Completada: {rel} -> estado: completada ({hoy})")
            return
    print(f"No se encontro tarea con ID {tarea_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestion de tareas StudIAMatch")
    parser.add_argument("--est", help="Referencia de estimacion (ej: EST-001)")
    parser.add_argument("--requerimiento", help="Slug del requerimiento contenedor (ej: req_catalogo_hito_1)")
    parser.add_argument("--fase", help="Numero de fase")
    parser.add_argument("--titulo", help="Titulo descriptivo de la tarea")
    parser.add_argument("--prioridad", default="alta", choices=["baja", "media", "alta", "critica"])
    parser.add_argument("--hito", help="Hito de entrega asociado")
    parser.add_argument("--paquete", help="Paquete de la estimacion asociado")
    parser.add_argument("--cas", help="Criterios de aceptacion cubiertos (ej: CA1, CA2)")
    parser.add_argument("--fecha-inicio", help="Fecha de inicio comprometida YYYY-MM-DD")
    parser.add_argument("--fecha-limite", help="Fecha limite de construccion YYYY-MM-DD")
    parser.add_argument("--despliegue", help="Fecha/hora objetivo de despliegue")
    parser.add_argument("--responsable", default="IA implementadora", help="Responsable de ejecucion")
    parser.add_argument("--revisor", default="security-auditor", help="Revisor obligatorio")
    parser.add_argument("--aprobador", default="Usuario/PM", help="Aprobador funcional")
    parser.add_argument("--skill-principal", default="general", help="Skill/agente principal sugerido")
    parser.add_argument("--subespecialidad", help="Sub-especialidad tecnica sugerida")
    parser.add_argument("--skill-apoyo", action="append", dest="skills_apoyo", help="Skill/agente de apoyo. Repetible")
    parser.add_argument("--gate-obligatorio", default="security-auditor", help="Gate obligatorio antes de commit/PR")
    parser.add_argument("--entregable", help="Entregable concreto")
    parser.add_argument("--criterio", action="append", dest="criterios", help="Criterio de aceptacion verificable. Repetible")
    parser.add_argument("--archivo", action="append", dest="archivos", help="Archivo previsto afectado. Repetible")
    parser.add_argument("--dependencia", action="append", dest="dependencias", help="Dependencia de la tarea. Repetible")
    parser.add_argument("--listar", action="store_true", help="Listar todas las tareas")
    parser.add_argument("--completar", help="Marcar tarea como completada (ej: TAREA-003)")
    args = parser.parse_args()

    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.listar:
        listar_tareas()
    elif args.completar:
        completar_tarea(args.completar)
    elif args.est and args.fase and args.titulo:
        crear_tarea(
            est_ref=args.est,
            fase=args.fase,
            titulo=args.titulo,
            requerimiento=args.requerimiento,
            prioridad=args.prioridad,
            hito=args.hito,
            paquete=args.paquete,
            cas=args.cas,
            fecha_inicio=args.fecha_inicio,
            fecha_limite=args.fecha_limite,
            despliegue=args.despliegue,
            responsable=args.responsable,
            revisor=args.revisor,
            aprobador=args.aprobador,
            skill_principal=args.skill_principal,
            subespecialidad=args.subespecialidad,
            skills_apoyo=args.skills_apoyo,
            gate_obligatorio=args.gate_obligatorio,
            entregable=args.entregable,
            criterios=args.criterios,
            archivos=args.archivos,
            dependencias=args.dependencias,
        )
    else:
        parser.print_help()
