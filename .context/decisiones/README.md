# Registro de decisiones

> Índice de decisiones existentes. No se crean decisiones implícitas ni se convierten metas históricas en política operativa.

| Decisión | Estado declarado en su nota | Alcance / efecto | Vigencia para este corte |
|---|---|---|---|
| [ADR-0026 — cutoff H1 y baseline Sprint 1](ADR-0026_cutoff_h1_y_baseline_sprint1.md) | ACCEPTED | Fija cutoff y baseline técnicos de H1/Sprint 1 y preserva waivers/artefactos históricos. | Historia aprobada; el trabajo actual sigue el [estado operativo](../estado_del_proyecto.md) y la autoridad cliente sanitizada vigente. |
| [ADR-0028 — target release governance](ADR-0028_target_release_governance.md) | ACCEPTED_AS_TARGET_NOT_ACTIVE | Describe un modelo futuro de release RF-01 y condiciones de activación. | TARGET / NOT ACTIVE; no usar para promover H3. Git flow actual indicado en AGENTS.md permanece. |
| ADR-0027 — work packages y convergencia | Retirado/no disponible como documento vigente | El archivo fue agregado en commit local 70917eb5 y eliminado por commit local a92f1753 el 2026-08-25; la versión histórica es recuperable solo mediante Git local | No restaurarlo ni usarlo como autoridad. El corte operativo está en [estado_del_proyecto](../estado_del_proyecto.md); los commits locales consultados se identifican en la [historia Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). No se consultó remoto. |
| Decisiones de alcance H3REQ1 y transporte JWT | Atestadas en la [fuente sanitizada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md) | Aceptación del plan dentro del alcance existente, encabezado Admin y excepción estrecha de transporte documentada por fecha | Aprobación local acotada; no concede JIT ni autorización remota. Leer sección/fecha y contrato de credenciales antes de aplicar. |
| Transición de schema H2/H3 y autoridad de baseline | [AGENTS.md](../../AGENTS.md), [estado](../estado_del_proyecto.md), migrations y evidencia por hito | Pro es baseline de schema; expansión/compatibilidad y contracción requieren evidencia por ambiente | Vigente como regla del proyecto. SQL local no demuestra aplicación remota. |

No se reconstruyen alternativas o motivos que no estén escritos en las fuentes. La historia de decisiones completa y sus límites permanecen en las notas originales; este índice solo conecta los documentos. Una nueva decisión funcional requiere la autoridad humana correspondiente.

[Requerimientos](../requerimientos/README.md) · [Hitos](../hitos/README.md) · [Arquitectura](../arquitectura.md) · [Índice principal](../indice.md)
