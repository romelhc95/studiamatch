# Preparación V9 — clasificar lectura de imagen sintética

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas y gates

| Tarea | Estado | Gate |
|---|---|---|
| Preservar fallo V8 | `SYNTHETIC_IMAGE_UNAVAILABLE`, exit 1; causa no clasificada | G03/G04 abiertos |
| Corregir clasificación | stderr de una argv fija acotado en memoria; cinco categorías cerradas | Revisión y JIT nuevos pendientes |
| Revalidar V8 | Cinco pruebas V8 + nueve V9 sobre clasificación, argv fijo, límites stdout/stderr, timeout y cleanup; solo si la imagen ya está local y legible | Docker pendiente de autorización |
| Reanudar expresión | Hasta 25 probes en contenedor temporal solo si tests pasan | G04 sigue abierto |
| Cierre local | No F1/r9/copia/startup/integración en este paquete | G03–G09 abiertos |
| CI independiente | Patch aislado; validaciones Docker/publicación no ejecutadas | G10 abierto |

## Ficha de impacto

- **Causa demostrada:** el helper V8 asigna `SYNTHETIC_IMAGE_UNAVAILABLE` a cualquier resultado
  non-zero de `docker image inspect`; por eso no distingue image-not-found, acceso, Engine u
  otro error. El mismo digest tuvo un PASS histórico en V7 y un FAIL ahora; ninguno explica por
  sí solo el cambio.
- **Cambio:** herramientas diagnósticas/test-only bajo
  `tests/h3req1_docker_peer_substep_diag/`. No modifica producto, SQL, BFF, roles, MFA, gateway,
  cuotas, build de producto, secretos, ramas o remote.
- **Pruebas:** catorce casos focales combinan los cinco tests V8 que no se alcanzaron y nueve
  casos sintéticos V9 para faltante, denegación, Engine, template, fallback sanitizado, rechazo
  de argv alterado, límites stdout/stderr, timeout y cierre de streams/proceso. Corren en el
  digest existente solo después de comprobarlo localmente; no pull/build. No se ejecutaron
  Python, pytest ni Docker durante la preparación.
- **Operaciones Docker:** una lectura de imagen; después, condicionalmente, contenedor de tests y
  uno de probes. Sin socket dentro de contenedor, F1, r9 o acceso a `studiamatch-dev`. Cleanup
  fail-closed y límites heredados V8.
- **Transición/rollback:** no es cambio funcional/de DB/deploy; excluir los archivos V9 revierte
  el diagnóstico sin tocar el candidato producto ni historia.
- **No-regresión:** la matriz existente de los cuatro ajustes permanece sin defecto demostrado;
  BFF/HttpOnly, MFA, roles, gateway, cuotas y cuenta existente no cambian.

## Pines y revisión

[JIT V9](../operaciones/jit_h3req1_docker_desktop_wsl_f1_image_read_classifier_v9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-ONCE-20261009-V1`; una ejecución
agrupada pendiente de aprobación, SHA-256
`f2d19ea84397c66ab6ba2755e38b840448a8f40def796ac7895904029805d86c`. El wrapper SHA-256
`2f12d0afe106b49ed2dba68a5403783837b6883bfc329384112424a718a1e2b3` rechaza fases/códigos no
enumerados y acepta su propio `jit-preflight`; las nueve pruebas V9 cubren clasificación y
límites/argv/timeout/cleanup.

La primera revisión independiente encontró dos LOW: faltaba una allowlist cerrada de códigos
en el wrapper y pruebas de límites/argv/timeout/cleanup. Se corrigieron ambos; la segunda
revisión pidió alinear “10” con “14” en el JIT. Tras la corrección, la revisión final confirmó
sin hallazgos restantes y verificó los cinco pines fuente, test, runner, orquestador y wrapper,
además del JIT actualizado. No se ejecutaron Python, pytest ni Docker durante la preparación;
`bash -n` del wrapper y `git diff --check` dieron PASS.

G01=10/10, G02=10/10, G03–G10=0/10, total 20%, delta cero. La documentación y el paquete no
suman puntos.
