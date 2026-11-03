# Evidencia del ciclo local iterativo H3REQ1 — 2026-10-08

## Autorización y alcance consumido

Se ejecutó el paquete congelado
[`H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1`](../operaciones/h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md), SHA-256
`4b2649342395f8bb14fb43958d660d3588f1f6ca55bce4a6516858b395cfb4f8`, con aprobación
explícita de A/B/C, excepción iterativa y los dos riesgos MEDIUM de A.

La rama/candidato fue `feat/h3req1-sync-20261002`, HEAD base
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Se preservó el WIP previo. No se modificó
código de producto, SQL, configuración de runtime ni workflows. El runner generó el
registro F2d; después se agregó esta evidencia y se actualizaron las notas Obsidian de
estado/trazabilidad.

## A — F2d de identidad del daemon

El JIT F2d exacto (`deb429e38070174b7f179ed2c178bf4c5598ef04c0de4b92ba2f87d624b54078`)
se consumió una sola vez. Runner: `23f860e5582f1fefd96b2ccc4cf1b70e782e0d1a70ab72b630115fdf36c7964c`;
manifiesto de entradas 17/17: `18101dd492dd894d5c5692c204f1a47d3727fb609f75b83ffdbc854bcf0f657a`.

Resultado: **NO-GO**, exit 1, `daemon-proof=NO-GO|reason=direct-peer-credentials-unavailable|api-requests=0`.
El endpoint Unix local y la ruta canónica se comprobaron, pero `SO_PEERCRED` no acreditó
la identidad del peer. El registro descarta metadata cruda, conserva F1 y confirma cero
mutaciones, cero limpieza y cero retries. No se leyó F1, no se ejecutó r9 ni se llamó la
Docker API. Ver [resultado F2d](h3req1_c03_f1_daemon_diagnostic_f2d_2026-10-08.md).

La aprobación cubrió para esta única invocación los dos residuales definidos por el JIT:
metadata no seleccionada del `inspect` completa podría vivir transitoriamente en memoria
de Docker CLI; y el mismo usuario local puede invocar Docker fuera del runner/JIT. El riesgo
del `inspect` no se materializó porque la condición de identidad cerró antes de Docker API.
La aceptación no autoriza otra invocación ni modifica el resultado NO-GO.

## B y C — parada por dependencia y lecturas GitHub

F2d era una condición previa obligatoria para toda operación dependiente del daemon. Al
fallar, no se ejecutaron linters, pruebas, UAT, harnesses SQL, PG17, snapshot, smoke,
integración C03 ni otras fases Docker. No se tocaron `.env*`, `web/out` ni contenidos de
`tests/h3req1-c03-bootstrap/node_modules/.deno`. No se aplicó ningún cambio de código.

El bloque GitHub C fue de solo lectura, contra `romelhc95/studiamatch`, dentro del límite
de 30 llamadas y sin reintentar respuestas fallidas. `desarrollo`, `certificacion` y `main`
aparecen protegidas. El ruleset visible `owner-only-protected-branch-updates` restringe
updates, pero la consulta de branch protection devolvió 403 (`Resource not accessible by
integration`). Por ello, required checks y reviews son **desconocidos**, no ausentes ni
PASS. Los checks/run successes visibles corresponden al 2026-09-27 y no demuestran
enforcement efectivo para el WIP actual. No hubo escrituras remotas.

## Revisión de seguridad estática

Codex Security completó el diff scan `f949b9d1-ed8d-4510-9de5-746a1cd10042` para el
snapshot `codex-security-snapshot/v1:sha256:b81eab7ecb0248b40b98391c9a4001f581b562f8a22deb445ae029dc7d5b4663`:
51/51 filas revisadas, **cero hallazgos reportables confirmados**, cobertura estática
parcial. Dos candidatos quedaron diferidos:

1. El reset de `mock-server/server.js` podría borrar eventos si una configuración de
   prueba apunta a una base remota bajo el prefijo admitido y se presenta el token de reset.
   No se verificó que exista esa combinación.
2. No se pudo probar si `Protected Workflow Integrity` es un required check independiente
   en las tres ramas; GitHub devolvió 403.

También queda sin verificar la configuración Supabase de `pgrst.db_pre_request` y la
adopción de bindings/secretos Cloudflare. El análisis es estático y no sustituye runtime.
El informe sellado `report.md` está asociado al scanId indicado arriba.

## Desviación de acceso y estado de cierre

Una enumeración amplia anterior de `git status` mostró nombres de rutas dentro de la ruta
prohibida `.deno`. No se leyeron contenidos ni se calcularon hashes allí; no hubo más
acceso. La limitación queda registrada en el informe del scan.

G01 y G02 conservan 10 puntos cada uno; G03–G10 permanecen en cero. Total: **20%**.
D01–D14: **0/14**. `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` y cierre global: **NO-GO**.

Transición: `expand` conserva el estado/código existente y agrega trazabilidad; la fase de
compatibilidad mantiene el contrato legacy ya vigente; `deploy` no se ejecutó;
`contract` y rollback funcional no se ejecutaron. Rollback de este ciclo: retirar solo
esta nota y sus enlaces si se invalida el registro documental.

## Dependencias concretas para reanudar

- Un método/endpoint local con aprobación nueva que pruebe identidad del daemon sin repetir
  el F2d consumido. Hasta entonces no se ejecutan fases Docker, F1 ni r9.
- Evidencia administrativa sanitizada de required checks/reviews efectivos para las tres
  ramas protegidas; el conector de lectura no tiene permiso para obtenerla.
- La adopción de `pgrst.db_pre_request`, claves y bindings sigue siendo un gate runtime
  posterior y conserva su JIT independiente.
