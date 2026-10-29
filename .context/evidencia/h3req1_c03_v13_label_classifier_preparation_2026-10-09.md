# Preparación V13 — clasificador de labels H3, F1 y r9 condicional

Fecha: 2026-10-09. Estado: fixtures 7/7 PASS, hallazgos de primera revisión corregidos y revisión independiente final sin hallazgos. La ejecución Docker requiere autorización humana nueva.

## Ficha del cambio

| Campo | Resultado |
|---|---|
| Objetivo | Resolver el preflight V12 que rechazó un mapa `Config.Labels` no vacío sin identificar si contenía claves snapshot H3. |
| Candidato | `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. |
| WIP | 54 tracked modificados, 220 rutas untracked, 0 staged; checkout original preservado aparte con 39/39/0. |
| Archivos propios | `tests/h3req1_docker_peer_substep_diag/f1_template_label_classifier_v13_once.py`; `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v13_label_classifier_then_r9_once.sh`. |
| Impacto | Diagnóstico/tooling local únicamente; no cambia producto, contratos, SQL, Docker, secretos o estado remoto. |
| Evidencia V12 | `SYNTHETIC_IMAGE_LABELS_PRESENT`, exit 1; se detuvo antes de contenedores, F1 y r9. |
| G03/G04 / total | 0/10 y 0/10; G01/G02 10/10; G05–G10 0/10. Total 20%, delta 0. D01–D14 0/14. |

## Hallazgo y ajuste

V12 demuestra solo que el JSON del mapa de labels no es vacío. V13 parsea la salida en memoria, acepta `null`, `{}` y labels ajenos, y bloquea si aparece cualquiera de las tres claves snapshot fijadas por el helper V7. JSON no válido, raíz no objeto o bytes que no sean UTF-8 fallan cerrado. No se emiten ni guardan nombres, valores ni metadata del mapa.

El predicado se llama una sola vez y cachea únicamente que la imagen sintética pasó. Las variantes `present` y `absent` conservan su contrato: la primera añade las tres labels y tmpfs; la segunda no agrega labels ni tmpfs. Un error de lectura conserva su código sanitizado; fallo de cleanup detiene el siguiente paso. El wrapper exige secuencia exacta, y solo permite leer F1 después del smoke; r9 queda después de ambas lecturas F1 satisfactorias.

## Pruebas y revisión

Fixtures sintéticos ejecutados sin Docker: `null`, mapa vacío, label ajeno, cada una de las tres claves objetivo por separado y JSON malformado. Resultado tras aplicar la cobertura señalada: 7/7 PASS. Los casos imprimen solo fases cerradas; no exponen el contenido del fixture.

Validaciones de preparación: compilación Python en memoria PASS; `bash -n` PASS; manifiestos r9 revisados para reutilización. Estas comprobaciones no son runtime Docker, F1, r9 ni PASS de producto. No se reejecutan suites funcionales o scans amplios.

Revisión independiente inicial: encontró un defecto MEDIUM donde el wrapper podía salir con status 0 ante output inesperado y un gap LOW porque solo una de tres claves se probaba. Se cambió el status a no-cero ante cualquier mismatch y se añadieron tres casos independientes. La revisión final no halló defectos restantes; confirmó que wrapper y helper fijan SHA `59781a6607da28918536e57698e683051967e3407ec30e09a148692675d9ddb7` y `e2cb61472552dab4165014347f63232a3f8d1d888efa7b75aea918a02c71d073`. El runner Python produjo 7/7 fases sintéticas `OK`. La revisión no ejecutó Docker ni pruebas.

## Pines previstos para el JIT V13

SHA-256 del JIT V13: `5019c8cd6aab75d18d3f4e369744470fee16ad91398855f6d3c18c781250aa25`. Los SHA de runners y dependencias están en el [JIT V13](../operaciones/jit_h3req1_docker_desktop_wsl_f1_v13_label_classifier_then_r9_once_2026-10-09.md). Resultado V12 fijado: [evidencia](h3req1_c03_v12_synthetic_image_label_map_failure_2026-10-09.md). La invocación V13 no repite F2d/V10/V11/V12; retesta los siete fixtures puros antes del diagnóstico de labels, y continúa con una única lectura F1 y r9 condicionales.

## Estado y siguiente gate

El JIT V13 también fue aprobado y consumido: el wrapper emitió `f1-v11-output/OUTPUT_REJECTED`, exit 1, y detuvo r9. La salida no permite saber si el runner había alcanzado F1 ni acreditar cleanup; los detalles están en el [resultado V13](h3req1_c03_v13_output_rejected_2026-10-09.md). No se ejecutó r9, copia, arranque, integración Edge/PG17/PostgREST o C03 integrado. V14 prepara una nueva solicitud agrupada de una invocación, sin habilitar publicación, integración o configuración CI remota.

Se conservan BFF/HttpOnly, MFA, roles, gateway, cuotas y la cuenta actual. No se deriva XSS ni HIGH actual del hallazgo histórico de sessionStorage. La matriz de aceptación de los cuatro ajustes permanece en la nota de alcance; los runtimes del candidato vigente esperan desbloqueo local. Sin `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
