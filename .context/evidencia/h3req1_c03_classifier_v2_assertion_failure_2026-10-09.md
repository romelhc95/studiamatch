# H3REQ1 — falla V2 acotada al caso `main()`; diagnóstico V3 preparado

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El WIP del
candidato y el checkout original se preservan.

## Invocación aprobada y salida

El usuario aprobó una invocación del JIT
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`,
SHA-256 `708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`. Se ejecutó una vez
como `romel` en Ubuntu WSL interactiva, sin `sudo`; runner combinado fijado al SHA
`d7e64ac2125bcaa703479e4f6eb83e449fcc309e56b559795235a64006e416f9`.

Salida sanitizada completa y exit:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=V2_MAIN_SANITIZATION_FAILED
exit=1
```

El endpoint Desktop WSL y la lectura allowlisted del digest local de imagen sintética pasaron.
Falló el caso V2 `test_v2_main_emits_only_sanitized_template_error`. El código genérico no
permite conocer si discrepó el retorno de `main()`, la secuencia de fases, la ausencia del
marcador sensible, una excepción o la clasificación del reporte. La salida cruda de pytest no
se mostró ni persistió. La ejecución se consumió y se detuvo: no leyó F1, no ejecutó r9 y no
continuó a copia, Pages/workerd ni C03 integrado.

No hubo `pull`, rebuild, instalación o cambio de configuración Docker, ni consulta/inicio del
contenedor `studiamatch-dev`. Se usó el contenedor de pruebas efímero previsto por el JIT.

## Revisión del resultado y cambios limitados

La revisión estática del test mostró que `test_v2_main_emits_only_sanitized_template_error`
agrupaba tres comprobaciones sin mensajes diferenciados: exit code, secuencia exacta de
fases/códigos, y ausencia de `private-host-path` en stdout. El código del helper emite solo
fases/códigos fijos; no se halló evidencia estática que justifique modificar la clasificación
F1 o relajar la aserción.

Se preparó instrumentación de test —no producto— que etiqueta cada subpredicado con un token
constante y hace que un runner nuevo mapee solo esos tokens a códigos cerrados. El detalle de
pytest sigue en memoria efímera; no se imprime ni persiste. Un token desconocido conserva el
código genérico. No se ejecutaron las nuevas pruebas.

La primera revisión del paquete V3 halló que el helper base todavía pasaba un entrypoint
V2 fijo al contenedor. Se corrigió para aceptar un runner fijado, y el wrapper V3 pasa la ruta
V3. La solicitud anterior con SHA `a7fe73ac…` quedó obsoleta y no se ejecutó.

Revisión estática final del paquete corregido: `bash -n` exit 0, parseo AST de los tres
archivos Python PASS, `git diff --check` PASS y pines verificados; no hay placeholders. No se
ejecutaron pytest ni los tests del contenedor.

La revisión de seguridad manual se limitó a los nuevos/modificados runners y su manejo de
salida. El preflight del plugin `security_diff_scan` quedó `ready` con advertencia por
delegación no disponible. Al solicitar el scope de `tests/h3req1_docker_peer_substep_diag`,
el conector rechazó crear el scan e indicó que `scope="."` es obligatorio. No se creó scanId ni
se amplió el alcance: el usuario pidió no repetir scans completos. Por lo tanto no existe un
reporte automatizado de Codex Security; los checks de sintaxis/pins y la revisión manual no se
presentan como sustitutos de ese reporte.

El paquete agrupado
[JIT diagnóstico V3 + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v3_main_assertion_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V3-MAIN-ASSERTION-AND-R9-ONCE-20261009-V1`,
SHA-256 `1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`, requiere aprobación
independiente. Incluye una sola ejecución diagnóstica; F1 y r9 ocurren solo tras los predicados
exactos en `OK`.

## Estado de aceptación y otros frentes

Los cuatro cambios funcionales permanecen como en la matriz: edición Admin con procedencia,
auditoría actor/fecha/diff, disponibilidad con evidencia válida ≤90 días y email Auth en
encabezado. No se probó ninguno de los nuevos asserts en este JIT. Sus resultados históricos
se conservan separados; no se suman como aceptación del candidato actual.

CI Protected Workflow Integrity V3 permanece como patch aislado, SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`; sin cambios, publicación,
pytest, actionlint ni run remoto en este ciclo. El stop local no acredita CI.

G01=10/10 y G02=10/10; G03–G10=0/10; total **20%**, delta cero; D01–D14=0/14. Los parciales
anteriores (SQL C03 41/41, r4 20/20, scanner r7, UAT BFF r2, UAT histórico 144/144 y onboarding
histórico 10/10) continúan separados. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
