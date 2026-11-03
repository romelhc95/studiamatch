# H3-CLOSE-03 — preflight integrado y bloqueo de autorización

Fecha: 2026-10-05. Estado: **NO-GO global; subgate SQL safe-suspend/resume JIT v3 PASS**.
La aprobación JIT exacta y el prompt `continua` autorizaron solo el PG17 local nuevo y los
cuatro roots enumerados. No se tocó el PG17 preservado ni Auth, servicios remotos,
despliegues, cleanup, push, PR, merge o ramas protegidas.

## Tareas y gates de este ciclo

| Tarea | Resultado verificable |
|---|---|
| Confirmar candidato, rama, WIP y Docker | PASS read-only: worktree `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`; 108 entradas WIP, 0 staged. El montaje `/candidate` del contenedor candidato es read-only. |
| Conservar H3-CLOSE-02/JIT v4 | PASS vigente: 72/72 inputs v4 no pertenecientes a C03 sin cambios. No se repitió ningún harness de ese gate. |
| Revisar nuevo candidato safe-suspend/resume | PASS estático acotado: 41/41 inputs transitivos presentes, cero includes ausentes; 2 fuentes cambiaron y 1 se agregó respecto del PASS C03 v2. Ambos mapas ACL tienen las mismas 10 firmas. No demuestra sintaxis/ejecución SQL. |
| Preservar recurso previo | PASS read-only: PG17 anterior mismo ID `88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d`, running, `network=none`, sin puertos, tmpfs 1 GiB, mounts read-only. Sigue intacto y no se conectó. |
| Validar nueva recuperación persistente | **PASS local bajo JIT v3**: los cuatro `psql` terminaron exit 0. Los tres primeros solo prepararon prerrequisitos; únicamente el harness safe-suspend/resume cuenta como resultado C03 nuevo. Confirmó `H3D01` para drift, resume persistente tras `\connect` y resume idempotente. |
| Completar rollback integrado y H3-CLOSE-01/04–08 | **NO EJECUTADO**: falta runner Pages/workerd + Edge + SQL y gates CI/Git/Cloudflare/Supabase/Auth remotos; cada uno conserva aprobación separada. |

## Candidato, alcance y hashes

Docker `h3req1-candidate-docker-20261004` monta el worktree exacto en `/candidate` como
read-only. El directorio `/workspace` dentro del contenedor es otra copia y no se usó
como fuente. `HEAD` identifica el baseline, no un candidato congelado. El estado WIP se
preservó íntegro y no se hizo stage ni commit.

Verificación de hashes ejecutada dentro de Docker sobre `/candidate`:

- El manifiesto fuente v1 tenía 74 rutas; aplicadas las sustituciones de JIT v4,
  **72/72 inputs H3-CLOSE-02 no C03** siguen sin cambios.
- El cierre actual de C03 contiene **41 rutas**, 0 ausentes. Frente a los 40 inputs del
  subgate v2, cambiaron `db/rollback/h3req1_safe_suspend.sql` y
  `tests/sql/h3_safe_suspend_harness.sql`; se agregó `db/rollback/h3req1_safe_resume.sql`.
  Por ello el PASS v2 es histórico para aquellos bytes y **no acredita este candidato**.
- SHA-256 actual: `db/rollback/h3req1_safe_suspend.sql`
  `5236371a8bb2beec5434b49f60bf56e46509b58408a81ea471e6297b41769b2d`,
  `db/rollback/h3req1_safe_resume.sql`
  `d47579a8e7c4fbf005b8bcca4b2261aa09a311b2606f167a7ee099b5b3339cd8` y
  `tests/sql/h3_safe_suspend_harness.sql`
  `821167b000ce20e18f1c4a2504bfe57fbcf4e92f33145c1290bd7c9c81bd04f6`.
- Revisión de seguridad estática de los tres archivos: un blocker y un falso positivo
  detectados en la primera pasada se corrigieron (`jsonb_object_keys`, SQLSTATE específico
  `H3D01` y aserción de resume idempotente). Segunda revisión: cero blockers estáticos
  adicionales. Ninguna revisión ejecutó SQL.
- Validación local final: cierre transitivo **41/41**, hashes del manifiesto coinciden,
  cero includes ausentes, diez ACLs idénticas y checks estáticos del SQLSTATE `H3D01` y
  los tres puntos de entrada a `safe_resume` PASS. Contratos documentales Docker: **7/7**;
  `git diff --check` PASS. Son checks estáticos/documentales; no validan ejecución SQL.
- JIT consumido: propuesta v3 SHA-256
  `89e9d48ea9b128cbb6bfcd37ce2dce03894a73e4b41d5143f523236b6625bcee`. Revalidación
  inmediatamente anterior a crear el recurso: rama `feat/h3req1-sync-20261002`,
  `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`, 108 entradas WIP, 0 staged; 41/41
  hashes exactos, contenedor destino libre, digest PG17 local exacto disponible.
