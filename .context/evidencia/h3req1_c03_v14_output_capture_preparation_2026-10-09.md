# Preparación V14 — captura de fases sanitizadas y gate F1/r9

Fecha: 2026-10-09. Estado: preparación estática y fixtures PASS; revisión independiente final sin hallazgos. Requiere aprobación JIT nueva.

JIT V14 SHA-256: `60ba16f2b29919ef89869625360416cb87470a7e4ad374f7c1d4b763d9686f48`.

## Resultado que motiva el ajuste

V13 terminó con `phase=f1-v11-output|error_code=OUTPUT_REJECTED`, exit 1. El wrapper no conservó las fases internas, por lo que no distingue el máximo de 2048 bytes de una línea no permitida. r9 no se ejecutó. No puede inferirse si F1 fue leído ni si la limpieza de posibles temporales tuvo éxito. La evidencia sanitizada queda en [resultado V13](h3req1_c03_v13_output_rejected_2026-10-09.md).

## Ficha de impacto

| Campo | Valor |
|---|---|
| Candidato | `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP actual | 54 tracked modificados, 226 entradas untracked de `git status --short`, 0 staged; checkout original conservado |
| Archivos propios | Helper V14 de auditoría limitada y wrapper V14 de captura; sin cambios funcionales |
| Comportamiento preservado | V13 conserva la clasificación de tres claves H3, siete fixtures, smokes, F1 allowlisted y gating de r9 |
| Causa del rechazo V13 | No determinada: la evidencia no distingue límite de 2048 bytes de línea no permitida |
| Ajuste preparado | Captura y valida hasta 8192 bytes; conserva fases sanitizadas previas al rechazo para distinguir ambas causas |
| Riesgo contenido | Revisa solo el prefijo reservado a temporales V12; ante cualquier residual detiene sin inspect ni cleanup |
| G03/G04 / total | 0/10 y 0/10; G01/G02 10/10; G05–G10 0/10; total 20%, delta 0; D01–D14 0/14 |

## Corrección y gates

V14 ejecuta las fuentes fijadas bajo timeout, captura su stdout en memoria y valida que no exceda 8192 bytes bajo `LC_ALL=C`. Conserva solo las fases válidas previas a una línea rechazada y emite `OUTPUT_LIMIT` si rebasa ese máximo. La comprobación ocurre después de la captura, no limita el stream durante la escritura; las fuentes están fijadas y sus comandos Docker tienen salidas individuales acotadas. Todo output inesperado, incluido un proceso con status 0, detiene antes de r9 con exit no-cero.

Antes de crear smokes, V14 cuenta únicamente si hay IDs devueltos por `docker container ls --all --quiet --filter name=^/h3req1-v12-template-`. No imprime ni persiste los IDs. Si existe al menos uno, informa presencia y se detiene; no limpia recursos. Después reusa el helper V13 fijado y los límites de una lectura de labels sintéticos, máximo dos smokes temporales, una lectura F1 de imagen y otra de contenedor; r9 requiere PASS exacto.

El resultado V13 no permite saber si alcanzó F1, por tanto la nueva autorización puede incluir una lectura F1 repetida. La repetición potencial queda expresamente descrita en el [JIT V14](../operaciones/jit_h3req1_docker_desktop_wsl_f1_v14_output_capture_then_r9_once_2026-10-09.md); no es un retry automático.

## Preparación y revisión

El modo `--synthetic-only` de V14 invoca los siete fixtures puros V13 y no carga Docker. Resultado: siete fases `OK`, exit 0. Compilación Python en memoria y `bash -n` PASS. No se ejecutó Docker en la preparación. Revisión independiente final: sin hallazgos en los dos archivos V14; confirmó pins, captura/filtrado sanitizado, fail-closed, auditoría read-only del prefijo y orden de gates. La revisión no ejecutó Docker ni pruebas.

Nota de revisión: el tamaño máximo se comprueba después de capturar stdout en memoria. No se imprime ni persiste salida cruda; el timeout y los límites de salida de los comandos fijados acotan la fuente. Este detalle queda dentro del alcance de la aprobación JIT.

El bootstrap CI Protected Workflow Integrity V3 permanece aislado en su patch SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. Su validación en Docker,
publicación, integración y required status siguen pendientes de sus gates; V14 no cambia alcance CI.

## Sin cambios de alcance

No se usa sudo, `/proc` del motor, pull/build/install, retry, alteración de Docker, DB/SQL/Supabase,
Auth/correo, Git remoto, GitHub, Cloudflare, PR, merge, ramas protegidas o deploy. Se conservan
BFF/HttpOnly, MFA, roles, gateway, cuotas y cuenta existente. No se infiere HIGH actual del informe
histórico de sessionStorage. Sin `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
