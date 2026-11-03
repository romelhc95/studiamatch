# H3REQ1 C03 — V6 smoke sintético no pudo renderizar el formato F1

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocación consumida

El usuario aprobó una invocación del JIT
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-V6-R9-ONCE-20261009-V1`, SHA-256
`c84491eee2e23bba26be38985e4658ffe280947c43c953f232eb23699d915277`. Se ejecutó una vez con
`require_escalated` como usuario `romel` no-root en Ubuntu WSL interactiva, sin `sudo`.

Salida completa, ya sanitaria:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-unit-tests|error_code=OK
phase=f1-template-synthetic-inspect|error_code=SYNTHETIC_TEMPLATE_RENDER_FAILED
```

Exit 1. El wrapper detuvo la secuencia después de inspeccionar el primer contenedor sintético
(metadata con labels y Tmpfs presentes). El cleanup del contenedor terminó sin emitir fallo.
Los 15 casos unitarios sintéticos V4/V5/V6 pasaron antes del smoke. No se emitió el agregado
`classifier-synthetic-tests|OK` porque el smoke posterior falló. No se inició el segundo caso
de mapas ausentes, lectura F1 ni r9.

## Predicado y límites

`SYNTHETIC_TEMPLATE_RENDER_FAILED` indica que el `docker inspect --format` sintético terminó
con status no cero. V6 fijó el código de fallo de forma general y descartó stderr; por tanto la
salida no indica campo, expresión, clase del error ni metadata. No prueba un defecto de Docker,
no atribuye la falla a labels/Tmpfs y no demuestra que el template real se comporte de igual
manera. La clasificación detallada de expresiones allowlisted solo se aplicó a la lectura F1,
que no se alcanzó.

No hubo retry, pull, build, instalación, cambio Docker/daemon/configuración/imagen, acceso o
modificación de `studiamatch-dev`, F1, r9, copia, Pages/workerd, integración C03, SQL, remoto,
Cloudflare, cambios de producto ni modificación de secretos. La invocación quedó consumida.

## Siguiente corrección ejecutable

Preparar un inspector sintético acotado que capture stderr solo en memoria con límite fijo y
clasifique el error del smoke con el clasificador V6 allowlisted. Debe distinguir errores de
evaluación conocidos por expresión y mantener un código cerrado genérico para cualquier otro
caso. Incluir pruebas enfocadas nuevas sin repetir la suite V4/V5/V6 intacta; conservar su
resultado `15/15` como parcial con hashes revalidados. El siguiente JIT puede continuar a mapas
ausentes, F1 una vez y r9 solo si el smoke presente y ausente y la política F1 pasan. Se requiere
nueva aprobación porque V6 ya se consumió.

## Gates y parciales

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0; D01–D14=0/14. Parciales de esta
invocación: endpoint previo PASS; imagen sintética sin volúmenes PASS; imagen sintética PASS;
15/15 pruebas unitarias PASS; primer template smoke FAIL; mapas ausentes, F1, r9 no alcanzados.
No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
