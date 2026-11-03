# Evidencia — continuación de readiness H3REQ1

**Fecha:** 2026-10-03 UTC  
**Estado:** `NO-GO_H3REQ1_DEVELOPMENT_FREE`  
**Objetivo:** preparar readiness local para el PR funcional H3REQ1 e inicio de pruebas
remotas Development. No declara aceptación remota ni GO de Certificación/Producción.

La matriz fijada por el responsable es la del
[plan integral](../operaciones/plan_go_h3req1_local_development_2026-10-02.md). Esta
evidencia conserva los resultados de este ciclo y no sustituye UAT final sobre el
candidato congelado.

## Baseline y WIP

- Rama: `feat/h3req1-sync-20261002`.
- `HEAD`: `4eb4d877a50b012bb630a129bd0c74482c33be9c` (baseline, no identifica el WIP).
- Estado al corte documental: 40 rutas tracked modificadas, 46 untracked, 0 staged.
  Las rutas nuevas de este ciclo incluyen la captura read-only de reglas GitHub, el
  README/tarball de procedencia `braces` y esta evidencia.
- No se generó hash integral del candidato ni se hizo commit.
- Los dos artefactos literales de plantilla permanecen en 0 bytes, intactos y
  excluidos del candidato. La captura `.openchamber/screenshots/` es evidencia de
  consulta, no archivo funcional del PR.

## Decisiones humanas registradas

- Matriz única confirmada; no agregar alcance fuera de requisitos, atestación y seis
  pilares vinculantes.
- Aprobado integrar localmente un snapshot fijado del arreglo `braces` upstream.
  Responsable y fecha de revisión/vencimiento del seguimiento no quedaron confirmados.
- Aprobado diseño/implementación local de gateway firmado para RPC Admin directas,
  preservando JWT de usuario, `auth.uid()`, RLS, RBAC y MFA. No es aprobación de DDL,
  grants, secretos, bindings ni operaciones remotas.
- Autorizada lectura GitHub de protecciones/checks/colaboradores, no modificaciones.

## Tooling — snapshot `braces`

