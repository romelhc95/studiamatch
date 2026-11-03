# Preparación V7 — clasificación del inspect sintético F1

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Dependencia ejecutada

El JIT V6, SHA-256
`c84491eee2e23bba26be38985e4658ffe280947c43c953f232eb23699d915277`, fue aprobado y
consumido una vez. Endpoint previo, imagen sintética y 15/15 casos V4/V5/V6 dieron PASS; el
primer smoke de inspect devolvió `SYNTHETIC_TEMPLATE_RENDER_FAILED`, exit 1. Se limpió el
contenedor temporal y el stop-on-failure no alcanzó el caso sin mapas, F1 ni r9. La causa quedó
sin clasificar porque V6 descartó stderr. Evidencia: [resultado V6](h3req1_c03_v6_template_smoke_inspect_failure_2026-10-09.md).

## Corrección de preparación

V7 cambia solo tooling de diagnóstico/sintéticos: aplica `run_bounded_inspect` con captura
acotada en memoria al smoke temporal, pasa por el clasificador V6 y traduce el resultado con
una allowlist V7. Unknowns se cierran como `SYNTHETIC_TEMPLATE_INSPECT_FAILED`. Añade cuatro
casos enfocados: códigos allowlisted por campo, recorrido de stderr nil-map por V6 y V7,
fallback cerrado y propagación de errores del runner acotado. Revalida los digests V4/V5/V6
sin reejecutar esas 15 pruebas. El preflight local del helper valida todos los inputs V4–V7 y
la evidencia V6 antes de cualquier llamada Docker.

Una primera revisión independiente halló LOW bloqueante: el runner esperaba el SHA de la
versión anterior del test V7. Ese paquete no se ejecutó. Se alinearon runner, helper, wrapper y
JIT al digest del test actual y se solicitó revisión final. La revisión final no encontró
hallazgos y confirmó la cadena de hashes, errores allowlisted, cuatro casos exactos, sanitización,
cleanup y condiciones F1/r9.

## Paquete al cierre de preparación

[JIT V7](../operaciones/jit_h3req1_docker_desktop_wsl_f1_template_smoke_classified_v7_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-CLASSIFIED-V7-R9-ONCE-20261009-V1`, SHA-256
`d83ae63a49ce94be4672822758fb294c5a951af1a060ddfcb63f59d764808f2f`, está revisado y pendiente
de aprobación explícita para una sola invocación. Ejecuta como `romel` no-root en Ubuntu WSL
interactiva, sin `sudo`. Se reutiliza la atestación del endpoint; no se repite el socket. Opera
solo sobre imagen sintética fijada y dos contenedores temporales limitados; no accede a
`studiamatch-dev`, no hace pull/build/install ni cambia Docker. F1 se lee una vez y r9 corre una
vez solo tras PASS exacto. Fallo/timeout consume la invocación y detiene las etapas posteriores.
Los JIT V4/V5/V6 siguen consumidos y no se reintentan.

## Resultado posterior de la invocación V7

El usuario aprobó y consumió una sola invocación. La atestación previa, lectura de imagen
sintética, lectura de volúmenes y cuatro pruebas focales dieron `OK`. El primer smoke de inspect
terminó en `phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR`;
exit 1. No se ejecutó el smoke de mapas ausentes, F1 ni r9. La clasificación cerrada no
identificó la expresión concreta. No reintentar V7. Resultado detallado:
[evidencia V7](h3req1_c03_v7_template_smoke_evaluation_failure_2026-10-09.md).

Pines finales: helper V7 `5b5341f7775b38350197976fe3d0246702e1158ae1578a2957717f97b5f9d0c1`,
clasificador `432295368a96b7ba8329e3a83aede3bfbba872400331b19127c334d06ca3d58d`, pruebas
`548d65701def7cb7450cea1761063d992d39f2edac66d86269101cd431f52fa7`, runner
`99d1da50ead767f0fcbe2877db6df99589f64b2f8aaf7ed1ee85652174c6ede2` y wrapper
`dee832ef729287205b56bfb6e3be3f889121b9b5464166ef6b7443e97b210e96`.

## Revisión y validación realizadas

- Revisión independiente final: **sin hallazgos**. Verificó salida cerrada y sanitizada,
  secuencia exacta de 8 fases, cleanup fail-closed, recursos/tiempo limitados, pins y gates
  condicionales. No ejecutó código, pruebas ni Docker.
- Preparación estática: `bash -n`, compilación Python in-memory y revisión de whitespace:
  **PASS**. `git diff --check`: **PASS**.
- No se ejecutaron pytest V7, Docker, r9, F1, producto, SQL, runtime, actionlint ni CI.
- No se cambió producto, migración, secretos, contenedor, imágenes, configuración Docker,
  remoto, Pages, Auth ni datos. No hay cambio de porcentaje por preparación/documentación.

## Ajustes cliente, CI y gates

La [matriz de los cuatro ajustes](h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente)
se incorporó con inputs, pruebas preservables, cobertura, resultado actual y siguiente acción.
El contrato Python coincide por SHA con el manifiesto 2026-10-04; el harness PG17 actual difiere
de ese manifiesto y no permite reutilizar el C03 41/41 histórico. La evidencia del 2026-10-01
no trae digests por archivo para migration/UI/BFF/UAT. La evidencia inicial se preserva como
parcial; los casos afectados no se revalidaron en este corte. No se halló un defecto funcional
que justifique cambiar implementación.

El patch Protected Workflow Integrity conserva su SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`; su aplicación aislada y
diff-check históricos son preparación solamente. No está validado en Docker, instalado,
publicado ni requerido. Los datos conocidos de Branches, Actions y Cloudflare no se vuelven a
solicitar; falta validación local/remote autorizada y la promoción debe evitar un build/deploy de
producto incidental.

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14. Parciales de este
corte: V7 endpoint/image/image-volumes y cuatro focused tests PASS; primer smoke FAIL;
segundo smoke, F1 y r9 no alcanzados. No existe `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Estado preservado

Candidato WIP: 54 rutas tracked modificadas, 203 untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`: rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, 39 tracked, 39 untracked, 0 staged. Se preservan
ambos checkouts y sus recursos ajenos.
