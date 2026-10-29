# H3REQ1 G08/G09 — corte de validación local R2 — 2026-10-10

## Candidato, autorización y preservación

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`; HEAD base: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Autorización humana: ciclo estrictamente local G01–G09 de 2026-10-10; sin JIT documental local adicional. No autoriza Git remoto, servicios remotos, secretos, checkout original, deploy ni CI remoto.
- WIP observado al comenzar este corte: 55 archivos rastreados modificados, 656 entradas no rastreadas, 0 staged. No se descarta ni altera trabajo previo.
- `studiamatch-dev` permanece healthy sobre `studiamatch-h3req1:20261009-v3`, loopback `127.0.0.1:3000`; holders de snapshot S2/S3 preservados. Pruebas G08 usaron contenedores efímeros sin red y no ejecutaron comandos dentro del contenedor habitual.

## G07 y G03 que se conservan

- La ejecución R48 de C03 integrado terminó `PASS` local sintético. Su manifiesto vigente contiene 127 entradas y `sha256sum -c` validó 127/127 inputs actuales. R47 queda como intento fallido previo al runtime (contrato de runner); R48 lo supersede sin borrar la evidencia.
- G03 r9 V5 ya acredita typegen, TypeScript con heap 3072 MiB, suites protegidas/workflow, scanner de credenciales y scope guard. ShellCheck/ESLint/actionlint se reutilizan mientras sus inputs permanezcan idénticos; este corte no los vuelve a ejecutar.

## G08 — pytest

Snapshot aislado para pytest: `source-candidate-r2.tar`, 1929 entradas, SHA-256
`f15f2ddcb996ecfb51fc1671318c30a97dfe67e2a5d35cb61c8433840762adaa`. Se excluyeron `.env*`, `.git`, cachés, `node_modules`, `.next`, `.wrangler` y salidas generadas; se incluyó únicamente el template no secreto `.env.example`. El preflight confirmó cero paths `.env*` operativos.

| Intento | Resultado | Alcance |
|---|---|---|
| Selección indiscriminada `pytest tests` | Exit 2 durante colección: dos directorios auxiliares one-shot contienen `test_diagnostic_once.py` y colisionan como módulo sin paquete. No ejecutó casos. | `pytest-full-r3.log` |
| `pytest --import-mode=importlib tests` | Exit 2 durante colección: cinco pruebas auxiliares dependen de importar helpers por su directorio local; con importlib esos módulos no están en `sys.path`. No ejecutó casos. | `pytest-full-r4.log` |
| Suite de archivos de producto `pytest tests/test_*.py -q --tb=short` | **Exit 0: 307 passed, 4 skipped, 1 warning de deprecación PyPDF2, 4.41 s.** | `pytest-project-r5.log` |

La selección de `tests/test_*.py` cubre los contratos Python de producto y las pruebas offline explícitas en `security-audit.yml`; excluye carpetas de pruebas de runners one-shot que no forman parte del paquete de producto y provocan conflictos de colección. Los cuatro skips corresponden al fixture de tests live de Supabase que exige `RUN_SUPABASE_INTEGRATION_TESTS=1` y credenciales; ambas condiciones quedaron ausentes, por aislamiento y exclusión de secretos/servicios remotos.

El primer intento del corte con el intérprete del sistema terminó antes de pytest por `No module named pytest`; la imagen fijada contiene `/opt/venv/bin/python` con pytest 9.1.1. La extracción inicial falló al intentar cambiar metadatos de la raíz `tmpfs`; la siguiente extracción aisló el receptor en `/workspace/repo`. No se reinstalaron dependencias.

La ejecución de 307 tests usó la imagen local V3 por digest
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`, `--network=none`, rootfs read-only, usuario 1001, límites 4 GiB/2 CPU, snapshot de fuente read-only y espacio de trabajo `tmpfs`. El contenedor efímero se retiró al finalizar; no se montó `.env*`, `.git`, volumen de dependencias ni checkout original.

## G09 — evidencia ejecutada que espera reconciliación documental

- UAT visual R9: salida `uat-runner-r9.out` declara PASS, 48/48 casos, 144/144 ejecuciones y capturas, cero retries. Matriz y hashes viven junto a ella en `../h3req1_g09_uat_2026-10-10_r1/h3-expanded-r9/`; falta verificar integridad de los 144 PNG en este corte.
- Onboarding R3: resumen sanitizado `../h3req1_g09_onboarding_2026-10-10_r3/onboarding-r3/onboarding-summary-r3.json` declara diez casos PASS, spacing mínimo 20100 ms y cero retries; no se usaron cuentas/correos reales.
- La revisión final, las seis premisas de calidad y la reconciliación de aceptación cliente siguen pendientes. No se suma ningún gate por estos resultados parciales ni por documentación.

## Próximos checks autorizados

1. Verificar integridad UAT R9 y onboarding R3, sin volver a ejecutar suites.
2. Ejecutar H2 writer scan, compilación Python afectada, npm audits de desarrollo/producción y build normal + mock sobre esta fuente aislada.
3. Reconciliar checks G03/G07 por hashes y completar consumidores locales BFF/SDK/cuotas/suspensión que no estén cubiertos por evidencia vigente.
4. Revisar de forma independiente los cambios funcionales/contratos; corregir y renovar solo las pruebas afectadas.
5. Actualizar estado e índice con G01–G10 y métricas solo después de comprobar criterios de cierre.

Sin commit, push, PR, merge, CI remoto, servicio remoto, deploy, secretos o datos operativos.
