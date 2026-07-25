# System Prompt Base

## Mision

Trabaja sobre StudIAMatch con cambios pequenos, verificables y fail-closed. Examina Git, codigo, workflows y la fuente tecnica aplicable antes de afirmar estado o ejecutar una promocion.

## Autoridad Documental

1. `.context/` es la unica fuente documental de verdad.
2. Consulta primero la [matriz de autoridad](../00_INDICE.md#matriz-de-autoridad) y aplica la nota canonica de cada materia.
3. El estado vivo existe solo en [Estado del proyecto](../estado_del_proyecto.md) y en la tarea activa enlazada desde alli.
4. Los hitos e indices describen alcance y navegacion; el changelog conserva historia no autoritativa.
5. Ante una contradiccion, no combines versiones: conserva la fuente con autoridad y registra una ADR si hace falta una decision humana.

## Reglas Inmutables

1. No exponer secretos ni registrar valores de credenciales.
2. No ejecutar una fase sin autorizacion humana explicita.
3. Ejecutar desarrollo dentro del contenedor Docker montado desde el workspace vigente; no usar `npm`, `python` o `pip` en Windows host.
4. No promover SQL a Pro antes de certificar en Free y recibir aprobacion humana.
5. No copiar datos operativos Free hacia Pro como flujo normal.
6. No editar migrations o ledgers historicos; reconciliar con migrations forward-only.
7. No marcar una fase, criterio, prueba o release como completo sin verificacion trazable.
8. Tratar los schedules declarados en YAML como activos aunque un comentario diga lo contrario.
9. Usar identificadores y enlaces relativos definidos en la [taxonomia](../backlog_tareas/_README.md#taxonomia-canonica).

## Contexto A Consultar

- [Estado vigente](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [HITO-001](../hitos/hito_001.md)
- [Pipeline](../arquitectura_pipeline.md)
- [Frontend](../estructura_frontend.md)
- [Supabase](../sistema_db_supabase.md)
- [Flujo de requerimientos](../operaciones/flujo_requerimientos.md)
- [Release minimo](../operaciones/flujo_release_minimo.md)

## Politica De Paths

Documentar rutas relativas al repositorio. La ubicacion del workspace, respaldos y worktrees es configuracion local y no se versiona.

## Salida Esperada

Comunicar hechos, diferencias entre estado actual y objetivo, validaciones ejecutadas, riesgos y gates pendientes. No presentar antecedentes historicos como implementacion vigente.
