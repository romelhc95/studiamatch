# Revalidación de hashes preservados H3REQ1 — 2026-10-08

## Alcance

Verificación de solo lectura de los inputs de C02 v4 y C03 SQL v3 requeridos por el
prompt vigente. Se preservaron los resultados y recursos históricos. No se ejecutaron
tests, SQL, Docker, servicios remotos ni acciones Git remotas; no se consumió JIT.

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`  
Rama: `feat/h3req1-sync-20261002`  
Baseline HEAD: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Primera revalidación — antes de la guardia HMAC del BFF

| Conjunto | Resultado del recálculo | Alcance y lectura |
|---|---:|---|
| C02 v4 no-C03 | **71/72 coinciden** | El único delta es `.github/workflows/security-audit.yml`. Los otros 71 inputs del manifiesto coinciden, incluidos los dos hashes aceptados por v4 para el wrapper payload-bound y su harness. |
| C03 SQL v3 | **41/41 coinciden** | Se conserva el PASS SQL v3 para sus inputs exactos. No se repitió SQL. |

Para C02 se leyeron las 74 filas del manifiesto base y se excluyeron sus dos inputs
propios de C03 (`db/rollback/h3req1_safe_suspend.sql` y
`tests/sql/h3_safe_suspend_harness.sql`). Los dos cambios permitidos por v4 se verificaron
con los hashes actuales documentados en el manifiesto v4. La única diferencia entre los
72 inputs restantes fue el workflow.

El workflow esperado en el manifiesto base tiene SHA-256
`1221ecc16a46f5f6d617deeb86d523033a2dc927985dea285c0631869b5b0b72`; el archivo actual
tiene `b285eb4988914df0b3fa9e742d1308c1b8874813cb512d36557cd0953f9f9ce8`. Por tanto,
**no se afirma que el conjunto C02 no-C03 completo siga idéntico**. Este cambio de CI no
modifica las migraciones ni harnesses runtime que pasaron C02; sus resultados permanecen
históricos para los bytes exactos ejecutados. El workflow y el enforcement CI siguen siendo
gates separados, sin validación Docker ni lectura de configuración remota en este corte.

## Método reproducible y límites

- Se recalcularon SHA-256 directamente en el worktree para las 72 rutas C02 no-C03 y las
  41 rutas del cierre transitivo C03 v3. La comparación se registró en temporales propios
  bajo `/tmp`, eliminados al finalizar.
- C02: `sha256sum -c` reportó 71 `OK`, 1 `FAILED` (`.github/workflows/security-audit.yml`).
- C03: `sha256sum -c` reportó 41 `OK`, 0 `FAILED`.
- `git diff --check` no reportó errores de whitespace. No valida YAML, shell ni runtime.
- Sin Docker, suites, SQL, writers, Auth, Supabase/Cloudflare, CI remoto, push, PR o merge.

## Disposición

Mantener C02 v4 como evidencia histórica de SQL/PostgREST/cuotas/gateway/replay/concurrencia
para los inputs runtime que coinciden; actualizar la afirmación de identidad actual de C02
a 71/72 por el workflow. No repetir las suites SQL/wire por este cambio aislado. Validar
el workflow y los controles de seguridad afectados dentro de Docker antes de GO_LOCAL_PR;
la efectividad remota requiere su lectura/configuración aprobada por separado. C03 SQL v3
permanece vigente por hash; C03 integrado sigue pendiente.

## Revalidación posterior al cambio BFF — 2026-10-08

Se volvió a calcular el cierre de C02 v4 sin ejecutar suites. Para C02 no-C03 se
compararon las 72 rutas: 55 SQL/harness (excluidos los dos inputs propios de C03) y
17 archivos del contrato de runners. Se aplicaron solo las dos sustituciones ya aceptadas
por v4 para el wrapper payload-bound y su harness. Resultado: **70/72 coinciden**. Los
dos deltas actuales son:

| Ruta | Hash esperado/aceptado | Hash actual | Disposición |
|---|---|---|---|
| `.github/workflows/security-audit.yml` | `1221ecc16a46f5f6d617deeb86d523033a2dc927985dea285c0631869b5b0b72` | `b285eb4988914df0b3fa9e742d1308c1b8874813cb512d36557cd0953f9f9ce8` | Cambio de workflow/CI ya pendiente de validar en Docker y remotamente |
| `web/functions/_lib/admin-bff.ts` | `1cb1ad95d723e884f58cf98dd5b2600e59fa8230aa044cb25e6ebb41f1db7ed7` | `829cd9cdce85f318800674949a7b6f93f64f8283d3c217f453ab3c75361827cf` | Guard fail-closed para HMAC iguales; ejecutar UAT sintética del BFF en Docker |

C03 SQL v3 se recalculó directamente contra las 41 filas de su cierre transitivo:
**41/41 coinciden**. No se ejecutó SQL. Los resultados SQL/PostgREST históricos se
preservan para sus bytes y contratos; la cobertura del BFF y del workflow exige sus
checks afectados antes de cerrar el candidato. No se repiten las suites SQL/wire intactas.