Origen fijado: [`micromatch/braces` PR #72](https://github.com/micromatch/braces/pull/72),
commit `28d440b5dd449dbf1fe6f3506cf94ecca4d02660` (`FSDevelop/braces`). El PR está
abierto y no se presenta como release oficial. El paquete local se identifica como
`3.0.4-h3.1` para distinguirlo del upstream; conserva licencia MIT.

| Artefacto | SHA-256 |
|---|---|
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| `web/vendor/README.md` | `4e7f2700dcc37fe9db4b4fb3834ff7d4a4764e0f9ed3b8ea330e202d1b2ae62d` |
| `web/vendor/braces-3.0.4-h3.1.tgz` | `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819` |

Validación en copia limpia Docker `/tmp/h3req1-deps-pinned-20261003-r1/web`:

- `npm ci --prefer-offline`: PASS; árbol resuelve `braces@3.0.4-h3.1` para
  `micromatch@4.0.8` / `fast-glob@3.3.3`.
- `npm audit --include=dev` y `npm audit --omit=dev`: **0 vulnerabilidades**.
- Suite del snapshot upstream: **904 passing**.
- ESLint: 0 errores, 9 warnings históricos. TypeScript y `next build`: PASS.
- Export: 151/151 archivos iguales byte a byte a la referencia de dependencia; tamaño
  2,655,865 bytes. SHA-256 del manifiesto ordenado `path + SHA-256 por archivo`:
  `24dcbdb550307b3fa7634353577dd094c17e7bf0d4a7b19ff999491aeeeb884d`.
- No hubo `npm audit fix` ni se usó una release publicada inexistente.

El snapshot elimina el advisory en la resolución auditada, pero sigue requiriendo
seguimiento de mantenimiento porque procede de un PR no mergeado. El owner y fecha de
revisión no están aprobados; la decisión queda abierta y no se oculta como waiver.

## Calidad y evidencias UAT

Sobre el WIP: pytest **283 passed, 4 skipped**, 1 warning de deprecación `PyPDF2`;
los cuatro skips son tests opt-in que requieren `RUN_SUPABASE_INTEGRATION_TESTS=1` y
conexión live Supabase, excluida de este alcance. ESLint: 0 errores/9 warnings
existentes. TypeScript, `actionlint`, `shellcheck`, credential scan sobre tracked y
untracked (excepto archivos binarios/lock), y `git diff --check`: PASS.

### Causa, riesgo y owner de warnings/skips

- **ESLint, 7 `react-hooks/exhaustive-deps`:** `HomeContent.tsx` memoiza facetas usando
  `getFilteredExcluding`, función recreada en cada render. En particular, las facetas
  `activeInstitutions` y `activeModes` omiten `activeFilters.priceMin` de sus arrays
  de dependencias (líneas 165 y 171), aunque el filtro usa ese valor. Si cambia el
  precio mínimo, pueden quedar opciones de faceta desactualizadas. `HomeContent.tsx`
  no fue modificado por H3; no se amplió el PR sin decisión. **Riesgo:** defecto previo
  de filtrado público, separado de aceptación H3. **Owner:** no asignado; requiere
  decisión del responsable antes de cerrar el pilar de calidad.
- **ESLint, 2 `no-unused-vars`:** `_e` en catches de acceso/escritura de cache local
  (mismas líneas 299 y 323) no se usa; no cambia comportamiento. **Riesgo:** ruido de
  mantenimiento. **Owner:** no asignado; confirmar si se corrige en H3 o se deja como
  baseline existente.
- **Pytest, 1 `DeprecationWarning`:** la dependencia `PyPDF2` anuncia deprecación.
  **Riesgo:** mantenimiento/futura incompatibilidad, sin fallo actual. **Owner:** no
  asignado.
- **Pytest, 4 skips:** requieren credenciales/ambiente live Supabase y la opción
  `RUN_SUPABASE_INTEGRATION_TESTS=1`; no se corrieron por no usar escrituras remotas.
  **Riesgo:** no aportan aceptación remota, que es una fase posterior autorizada, no
  prerequisito circular para iniciarla. **Owner de ejecución:** operador Development,
  aún sin asignar.

Se conservan como cortes previos, no como hash final: UAT r17 **48/48 casos,
144/144 ejecuciones/capturas, 0 retries** y onboarding **10/10**, pacing mínimo
20.1 s. El build con la nueva metadata local produjo los mismos 151 assets. La
integración del gateway y cualquier cambio funcional posterior exigirán repetir las
validaciones afectadas, incluida UAT sobre el artefacto candidato exacto.

## Cuotas — contrato escogido y límite de ejecución

El responsable eligió el camino de gateway firmado. La dirección de diseño local es:

1. El BFF verifica la sesión y admite cada RPC a través del Durable Object antes de
   llamar a PostgREST; el rechazo por límite o falla del contador es 429/503 y no
   llega a la RPC.
2. Un verificador `db_pre_request` en la Data API exige una firma temporal allowlisted
   para `/rest/v1/rpc/admin_*`; llamadas directas no firmadas fallan cerrado. Para
   peticiones BFF, el actor firmado debe coincidir con el JWT ya validado y
   `auth.uid()`. La firma no sustituye el JWT ni autorización RPC.
3. La Edge mantiene verificación de identidad, admisión independiente de
   120/actor/min antes de Auth, reserva previa al envío y finalizadores de operaciones
   ya reservadas fuera de la cuota de iniciación.

La documentación Supabase describe `db_pre_request` como gate para rate limits y
denegación de acceso directo a Data API; opera solo sobre PostgREST. El cambio requiere
función SQL, configuración `pgrst.db_pre_request`, permiso del rol `authenticator` y
pruebas PG17/PostgREST. No se creó ni ejecutó SQL, DDL, grants o writes en este corte;
el JIT específico sigue siendo requisito antes de implementarlo/probarlo.

## GitHub — lectura autorizada, controles incompletos

- API branches: `desarrollo` está protegida y apunta a
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; `certificacion` también aparece
  protegida. Colaboradores: `romelhc95` admin y `romelhc95-approver` write.
- UI Rulesets: un ruleset activo, `owner-only-protected-branch-updates`, apunta a
  `desarrollo`, `certificacion` y `main`. Solo `Restrict updates` aparece marcado;
  `romelhc95` está en bypass `Always allow`. “Require a pull request” y “Require
  status checks to pass” aparecen desmarcados en ese ruleset.
- La pantalla clásica `/settings/branches` no termina de cargar sus reglas y el REST
  `/branches/desarrollo/protection` devuelve 401 `Requires authentication`. Por eso
  no puede concluirse que no haya una regla clásica separada, pero tampoco se acredita
  PR obligatorio, revisión distinta, `security-audit` requerido ni enforcement para
  admins.
- Evidencia visual local: `.openchamber/screenshots/github-ruleset-readonly-2026-10-03T13-39-52-523.jpg`.
- No hubo configuración, commit, push, PR, review ni merge remoto. Para cerrar este
  gate se necesita export/captura sanitizada de la regla clásica y permisos efectivos,
  o un mecanismo read-only con autorización efectiva que exponga esa configuración.

## Gates aún abiertos y autorizaciones

1. Owner y fecha de revisión del snapshot `braces`.
2. JIT local exacto para autoría/ejecución SQL del gateway firmado sobre PG17
   desechable; no reutilizar el JIT del safe-suspend harness.
3. CI: required checks/reglas clásicas y secuencia bootstrap independiente; las
   escrituras GitHub requieren autorización futura separada.
4. Rollback integrado Pages + Edge + cookies + bindings + SQL; el safe-suspend SQL,
   Pages/workerd y Edge pasan solo como pruebas separadas.
5. Evaluación de seis pilares, atestación contra el candidato exacto, compatibilidad,
   hashes separados de fuentes/build/resultados, paquete PR con plantilla actualizada
   y protocolo ejecutable Development.

No hay GO para abrir el PR funcional ni iniciar UAT remota. No se realizaron acciones
remotas de escritura, operación Supabase/Cloudflare, commit, push, merge o deploy.