- Secuencia ejecutada en `h3req1-c03-safe-resume-pg17-20261005`: `h3_from_h2_pro_pg17_harness.sql`
  exit 0 (bootstrap); `h3_admin_quota_harness.sql` exit 0 (bootstrap);
  `h3_admin_rpc_signed_gateway_harness.sql` exit 0 (bootstrap);
  `h3_safe_suspend_harness.sql` exit 0 (PASS del subgate C03). El mensaje de error
  `Current ACL is not the captured suspended state` fue el rechazo esperado; el harness
  verificó SQLSTATE `H3D01`, imprimió su marcador PASS, revirtió solo el grant fixture,
  reanudó desde la captura persistente y volvió a invocar resume para comprobar idempotencia.
  No se reivindican nuevos PASS de los tres harnesses de preparación.
- Contenedor nuevo ID `6bd601683e6c1d036990b684f59cd6d2ae818f3fd36ff4f8c03e224ab9958b32`,
  aún running y preservado (sin cleanup), imagen PG17 fijada, `network=none`, puertos vacíos,
  tmpfs 1 GiB y tres mounts candidatos `RW=false`. El contenedor anterior ID
  `88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d` sigue running,
  aislado e intacto; no recibió conexiones. Los tres hashes SQL mantienen los valores de
  arriba tras la ejecución.
- Los hashes de transporte BFF, workflow y lockfile siguen iguales a v4: `admin-bff.ts`
  `1cb1ad95d723e884f58cf98dd5b2600e59fa8230aa044cb25e6ebb41f1db7ed7`,
  `security-audit.yml` `1221ecc16a46f5f6d617deeb86d523033a2dc927985dea285c0631869b5b0b72`,
  `package-lock.json` `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc`.
- Hashes observados para el preflight de artefactos C03: Pages middleware
  `237bc47043ed8a7f0604445d43c2ca2042e352373ee165a56cf669dd4821fd9b` y Edge
  `supabase/functions/admin-invite/index.ts`
  `1569b90394b313a4b42e4e50158da077cec42d26356c0d713b16535f47053a60`.

**Corte histórico previo a ejecución v3:** se conserva sin repetir el **PASS H3-CLOSE-02/JIT v4**. El **PASS safe-suspend/JIT v2**
se conserva como resultado histórico, pero sus hashes ya no corresponden al candidato
actual y el subgate SQL necesita autorización nueva. El JIT v3 enlazado abajo es solo
propuesta; ninguno de esos PASS demuestra integración.

**Resultado posterior vigente:** v3 fue ejecutado y consumido con SQL PASS según esta
evidencia. Las frases anteriores conservan la cronología, no solicitan repetir el gate.
Ver [contraste con última sesión y próximos pasos](../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md).

## Recursos y límites

El contenedor preservado es `h3req1-c03-safe-suspend-pg17-20261005`, ID
`88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d`, imagen
`postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
La inspección fue read-only: `network=none`, sin port bindings, tmpfs de 1 GiB en
`/var/lib/postgresql/data`; los tres mounts `/candidate/tests/sql`, `/candidate/db/migrations`
y `/candidate/db/rollback` siguen `RW=false`. Se preserva sin conexión, cambios ni cleanup.

La UAT Pages/workerd existente valida middleware, cookies y rutas públicas; la UAT Edge
usa un cliente de fixture. El JIT v3 ya valida captura/resume persistente en PG17 local,
pero no combina los runtimes ni prueba orden/rollback cruzado. El nuevo PG17 queda
preservado; la base anterior tampoco se reutiliza.

## Decisión y permisos pendientes

El responsable eligió **captura ACL persistente** para preparar la recuperación local.
El diseño que se someterá a revisión debe guardar la captura de forma privada y duradera
antes de suspender; limitarla a firmas/roles allowlisted y una huella esperada; restaurar
solo si identidad del entorno, captura y huella coinciden; y fallar cerrado manteniendo
Pages/Edge suspendidos ante cualquier drift. La captura debe sobrevivir a una sesión
`psql`/proceso interrumpido. El orden previsto es verificar SQL/datos/auditoría, recuperar
SQL, habilitar Edge y habilitar Pages al final, con smoke controlado. Esta elección no
aprueba un mecanismo remoto ni un plazo/SLA.

El responsable autorizó y completó la autoría local acotada. Después aprobó el JIT v3
exacto y envió `continua`; se ejecutó solo el PG17 descartable nuevo. El snapshot privado,
la comprobación de identidad/ACL, rechazo ante drift, finalizadores in-flight, reconexión y
resume idempotente pasaron en el harness C03. El PG17 previo no se usó.

Siguiente autorización concreta: un JIT independiente para el drill integrado
Pages/workerd + Edge + PG17, con artefactos/hashes y transiciones exactas. El PASS de este
subgate no acredita rollback cross-runtime ni cambio de flags/bindings. Operaciones remotas
y gates H3-CLOSE-01/04–08 siguen fuera. No se limpiará ninguno de los dos contenedores sin
aprobación separada. Auth/MFA histórico sigue conservado, sin reset, reinvitación ni
reenrolamiento.

## Siguiente paso

Preparar o aprobar por separado el JIT del drill integrado. Hasta entonces C03 integrado
sigue NO-GO; no avanzar a UAT final, certificación, producción ni gates remotos.

Referencias: [estado vivo](../estado_del_proyecto.md),
[plan de cierre](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[traspaso](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[evidencia del candidato](h3req1_development_candidate_cycle_2026-10-04.md),
[JIT v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md),
[safe-suspend JIT v2 histórico](../operaciones/manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md),
[propuesta JIT v3](../operaciones/manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md) y
[atestación cliente sanitizada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).
