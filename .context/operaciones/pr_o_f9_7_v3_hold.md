# PR-O F9.7 - V1 Superseded

| Campo | Valor |
|---|---|
| ID historico | `PR-O-F9.7-V3-HOLD-001` |
| Estado vigente | `SUPERSEDED_NON_PROMOTABLE` |
| Subfase | `F9.7` |
| Base de merge que lo dejo en historia | `desarrollo@ee0e320d55b70dedd72c5a09429ed84a34bf7543` / tree `218bfcc7e99bdef3569fc730bba21228dee53540` |
| Sucesor canonico | [PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md) |

Esta nota preserva la existencia documental del PR-O v1 definido en PR #261. No se borra historia, no se eliminan artifacts y no se modifican SQL/manifests. Desde el merge `ee0e320d55b70dedd72c5a09429ed84a34bf7543`, este contrato deja de ser ruta aplicable, candidate promocionable o base para `GO_FOR_FREE`.

## Motivo De Supersesion

- El PR-O v1 no exigia eliminar `public.exec_sql(text)` del estado final.
- El hold terminal `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729` queda conservado como artifact actual, pero `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE` hasta existir hold sucesor.
- El tombstone Edge en Git no prueba estado remoto; el cierre futuro exige `REMOTE_ABSENT`, `REMOTE_TOMBSTONE_410` o `DISABLEMENT_SEPARATE_AUTHORIZED`.
- La secuencia atomica debe separar postcondiciones y ledgers de v3 y del hold sucesor antes del commit unico.
- Boundary `7` debe ser replay realmente `READ ONLY` y sin locks de escritura.

## Invariantes Conservados

- `application_authorized=false`.
- `capabilities=[]`.
- Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`.
- No hubo Supabase Free/Pro, DDL/DML remoto, backup, restore, writers, Edge, backfill, Cloudflare, Pro ni produccion.
- Los siete SQL y los manifests actuales permanecen byte-identicos; sus digests vigentes se fijan en el contrato sucesor.

## Prohibiciones

- No usar este PR-O v1 para aplicar v3, aplicar el hold actual, abrir `GO_FOR_FREE`, certificar F9.7 o promover a Pro.
- No tratar `db/migrations/20260729_fase09_7_leads_email_security_hold.sql` ni `db/manifests/fase09_7_leads_email_security_hold.json` como paquete final promocionable.
- No inferir estado Edge remoto desde el tombstone Git.

## Referencias

- [PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md)
- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Plan de corte Hito 1](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- Cierre definitivo F9.7
