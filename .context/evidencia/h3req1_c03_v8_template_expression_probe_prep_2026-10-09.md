# Preparación V8 — aislamiento por expresión del template F1

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas y gates

| Tarea | Estado previo a invocación | Gate |
|---|---|---|
| Conservar resultado V7 | `INSPECT_TEMPLATE_EVALUATION_ERROR`, exit 1; F1/r9 no alcanzados | G03/G04 abiertos |
| Aislar el formato sin mostrar valores | Implementación de 25 probes separadas y códigos cerrados | Sintéticos V8 y un JIT nuevo pendientes |
| Proteger recursos | Imagen fijada, dos contenedores temporales `--rm`, sin pull/build/install | Docker solo tras autorización V8 |
| Continuar cierre local | Bloqueado hasta resultado y corrección demostrada | r9, copia, startup y C03 no ejecutados |
| CI Protected Workflow Integrity | Patch aislado preservado; local validation waits for Docker | G10 abierto |

## Ficha de impacto

- **Objetivo:** identificar la columna allowlisted que produce la evaluación Go-template fallida.
- **Archivos/dominios:** cuatro archivos Python nuevos y un wrapper shell bajo
  `tests/h3req1_docker_peer_substep_diag/`, más el JIT y esta evidencia. Diagnóstico/fixture
  solamente; no cambia UI, BFF, roles, MFA, gateways, cuotas, SQL o flujos de producto.
- **Consumidores:** solo el JIT V8. No cambia el formato productivo; lee la misma constante V5
  fijada por SHA y la divide por `|` en 25 columnas con nombres estáticos.
- **Preservación:** V4/V5/V6, la ejecución V7, evidencia histórica, el WIP candidato y el checkout
  original permanecen intactos. No se reejecutan V7 ni las 15 pruebas V4–V6.
- **Pruebas:** cinco pruebas sintéticas focales V8 verifican 25 columnas, forma inválida,
  clasificación de template/transporte, fallback cerrado y salida sanitizada. Se ejecutarán en
  un contenedor temporal solo si la lectura de imagen y los pins pasan.
- **Transición/rollback:** no hay cambio funcional/de DB/pipeline/deploy. Rollback del tooling
  significa excluir los archivos V8 nuevos; no altera el artefacto de producto ni evidencia.
- **Permiso:** una invocación read-only agrupada con dos contenedores temporales usando la imagen
  sintética fijada, `require_escalated`, romel no-root en Ubuntu WSL interactiva. No habilita F1,
  r9, copia, Pages/workerd ni C03.
- **Desconocido:** si cada columna aislada pasa, V8 no atribuye el error agregado a una columna;
  informará `ALL_FIELDS_OK` como dato parcial, no como PASS del formato completo.

## Paquete y revisión

JIT: [V8 template expression isolation](../operaciones/jit_h3req1_docker_desktop_wsl_f1_template_expression_probe_v8_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-FIELD-ISOLATION-V8-ONCE-20261009-V1`, SHA-256
`b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`; una invocación pendiente
de aprobación.

Digests del paquete: clasificador `ef7d8bf086335b07374186043dfe74964536ca9194df773d889cd7df5f23ab72`,
tests `555b9557c6969d414412cdf4a7a68a68105c956a876eda15fe5feb72cac57ff0`, runner sintético
`e06d0490320e9a86df1a086f17040d7880a5253defeda88d25f88892cdd76c83`, helper
`498bb484854bd86d3b67d1ed3586d391cf7690b822aec7caac84c184299a9c24` y wrapper
`a82fc9102a465103f4c509288980a86ef0b294a2dcbfca8d9acd3bae15aaf9b7`.

La revisión de seguridad independiente V8 fue read-only y no encontró hallazgos. Confirmó los
digests, la correspondencia exacta de las 25 columnas, el ID del contenedor sintético, los
límites, la sanitización y la ausencia de acceso F1/r9/`studiamatch-dev`. `bash -n` del wrapper,
`git diff --check` y búsqueda de whitespace final pasaron; la búsqueda no encontró líneas con
whitespace final. No se ejecutaron tests Python ni Docker para preparar V8: sus cinco pruebas y
25 inspect read-only están dentro del JIT pendiente. El porcentaje se mantiene en 20% hasta que
se cierre un gate con evidencia runtime.

## Resultado de la invocación aprobada — 2026-10-09

El JIT V8 se ejecutó una vez y quedó consumido. Salida sanitizada: endpoint previamente
atestiguado `OK`; `synthetic-image-read|SYNTHETIC_IMAGE_UNAVAILABLE`, exit 1. El helper mapea
cualquier `docker image inspect` non-zero a ese código, así que la causa subyacente no está
clasificada. Se detuvo antes de los cinco sintéticos, el contenedor probe, las 25 expresiones,
F1 y r9. No hubo pull, build, install, retry, cambio Docker ni acceso a `studiamatch-dev`.
V7 había leído el mismo digest sintético `OK`, un resultado histórico no reutilizable. Ver
[resultado conservado](h3req1_c03_v8_synthetic_image_read_failure_2026-10-09.md).
