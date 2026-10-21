# Preparación V10 — aislar expresiones de imagen antes de probes

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Bloqueo demostrado y trabajo acotado

V9 clasificó `IMAGE_INSPECT_TEMPLATE_ERROR` en el template combinado de imagen y se detuvo antes
de las pruebas, el contenedor temporal y los 25 probes. No se infiere causa del Engine. V10 separa
las dos expresiones fijadas (`{{.Id}}`, `{{json .Config.Volumes}}`) y conserva stop-on-failure.

| Tarea | Predicado | Gate actual/siguiente |
|---|---|---|
| Validar `.Id` sin concatenación | ID igual al digest sintético fijado | Docker pendiente de nueva aprobación |
| Revalidar clasificadores | 17 casos exactos: 5 V8 + 9 V9 + 3 V10, sin skips | Solo después de ID PASS |
| Validar `Config.Volumes` aislado | ``, `null` o `{}`; stderr clasificado | Solo después de 17/17 PASS |
| Reanudar probes de contenedor | Hasta 25 expresiones V8, stdout descartado y errores cerrados | Solo después de ambos campos PASS; cleanup fail-closed |
| Producto/F1/r9/copia/startup/C03 | Fuera de este JIT | Continúan bloqueados |

## Ficha de impacto

- **Archivos/domino:** helper parser, pruebas y runner en
  `tests/h3req1_docker_peer_substep_diag/`; solo tooling de diagnóstico.
- **Consumidores:** orquestador V10 y wrapper WSL que exponen fases/códigos sanitizados. No cambia
  BFF/HttpOnly, roles, MFA, gateway, cuotas, UI, SQL, APIs de producto, CI ni secretos.
- **Contrato y transición:** ningún contrato funcional/DB/deploy cambia; no aplica
  `expand -> compatibilidad -> deploy -> contract`. Rollback: excluir archivos V10 sin tocar WIP,
  evidencia histórica o checkout original.
- **Pruebas preparadas:** parser V10 cubre digest exacto, valores sin volúmenes y metadata no ASCII;
  runner exige exactamente 17 casos V8/V9/V10 sin skips. No se ejecutaron Python, pytest ni Docker.
- **Operaciones:** dos lecturas `image inspect` con argv separado y límites de salida/tiempo;
  luego, condicionalmente, un contenedor efímero de pruebas y un contenedor de probes con el digest
  local fijado, `--pull=never`, red desactivada, usuario/capabilities/resources acotados y cleanup.
  Sin F1, r9, `studiamatch-dev`, pull/build/install/retry ni configuración Docker.
- **Evidencia preservada:** V8 genérico y V9 template error, junto con los JIT originales y el
  resultado del dispatch errado de Codex, permanecen sin editar.

## Pines y revisión

[JIT V10](../operaciones/jit_h3req1_docker_desktop_wsl_f1_image_template_field_isolation_v10_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-TEMPLATE-FIELD-ISOLATION-V10-ONCE-20261009-V1`, SHA-256
`08ced8865cffae2c46319897c98d368f45621dbe6650ff445ab701d55f546d7c`. La revisión independiente
final confirmó los seis hashes y los pines V8/V9/evidencia/JIT/dispatch; no encontró hallazgos.
También confirmó que un `SystemExit` por falla de ID ocurre antes de crear contenedores, y uno por
Volumes ocurre antes del contenedor de probes, por lo que esos stops no dejan recursos sin cleanup.
`bash -n` de wrapper/JIT y `git diff --check` PASS. Solo queda la autorización humana.

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta cero. No se suma porcentaje por
documentación, pruebas preparadas o clasificación parcial. No hay `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`.
