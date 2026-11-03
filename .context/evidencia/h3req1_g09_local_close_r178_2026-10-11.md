# Cierre local H3REQ1 — R178 — 2026-10-11

## Candidato y alcance

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- El candidato se identifica mediante el manifest R6 y su WIP; HEAD por sí
  solo no representa los cambios locales.
- La autorización cubrió únicamente ejecución local H3REQ1. No se creó PR,
  commit, push, merge, workflow remoto, deploy ni escritura cloud.

## Resultado

G01–G09 quedan completos para los alcances locales declarados. LOCAL-23 cerró
tras el dictamen estático independiente PASS de R5; no hubo HIGH/MEDIUM ni
hallazgos bloqueantes. G10 sigue pendiente de CI remoto y revisión humana.
El PR solo queda preparado localmente con la plantilla versionada.

| Gate | Resultado vigente | Evidencia principal y límites |
|---|---|---|
| G01 | Completo | Harnesses PG17/editorial compatibles con sus inputs actuales; sin DB operativa. |
| G02 | Completo | C03 SQL aislado conservado; el integrado se acredita aparte. |
| G03 | Completo | R160/R161, tooling y contratos afectados en Docker. 337 passed/4 skipped/1 warning en pytest de proyecto; skips y warning permanecen declarados. |
| G04 | Completo | Diagnóstico de F1 según Docker Desktop/WSL; no se repitió F1 ni se atribuyó el bloqueo a Docker defectuoso. |
| G05 | Completo | Snapshot S18: 17/17 fuentes y manifest. |
| G06 | Completo | Pages/workerd local y healthz real S16; artifact normal R146 verificado 201/201. |
| G07 | Completo | C03 integrado R51 PASS; 128/128 inputs coinciden; Pages/workerd, Edge, PG17 y PostgREST locales. |
| G08 | Completo | R159–R176: scanner, writer scan, pytest, tipos, lint, auditorías, builds y checks focales vigentes por inputs. Actionlint 1.7.7 y ShellCheck 0.11.0 PASS. R6 escaneo de credenciales 854 paths PASS en `studiamatch-dev`. |
| G09 | Completo local | Matriz LOCAL-01..23; INV-008 corregido y onboarding 10/10; 216/216 resultados caso-viewport seleccionados; R173 6/6 viewports y 36/36 aserciones; revisión independiente R5 PASS. |
| G10 | Pendiente remoto | No se instaló ni exigió el workflow, no se ejecutó CI remoto ni se obtuvo revisión humana GitHub. Requiere decisión e instrucción remota separadas. |

Métricas con el mismo denominador: tablero histórico G01–G10 pasa de
8/10 (80%) a 9/10 (90%), delta +10 puntos porcentuales. Cierre local G01–G09
pasa de 8/9 (88,89%) a 9/9 (100%), delta +11,11 puntos. El 100% corresponde a
la aceptación local; no equivale a GO_LOCAL_PR ni GO_DEVELOPMENT_REAL.

## Aceptación cliente y límites

1. Admin completa/corrige cursos conservando procedencia, autoría, overrides y
   rechazo de conflicto de versión: PASS en fixture sintético local.
2. Auditoría protegida/atómica con actor, fecha, antes/después: PASS en
   harnesses PostgreSQL 17 y recorrido integrado local.
3. Evidencia de disponibilidad válida, máximo inclusivo de 90 días, rechazo de
   exceso/futuro/vencida y compatibilidad legacy: PASS local.
4. Encabezado con correo autenticado y fallback, roles conservados: R173
   PASS, 6/6 viewports, 36/36 assertions, seis capturas y cero retries.

Los seis pilares se satisfacen dentro de sus límites observados: funcionalidad
con fixtures sintéticos; escalabilidad y rendimiento descriptivos sin SLA;
seguridad sin HIGH/MEDIUM conocidos en revisiones locales; mantenimiento con
los seguimientos documentados; calidad con skips/warnings explícitos. La
transición `expand -> compatibilidad -> deploy -> contract` se validó hasta el
runtime/build local; despliegue, contracción y rollback remotos no se
ejecutaron. Se conserva la mejora LOW opcional de grants por columna para la
revisión del schema antes de una promoción remota, sin bloquear aceptación
local ni conceder acceso a roles cliente.

## Evidencia R178

La revisión final R6 identificó una lista de tareas R72 que seguía rotulada
como pendiente aunque los deltas posteriores cerraron LOCAL-02/03. Se preservó
el corte histórico, se marcó como anterior a R75 y se cerró T02 con R116
(poblado/vacío/503), R119 (16 deep links propios en cinco instituciones) y
R146 (misma identidad después de mutación y rebuild normal). No hubo cambio de
código ni de cobertura ejecutada; se actualizan los pins del paquete R6 y se
revalida el escaneo documental.

El primer despacho del scan actualizado terminó con exit 2 antes de leer
contenido porque `git ls-files` textual escapó dos rutas UTF-8 y el receptor
las trató como nombres literales inexistentes. La comprobación acotada localizó
el fallo en el enumerador host→contenedor, no en el scanner ni en los archivos.
El despacho se corrigió a `git -c core.quotePath=false ls-files -z`; la pasada
final en `studiamatch-dev` terminó `phase=credential-scan-r6-reconciled`, 854
rutas, `error_code=OK`, exit 0.

- [Revisión independiente R5](h3req1_g09_final_review_r5_2026-10-11.md).
- [Matriz LOCAL-01..23](h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md).
- [G08 final](h3req1_g08_final_checks_reconciliation_2026-10-11.md).
- [Manifest R6](h3req1_pr_scope_manifest_2026-10-11_r6.json) y [cuerpo R6](h3req1_pr_body_draft_local_review_2026-10-11_r6.md).

Sin operaciones remotas. Production, Certification, cuentas reales, secretos
y el checkout original permanecen intactos.
