r"""
Script: crear_tarea.py
Uso:   python .context/crear_tarea.py --est EST-001 --fase 80 --titulo "Agregar X"
       python .context/crear_tarea.py --est est_001 --fase 1 --titulo "Paquete 1" --hito "Hito 1" --paquete "Paquete 1" --cas "CA1, CA2" --fecha-inicio 2026-07-11 --fecha-limite 2026-07-25 --despliegue "2026-07-27 09:00 PET" --skill-principal frontend-design --subespecialidad "Frontend Next.js 16" --skill-apoyo security-auditor --entregable "PR a desarrollo" --criterio "Criterio verificable" --analisis-previo "Revisar schema actual" --especificacion-cambio "courses.campo text not null default 'x'" --subtarea "ST-01 — Analizar y documentar cambio exacto"
       python .context/crear_tarea.py --listar
       python .context/crear_tarea.py --completar TAREA-003

Crea/actualiza archivos de tarea en .context/backlog_tareas/ siguiendo la plantilla.
Ejecutar desde la raiz del repo (C:\Users\Romel\Proyectos\studiamatch).
"""
import argparse
import re
import sys
from pathlib import Path
from datetime import date, datetime

CONTEXT_DIR = Path(__file__).resolve().parent
BACKLOG_DIR = CONTEXT_DIR / "backlog_tareas"
PLANTILLA = BACKLOG_DIR / "_plantilla_tarea.md"

def _siguiente_id():
    """Calcula el siguiente ID de tarea basado en archivos existentes."""
    max_id = 0
    for f in BACKLOG_DIR.iterdir():
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


def _lista_markdown(items, fallback="Por definir"):
    if not items:
        return f"- [ ] {fallback}"
    return "\n".join(f"- [ ] {item}" for item in items)


def _lista_simple(items, fallback="Por definir"):
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def _valor(valor, fallback="Por definir"):
    return valor if valor else fallback


def crear_tarea(
    est_ref,
    fase,
    titulo,
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
    alcance_incluido=None,
    alcance_excluido=None,
    fuentes_requerimiento=None,
    matriz_ca=None,
    matriz_pruebas=None,
    analisis_previo=None,
    especificacion_cambio=None,
    subtareas=None,
):
    tarea_id = _siguiente_id()
    nombre_archivo = f"tarea_{tarea_id}_{_slug_titulo(titulo)}.md"
    ruta = BACKLOG_DIR / nombre_archivo
    hoy = date.today().isoformat()
    est_ref_normalizada = _normalizar_est_ref(est_ref)
    cas_valor = _valor(cas, "Por definir")
    skills_apoyo_valor = ", ".join(skills_apoyo) if skills_apoyo else "Por definir"
    criterios_md = _lista_markdown(criterios, "Criterios derivados de la estimacion aprobada")
    archivos_md = "\n".join(f"| `{a}` | Por definir |" for a in archivos) if archivos else "| Por definir | Por definir |"
    dependencias_md = "\n".join(f"- {d}" for d in dependencias) if dependencias else "- Sin dependencias registradas"
    alcance_incluido_md = _lista_simple(alcance_incluido, "Derivar de la estimacion aprobada y completar antes de ejecutar")
    alcance_excluido_md = _lista_simple(alcance_excluido, "No agregar alcance no aprobado por el usuario/PM")
    fuentes_requerimiento_md = _lista_simple(fuentes_requerimiento, "Indicar documento aprobado, secciones fuente y mockups/referencias antes de ejecutar")
    matriz_ca_md = "\n".join(f"| {item} |" for item in matriz_ca) if matriz_ca else "| CA pendiente | Detalle fuente pendiente | Implicancia tecnica pendiente | Fuera de alcance pendiente |"
    if matriz_pruebas:
        matriz_pruebas_md = "\n".join(f"| {item} |" for item in matriz_pruebas)
    else:
        ca_ids = re.findall(r"CA\d+", cas_valor, re.IGNORECASE)
        matriz_pruebas_md = "\n".join(
            f"| {ca.upper()} | Definir antes de ejecutar | Por definir | Por definir | Por definir | Por definir |"
            for ca in ca_ids
        ) or "| CA pendiente | Definir antes de ejecutar | Por definir | Por definir | Por definir | Por definir |"
    analisis_previo_md = _lista_markdown(analisis_previo, "Analizar codigo/schema actual y documentar que se va a modificar antes de ejecutar")
    especificacion_cambio_md = _lista_simple(especificacion_cambio, "Completar cambio exacto antes de ejecutar: tabla/campo/tipo/check/indice/RLS, ruta/componente/estado, worker/funcion/input/output, o workflow/job/secret segun aplique")
    subtareas_md = _lista_markdown(subtareas, "Definir subtareas con analisis previo, objetivo, cambio exacto, archivos esperados, CA relacionado y validacion concreta antes de ejecutar")

    contenido = f"""---
id: TAREA-{tarea_id}
fase: {fase}
estado: pendiente
prioridad: {prioridad}
estimacion_ref: {est_ref_normalizada}
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
Estimacion de referencia: [[../estimaciones/{est_ref_normalizada}]]

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

## Fuentes del requerimiento
{fuentes_requerimiento_md}

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
{matriz_ca_md}

## Alcance incluido
{alcance_incluido_md}

## Alcance excluido
{alcance_excluido_md}

## Criterios de Aceptacion
{criterios_md}

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
{matriz_pruebas_md}

## Analisis tecnico previo obligatorio
{analisis_previo_md}

## Especificacion exacta del cambio
{especificacion_cambio_md}

## Subtareas tecnicas
{subtareas_md}

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
{archivos_md}

## Plan de ejecucion
1. Leer estimacion aprobada, CAs y esta tarea antes de tocar codigo.
2. Ejecutar el analisis tecnico previo y documentar la especificacion exacta del cambio.
3. Resolver bloqueadores o decisiones pendientes antes de implementar.
4. Ejecutar subtareas en orden, manteniendo cambios minimos y trazables.
5. Validar cada subtarea con la evidencia indicada.
6. Ejecutar validaciones finales dentro del contenedor Docker.
7. Ejecutar `docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito X`.
8. Invocar revision de seguridad antes de commit/PR.
9. Registrar resultado en changelog.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev ...` para checks aplicables.
- [ ] Lint/typecheck si toca frontend.
- [ ] `py_compile` si toca Python.
- [ ] Revision RLS/security si toca Supabase o escrituras.
- [ ] Ejecucion completa de la matriz `CA -> pruebas/evidencia`.
- [ ] Gate mecanico de cierre con resultado `GO`.

## Evidencia requerida
- [ ] Resumen de archivos modificados y motivo.
- [ ] Salida de validaciones ejecutadas.
- [ ] Riesgos residuales o decisiones pendientes documentadas.
- [ ] PR enlazada o referencia de entrega interna.
- [ ] Informe de cumplimiento y reporte QA timestamped versionados.

## Checklist de cierre
- [ ] Todos los CAs del hito quedan cubiertos o se documenta excepcion aprobada.
- [ ] No se agregan alcances excluidos.
- [ ] El analisis previo y la especificacion exacta quedaron documentados.
- [ ] No quedan credenciales ni datos sensibles en codigo/docs.
- [ ] Changelog actualizado.
- [ ] Tarea actualizada con resultado, fecha, commits/PR y evidencia.
- [ ] Gate mecanico verificado contra el staged scope actual.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
"""
    with open(ruta, "w", encoding="utf-8") as fp:
        fp.write(contenido)
    print(f"Creada: backlog_tareas/{nombre_archivo}")
    print(f"  ID: TAREA-{tarea_id} | Fase: {fase} | Est: {est_ref_normalizada}")
    return ruta


