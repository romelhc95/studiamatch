# Resultado JIT V8 — lectura de imagen sintética no clasificada

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocación y salida

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-FIELD-ISOLATION-V8-ONCE-20261009-V1`, JIT
SHA-256 `b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`. El wrapper estaba
fijado a SHA-256 `a82fc9102a465103f4c509288980a86ef0b294a2dcbfca8d9acd3bae15aaf9b7`; el
preflight lo aceptó. Se ejecutó una vez con `require_escalated`, como `romel` no-root en
Ubuntu WSL interactiva y sin `sudo`.

Salida sanitizada:

```text
phase=prior-endpoint-attestation|error_code=OK
phase=synthetic-image-read|error_code=SYNTHETIC_IMAGE_UNAVAILABLE
```

Exit del runner: `1`. La invocación se consumió.

## Diagnóstico y límite

El predicado fallido fue la lectura read-only `docker image inspect` de la imagen sintética
fijada: no entregó el ID/dato de volúmenes esperado. El helper configura el código
`SYNTHETIC_IMAGE_UNAVAILABLE` para cualquier salida no-cero de esa lectura en
[`f1_template_expression_probe_v8_once.py`](../../tests/h3req1_docker_peer_substep_diag/f1_template_expression_probe_v8_once.py).
Por ello la evidencia no distingue entre imagen local ausente, denegación de lectura, error
del Engine u otra respuesta no-cero. No se afirma que la imagen esté ausente ni que Docker sea
defectuoso. La fase de atestación previa fue aceptada, pero no clasifica este error posterior.

El runner V7 referencia el mismo digest sintético y su salida histórica tuvo lecturas de
imagen/volúmenes `OK`. Ese resultado no se reutiliza como PASS runtime actual; el nuevo non-zero
solo demuestra que esta invocación no obtuvo el dato esperado. No identifica si cambió la
disponibilidad, el contexto del endpoint, los permisos u otra condición.

El stop-on-failure detuvo la ejecución antes de los cinco sintéticos V8, del contenedor de
probes y de las 25 expresiones. No se leyó F1; r9, copia, Pages/workerd, integración C03 y
aceptación no se ejecutaron. No hubo pull, build, install, retry, cambio de Docker ni acceso a
`studiamatch-dev`; al fallar antes de crear contenedor de prueba no había contenedor temporal
que limpiar.

## Corrección y siguiente acción

La brecha demostrada está en la clasificación de errores de la lectura de imagen, no en el
template ni en producto. Preparar un clasificador cerrado con pruebas sintéticas para separar
imagen inexistente, acceso denegado, Engine no disponible y fallo no reconocido; descartar el
stderr crudo y no exponer metadata. Después de revisión y verificación de pins se requiere una
nueva autorización antes de cualquier nueva lectura Docker. No repetir V8.

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta cero. Los gates y los parciales previos
permanecen separados. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
