# H3REQ1 C03 — V5 nil-safe no resolvió la evaluación del template F1

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización e invocación consumida

El usuario aprobó una sola ejecución del JIT
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-NIL-SAFE-V5-R9-ONCE-20261009-V1`, SHA-256
`72d1c46aaa5c615d23308e605e8ad95edd8f8c39b2b0796ef171c355c7c8b316`. Se ejecutó como
`romel` no-root en Ubuntu WSL interactiva, con `require_escalated`, sin `sudo`.

Salida sanitaria observada:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
```

El runner devolvió exit 1; la pausa del mismo proceso se cerró con Enter. El predicado
`f1-container-read=OK` no se cumplió. La colección y los 11 casos sintéticos V5 pasaron; la
imagen sintética y la imagen F1 allowlisted también pasaron sus lecturas. El stop-on-failure
detuvo r9 antes de su preflight y contenedor de prueba. La autorización quedó consumida.

## Alcance y límites

Solo ocurrieron: inspect read-only de la imagen sintética fijada, un contenedor temporal
`--rm` para los sintéticos, lectura allowlisted de imagen F1 y una lectura allowlisted de
contenedor F1. No hubo retry, pull, build, instalación, cambio de daemon/configuración/imagen,
acceso o modificación de `studiamatch-dev`, copia, Pages/workerd, integración C03, SQL, remoto
ni Cloudflare.

## Diagnóstico demostrado

El formato V5 protegió con `with` los tres accesos a `Config.Labels` y el acceso a
`HostConfig.Tmpfs`; conservó el orden de 25 campos. El parser estricto y los casos fail-closed
de labels/Tmpfs faltantes pasaron en los sintéticos. Aun así, la única salida runtime de la
lectura F1 fue `INSPECT_TEMPLATE_EVALUATION_ERROR`. La salida sanitizada no identifica la
expresión evaluada ni permite afirmar que falte metadata. La hipótesis de que un mapa nil en
los cuatro accesos originales fuera la causa queda insuficiente para explicar el resultado; no
se atribuye la falla a Docker ni se modifica el formato por una causa no localizada.

## Siguiente trabajo antes de otra invocación

Revisar estáticamente todas las expresiones del formato y el clasificador de error. Preparar
una prueba sintética de integración que aplique el formato exacto a metadata controlada de un
contenedor temporal, verifique los 25 campos y los casos de mapas ausentes, y sanitice cualquier
fallo sin incluir texto de Engine. Revisión independiente y prueba mínima de esa preparación
antes de presentar un JIT nuevo. No se repite la lectura F1 ni se ejecuta r9 sin una nueva
autorización concreta.

## Gates y parciales

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta 0; D01–D14=0/14. Parciales separados:
atestación endpoint/identidad previa PASS; sintéticos V5 11/11 PASS; inspect de imagen
sintética PASS; lectura imagen F1 PASS; lectura contenedor F1 FAIL; r9 no alcanzado. No hay
`GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
