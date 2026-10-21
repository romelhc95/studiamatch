# G07 R15 — Miniflare compatible con el host Admin sintético

## Tareas concretas y gates

1. Preservar R14 y reproducir el `TypeError` en un Worker sintético: PASS; causa de R14 localizada en el constructor de Request de Miniflare.
2. Declarar la ruta local Admin y usar Request/Headers compatibles: implementado.
3. Bash, ShellCheck, manifiesto 65/65 y suite contractual: PASS.
4. Ejecutar el flujo Pages/workerd + Edge + PG17 + PostgREST desde el login: pendiente.
5. Completar suspensión coordinada, conservación de datos/auditoría/publicación/último admin, drift, resume y recuperación: solo si las etapas previas pasan.

## Ficha de impacto

- Componente: adaptador del test integrado Miniflare en `tests/h3req1_c03_integrated_runtime.mjs`.
- Consumidores: runner integrado R15 y pruebas contractuales R15.
- Contrato: la solicitud de test conserva URL y Origin same-origin que valida el BFF; se permite el hostname sintético exacto `admin.local.test` en Miniflare. BFF, Edge, Auth fixtures, sesiones HttpOnly y código de producto permanecen sin cambios.
- Evidencia preservada: R13 403, R14 TypeError y todos los artefactos R14. El manifest R14 archivado mantiene los hashes previos.
- Coverage a renovar: G07 integrada por cambio del adaptador y su route map.
- Recuperación: resources nuevos R15, con labels de JIT/manifiesto/nonce; stop-on-failure se limita a resources propios. Las imágenes, volúmenes de dependencias y contenedores históricos quedan fuera de limpieza global.

## Preflight R15

- Manifiesto: `tests/h3req1-c03-integrated.sha256`, SHA-256 `bbe4a9c0f39fc2e066bb19d0f3bc6f0413ee7d5e5913b2b4a2c959be1512624d`, 65/65.
- Runner: `tests/h3req1_c03_integrated_drill_r15.sh`, SHA-256 `a7d35e173bf0d4d955fe3f6a23d89894148be60cb5249806053bad3a722106ce`.
- Suite: `tests/h3req1_c03_integrated_drill_r15_contract.test.mjs`, SHA-256 `92bb4113b344f1e57560f3ccc389a71cdef162e2b948c69b056da965952f32ab`, 16/16.
- Runtime: `tests/h3req1_c03_integrated_runtime.mjs`, SHA-256 `fefa397430c87b4ffbfd64602cb282093b9f505a5d92dfd9487d2f2950999afd`.
- Bash syntax, ShellCheck 0.11.0, Node contract and focused review of the narrow code delta passed. R14 diagnostics and R15 static results are separately linked in the state file after runtime.
- Runtime command bounded at 1800 s; images pinned and local (`--pull=never`), internal Docker networks, PGDATA tmpfs, dependency caches read-only, source snapshot exact; no cloud services, operational `.env*`, egress, or real accounts.

The next action is one integrated R15 execution using JIT identifier `H3-CLOSE-03-INTEGRATED-2026-10-10-R15` and the exact manifest digest above. A failure stops the dependent C03 stages and is diagnosed from safe phase/code output; no unchanged retry.
