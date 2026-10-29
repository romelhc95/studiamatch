# H3REQ1 — sintéticos V2 fallaron; causa interna no distinguida

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP al invocar:
234 entradas; el checkout original conserva 78.

## JIT consumido y resultado

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-PIN-FIX-AND-R9-ONCE-20261009-V1`, SHA-256
`dbc58ec3dcc3ce7cacc83d84ec6689a16f1564ae40c0776607fba5e35371e79d`. El JIT y los runners
fijados fueron verificados antes de ejecutarlo. Ejecutor: `romel`, Ubuntu WSL interactiva con
TTY, sin sudo.

Resultado sanitizado:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-tests|error_code=SYNTHETIC_TESTS_FAILED
```

Exit del wrapper: **1**. Docker Desktop WSL endpoint y Engine Linux quedaron acreditados. La
fase sintética comenzó y falló; el stop impidió la lectura de imagen/contenedor F1 y r9. No se
repitió el JIT y no hubo consulta de `studiamatch-dev`, rebuild/pull, instalación ni cambio de
Docker.

## Predicado y límite de diagnóstico

La fase interior ejecuta `docker run --pull=never` con el digest de test fijado; dentro llama
`python3 -m pytest ... -k 'v2'`. El helper traduce cualquier retorno non-zero de esa orden a
`SYNTHETIC_TESTS_FAILED` y suprime stderr/stdout. El resultado no separa imagen ausente, fallo
al crear el contenedor, pytest/dependencia no disponible, colección ni una aserción fallida.
No hay nombre de test ni salida cruda preservada.

La revisión estática de los casos `test_v2_distinguishes_template_parse_and_evaluation_errors_without_raw_text`
y `test_v2_main_emits_only_sanitized_template_error` no encontró un defecto determinista. En
particular, el segundo fixture sustituye la orquestación sintética y fija el helper de inspección
con errores sintéticos; esto no prueba el comportamiento runtime. Por tanto no se cambia una
aserción a ciegas ni se afirma que pytest ni el Docker Engine sean la causa.

## Mejora diagnóstica y siguiente invocación

La brecha demostrada es la clasificación de la falla sintética. Se preparó una sola ejecución
nueva que aporta evidencia acotada sin exponer salida cruda y que:

1. compruebe presencia local del digest fijado mediante lectura Docker allowlisted, sin pull;
2. emita códigos cerrados distintos para framework/colección, aserciones de casos V2
   allowlisted y fallo de lanzamiento/timeout;
3. mantenga toda la salida pytest en memoria efímera, sin stdout/stderr, metadata, rutas o
   valores raw; y
4. continúe a F1 una vez y a r9 solo si todos los casos sintéticos pasan.

El JIT anterior está consumido; el nuevo ID es
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`,
SHA-256 `708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`. El paquete
[JIT diagnóstico sintético + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_synthetic_diagnostic_and_r9_once_2026-10-09.md)
requiere aprobación exacta. F1 no fue reconsultado y conserva su último resultado previo
`INSPECT_TEMPLATE_ERROR`. El reporte de hashes staged de `studiamatch-dev` es un asunto
separado; se conservó el contenedor.

## Estado independiente y gates

Bootstrap CI Protected Workflow Integrity V3 permanece aislado/sin aplicar, SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. No se ejecutaron pytest,
actionlint, validación Docker CI ni checks remotos. Las reglas GitHub requieren
`security-audit`; Pages Production continúa en `main` con watch `*`.

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta cero; D01–D14=0/14. Parciales
anteriores (C03 SQL 41/41 inputs, r4 20/20, scanner r7, UAT BFF r2, UAT histórico 144/144 y
onboarding histórico 10/10) permanecen separados. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
