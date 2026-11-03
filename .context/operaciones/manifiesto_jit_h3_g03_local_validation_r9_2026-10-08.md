# JIT propuesto — G03 local r9: linters y regresiones Docker

Fecha: 2026-10-08. Estado: **PREPARADO, NO AUTORIZADO, NO EJECUTADO**.

## Objetivo y causa del paquete

Completar el lint/typecheck y las regresiones locales del tooling H3 del candidato. La
ejecución r8 fue autorizada y consumida; descargó y verificó actionlint 1.7.7 y ShellCheck
0.11.0, pero el único contenedor terminó con exit 126 antes de leer `run-in-container.sh`.
La raíz del bind mount r8 tenía modo 0700 para UID/GID 1000 y el proceso interior era
1001:1001. r9 corrige el acceso con una copia independiente de los mismos 71 inputs y raíz
0755. No reintenta r8 ni vuelve a descargar herramientas.

## Identidad del candidato e inputs

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`; HEAD baseline:
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el WIP forma parte del candidato.
- Paquete: `/tmp/h3req1-g03-validation-29d8fff9-r2` (71 inputs source, además de sus
  manifiestos y wrapper). `inputs.sha256`:
  `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`.
- `r9-package.sha256`:
  `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`.
- Invocación fijada `run-r9.sh`:
  `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Herramientas locales ya descargadas por r8, revalidadas y copiadas sin red a
  `/tmp/h3req1-g03-validation-29d8fff9-r2.tools`. `tools.sha256`:
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
  - actionlint 1.7.7 tarball:
    `023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757`.
  - ShellCheck 0.11.0 tarball:
    `b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6`.
- Imagen local fijada: `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`;
  `--pull=never`.

## Operación exacta solicitada

Una sola invocación de hasta 180 segundos, sin retries ni continuación tras fallo:

```bash
/tmp/h3req1-g03-validation-29d8fff9-r2/run-r9.sh
```

El wrapper verifica los manifiestos y la raíz 0755, y rechaza un endpoint Docker `default`
que no sea `unix://`. Luego ejecuta un contenedor anónimo con `--rm`, red desactivada,
filesystem raíz de solo lectura, UID/GID 1001, capacidades retiradas,
`no-new-privileges`, 512 MiB, 1 CPU, 64 PIDs y tmpfs acotados. Solo monta el paquete r2 y
los tarballs fijados en solo lectura. El contenedor ejecuta `run-in-container.sh`.

Checks interiores, en orden y stop-on-failure:

1. Verificar inputs y hashes de los dos tarballs; extraer linters solo a tmpfs.
2. Confirmar Node `v20.20.2`, TypeScript `5.9.3` y que `package.json`/lock coincidan con
   el manifiesto de dependencias de la imagen.
3. actionlint en `security-audit.yml`, `protected-workflow-integrity.yml` y
   `db-sync-to-pro.yml`.
4. ShellCheck sobre los siete scripts fijados del paquete.
5. `npm run lint`, `tsc --noEmit`, pytest de `tests/test_protected_workflow_review.py`,
   `tests/test_scan_credentials.sh` y `tests/test_protected_path_scope_guard.sh`.

## Límites, fallo y recuperación

- Egress del contenedor: ninguno. No hay descargas en r9 ni instalación npm.
- No se pasan secretos/env privados, no hay DB, SQL, Auth, correo, servicios remotos ni
  socket Docker montado dentro del contenedor.
- Recurso permitido: exactamente un contenedor local fijado y efímero, retirado por su
  propio `--rm`. No limpiar ni inspeccionar recursos preexistentes.
- Timeout total 180 s; sin retry. Hash, endpoint, mount, dependencia o check que falle
  detiene la ejecución. Preservar salida sanitizada y exit code; no volver a ejecutar este
  permiso ni aumentar límites para ocultar un fallo.
- Recuperación: mantener r8 y r9 intactos, corregir en una nueva revisión de paquete y
  solicitar un JIT nuevo. No modificar archivos del candidato como parte de esta etapa.

## Prerrequisito de identidad del daemon

**No ejecutar este JIT todavía.** F2c confirmó un socket Unix local, pero no acreditó el
peer; `unix://`, `stat` o `realpath` no demuestran que el proceso sea dockerd directo. El
wrapper r9 conserva el gate de endpoint Unix, no sustituye la prueba F2d. Antes de solicitar
su aprobación, debe quedar acreditada la identidad local directa mediante F2d autorizado o
una alternativa concreta aprobada. Si aparece proxy o la identidad sigue incierta, detener
Docker y presentar la alternativa local con su JIT; no contactar un destino remoto ni
instalar/reconfigurar el engine.

La autorización r8 está consumida. Este manifiesto no hereda ni amplía aprobaciones de
r4–r8; su ejecución requiere aprobación humana nueva después de satisfacer el prerrequisito
anterior.