def listar_tareas():
    tareas = sorted(
        [f.name for f in BACKLOG_DIR.iterdir() if f.name.startswith("tarea_") and f.name.endswith(".md")]
    )
    if not tareas:
        print("No hay tareas en backlog.")
        return
    print(f"{'Archivo':<45} {'Estado':<12} {'Fase':<6}")
    print("-" * 63)
    for t in tareas:
        ruta = BACKLOG_DIR / t
        with open(ruta, encoding="utf-8") as fp:
            contenido = fp.read()
        estado = re.search(r"estado:\s*(\w+)", contenido)
        fase = re.search(r"fase:\s*(\w+)", contenido)
        print(f"{t:<45} {estado.group(1) if estado else '?':<12} {fase.group(1) if fase else '?':<6}")


def completar_tarea(tarea_id):
    print(
        f"No se puede completar {tarea_id} automaticamente. Actualiza el estado y resultado, "
        "stagea el cambio, genera el reporte QA y ejecuta validate_hito_close.py --hito N."
    )
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestion de tareas StudIAMatch")
    parser.add_argument("--est", help="Referencia de estimacion (ej: EST-001)")
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
    parser.add_argument("--alcance-incluido", action="append", dest="alcance_incluido", help="Alcance incluido en la tarea. Repetible")
    parser.add_argument("--alcance-excluido", action="append", dest="alcance_excluido", help="Alcance excluido de la tarea. Repetible")
    parser.add_argument("--fuente-requerimiento", action="append", dest="fuentes_requerimiento", help="Documento/seccion/mockup fuente del requerimiento. Repetible")
    parser.add_argument("--matriz-ca", action="append", dest="matriz_ca", help="Fila CA|Detalle exacto|Implicancia tecnica|Fuera de alcance. Repetible")
    parser.add_argument("--matriz-prueba", action="append", dest="matriz_pruebas", help="Fila CA|Prueba|Tipo|Metodo|Resultado esperado|Evidencia. Repetible")
    parser.add_argument("--analisis-previo", action="append", dest="analisis_previo", help="Analisis obligatorio previo a implementar. Repetible")
    parser.add_argument("--especificacion-cambio", action="append", dest="especificacion_cambio", help="Cambio exacto a implementar: tabla/campo/tipo, ruta/componente, worker/funcion, workflow/job, etc. Repetible")
    parser.add_argument("--subtarea", action="append", dest="subtareas", help="Subtarea tecnica verificable con analisis previo, objetivo, cambio exacto, archivos, CA y validacion. Repetible")
    parser.add_argument("--listar", action="store_true", help="Listar todas las tareas")
    parser.add_argument("--completar", help="Marcar tarea como completada (ej: TAREA-003)")
    args = parser.parse_args()

    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.listar:
        listar_tareas()
    elif args.completar:
        if not completar_tarea(args.completar):
            sys.exit(1)
    elif args.est and args.fase and args.titulo:
        crear_tarea(
            args.est,
            args.fase,
            args.titulo,
            args.prioridad,
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
            alcance_incluido=args.alcance_incluido,
            alcance_excluido=args.alcance_excluido,
            fuentes_requerimiento=args.fuentes_requerimiento,
            matriz_ca=args.matriz_ca,
            matriz_pruebas=args.matriz_pruebas,
            analisis_previo=args.analisis_previo,
            especificacion_cambio=args.especificacion_cambio,
            subtareas=args.subtareas,
        )
    else:
        parser.print_help()
