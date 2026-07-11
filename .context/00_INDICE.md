# StudIAMatch — Base de Conocimiento

## Regla de Oro para IAs
> **ANTES de ejecutar cualquier tarea de codigo, lee OBLIGATORIAMENTE**
> `prompts/system_prompt_base.md` para conocer reglas de ejecucion y restricciones.
> Luego consulta el archivo de arquitectura relevante segun el dominio de la tarea.

## Arquitectura (READ-ONLY — consultar, no modificar sin autorizacion)
- [[estructura_backend]] — Backend de 3 capas: Ingesta Python → Supabase BaaS → Next.js BFF
- [[sistema_db_supabase]] — Esquema DB completo, 14 tablas, RLS, funciones, indices
- [[arquitectura_pipeline]] — Pipeline FG2 de 4 estaciones, workflows CI/CD, gating
- [[estructura_frontend]] — App Router Next.js 16, rutas, componentes, patron de datos
- [[estado_del_proyecto]] — Deuda tecnica, limitaciones, SDLC, monitoreo

## Flujo de Trabajo (IA + Humano)
1. Llega requerimiento → IA lee `.context/` completo
2. IA genera estimacion en `estimaciones/est_XXX.md`
3. Humano aprueba o rechaza
4. IA crea tarea con `python .context/crear_tarea.py --est EST-XXX --fase NN --titulo "..."`
5. IA ejecuta siguiendo `prompts/system_prompt_base.md`
6. IA registra cambios en `changelog/`

## Backlog de Tareas
- [[backlog_tareas/_plantilla_tarea]]

## Estimaciones
- [[estimaciones/_plantilla_estimacion]]

## Operaciones
- [[operaciones/flujo_requerimientos]] — Requerimiento → estimacion → aprobacion → tareas → entrega

## Decisiones Arquitectonicas (ADR)
- [[decisiones/_plantilla_adr]]

## Changelog
- [[changelog/2026-07-05]] — Inicializacion
