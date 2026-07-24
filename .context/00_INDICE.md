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
Prompt obligatorio: [[prompts/system_prompt_base]]

1. Llega requerimiento → IA lee `.context/` completo
2. IA genera estimacion en `estimaciones/est_XXX.md`
3. Humano aprueba o rechaza
4. IA crea tareas por requerimiento con `python .context/crear_tarea.py --est EST-XXX --requerimiento req_XXX --fase NN --titulo "..."`
5. IA ejecuta siguiendo `prompts/system_prompt_base.md`
6. IA registra cambios en `changelog/`

## Backlog de Tareas
- [[backlog_tareas/_README]] — Regla de organizacion por requerimiento
- [[backlog_tareas/_plantilla_tarea]]
- [[backlog_tareas/req_est_001_sprint_1/_index]] — Tareas historicas EST-001 / Sprint 1

## Estimaciones
- [[estimaciones/_plantilla_estimacion]]
- [[estimaciones/est_001]] — Sprint 1 aprobado

## Operaciones
- [[operaciones/flujo_requerimientos]] — Requerimiento → estimacion → aprobacion → tareas → entrega
- [[operaciones/flujo_hitos_release]] — Ramas y ambientes permanentes del SDLC
- [[operaciones/politica_higiene_repo]] — Politica de ramas, archivos recurrentes y `desestimado/`
- [[operaciones/inventario_limpieza_repo_20260720]] — Inventario inicial de ramas y artefactos a revisar
- [[operaciones/agent_dispatcher]] — Dispatcher asistivo de agentes SDLC

## Decisiones Arquitectonicas (ADR)
- [[decisiones/_plantilla_adr]]

## Changelog
- [[changelog/2026-07-05]] — Inicializacion
- [[changelog/2026-07-11]] — Preparacion Sprint 1 / Hito 1
- [[changelog/2026-07-20]] — Dispatcher de agentes e higiene del repositorio
- [[changelog/2026-07-23]] — Migracion a API keys Supabase modernas
