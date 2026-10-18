# Preparación V12 — aislamiento de variante de template, F1 y r9

Fecha: 2026-10-09. Estado: JIT consumido; falló en el preflight del mapa sintético antes de crear contenedores, leer F1 o ejecutar r9. V11 permanece consumido y no se repite.

## Ficha y gates

| Elemento | Alcance y estado |
|---|---|
| Objetivo | Clasificar el smoke combinado que falló en V11; el JIT consumido se detuvo al exigir mapa completo de labels vacío. |
| Candidato | `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. |
| Cambios | Dos runners de diagnóstico bajo `tests/h3req1_docker_peer_substep_diag/`; sin cambios funcionales de producto. |
| G04 | 0/10. V11 y V12 fallaron antes de F1. |
| G03 | 0/10. Manifiestos r9 íntegros en preparación; r9 todavía no ejecutado. |
| G01/G02 | 10/10 cada uno, evidencia previa preservada. |
| Total | 20/100; delta 0. G05–G10 continúan abiertos. D01–D14: 0/14. |

## Hallazgo y corrección

V11 emitió únicamente:

```text
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
exit=1
```

F1 y r9 no se alcanzaron. El resultado no identifica la variante que falla. V12 verifica que la imagen sintética no herede labels y ejecuta las variantes presentes/ausentes en fixtures distintos. Ante cualquier código Go-template allowlisted, prueba los 25 campos allowlisted sobre el mismo fixture. Se preservan los valores en memoria solo para clasificar; no se imprimen ni guardan.

La primera revisión independiente detectó tres defectos: la etiqueta de propiedad falseaba la variante sin mapa de labels; un fallo de `docker stop` no impedía iniciar la siguiente variante; y los probes se activaban solo para un código genérico de evaluación, no para todas las clases Go-template allowlisted. Se corrigieron antes de solicitar el JIT: el runner valida que la imagen no herede labels; usa un marcador aleatorio en `Config.Env` sin agregar labels a la variante `absent`; comprueba ese marcador con salida binaria `OWNED` antes de cleanup; un fallo de cleanup detiene inmediatamente; y todos los códigos `INSPECT_TEMPLATE_*` activan el probe de los 25 campos. La decodificación ASCII de IDs también falla cerrado. La segunda revisión independiente queda pendiente.

## Pines y preparación

| Recurso | SHA-256 |
|---|---|
| Python V12 | `6ab7887690fc81a2fa5f97f047fc4a3973a4add8cb649751fdcd241c4db31e66` |
| Wrapper V12 + r9 | `a02b200efcf377da64bc13caa62136167811f31ac4fa4cf54ed81a4c7338f783` |
| Clasificador V11 base | `673a37dd8b2294ced7c5fd3a5faba408537df99a75191befb9a14df21c4ba743` |
| Probe allowlisted V8 | `ef7d8bf086335b07374186043dfe74964536ca9194df773d889cd7df5f23ab72` |
| JIT consumido V11 | `7775d8df1a71fe00f27e78e6a4e73599eab0a62bc064b438932adfb2dcd660b7` |
| Evidencia de fallo V11 | `971d9f770650411c963adba6270ae70891f332e3b6477663034a732e62156d29` |
| Paquete r9 | `688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02` |
| Manifiesto de inputs r9 | `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee` |
| Manifiesto de herramientas r9 | `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |
| JIT V12 | `b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf` |

Validación final de preparación: compilación sintáctica de V12 en memoria, `bash -n` del wrapper y comprobación de los tres manifiestos r9: PASS. El manifiesto marca 68 inputs del candidato, 3 auxiliares internos y 0 drift. La revisión independiente confirmó que las tres correcciones están presentes y, en una lectura final separada, verificó que el JIT fija el wrapper SHA `a02b200efcf377da64bc13caa62136167811f31ac4fa4cf54ed81a4c7338f783` y que el JIT conserva SHA `b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf`. No se ejecutaron Docker, F1, r9, pytest, npm, base de datos ni operaciones remotas en esta preparación.

La autorización V11 no cubre V12. Se solicita una invocación nueva con el alcance completo del [JIT V12](../operaciones/jit_h3req1_docker_desktop_wsl_f1_v12_template_variant_and_r9_once_2026-10-09.md); fallo/timeout consumen esa autorización. Sin aprobación, no se ejecuta Docker.

## Preservación y resultado actual

El usuario aprobó y consumió una invocación del JIT V12 SHA-256
`b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf`, ejecutada como romel
no-root en Ubuntu WSL con `require_escalated`. Resultado sanitizado: endpoint/V10/V11 previos
`OK`; `f1-template-synthetic-label-map/SYNTHETIC_IMAGE_LABELS_PRESENT`, exit 1. El mapa de
labels no vacío no demuestra que estén presentes las tres claves snapshot H3. El ciclo se
detuvo antes de contenedores, F1 y r9. No hubo retry, pull/build/install, cambios Docker ni
acceso a `studiamatch-dev`. La evidencia está en
[resultado V12](h3req1_c03_v12_synthetic_image_label_map_failure_2026-10-09.md).

La autorización V12 está consumida. La corrección posterior prepara una clasificación por
claves H3 específicas y no modifica producto ni runtime. Los siete fixtures sintéticos del
clasificador V13 pasaron localmente sin Docker. La revisión inicial encontró un defecto MEDIUM
y una brecha LOW; ambos se corrigieron. La segunda revisión independiente confirmó que no quedan
hallazgos en los dos runners V13 revisados.

El checkout candidato conserva 54 archivos tracked modificados, 220 rutas untracked y 0 staged; el checkout original conserva 39 tracked modificados, 39 untracked y 0 staged. No se hizo stage, commit, reset, checkout, clean, push, PR ni deploy.

El bootstrap Protected Workflow Integrity V3 permanece independiente y aislado, sin publicación, instalación ni enforcement remoto. Se conservan BFF/HttpOnly, roles, MFA, gateway, cuotas, cuenta existente y la matriz de cuatro ajustes. No se infiere HIGH actual desde el hallazgo histórico de sessionStorage. Aún no hay GO local ni Development.
