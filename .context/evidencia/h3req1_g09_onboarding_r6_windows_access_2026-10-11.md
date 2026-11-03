# H3REQ1 G09 — onboarding R6 y acceso Windows — 2026-10-11

## Identidad y alcance

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Antes de esta ejecución: 60 archivos rastreados modificados, 0 staged, 785 entradas untracked agregadas por directorio y 12,838 paths untracked; `git status --short` muestra 845 entradas y la expansión completa 12,898 paths. Se preservó el WIP.
- Inputs del build R6: manifiesto de fuentes 643 archivos, SHA-256 `7e4349e657591069a7accf7eeaa1fc35b95cea896c449f8b3d40a5bca032ab19`; manifiesto mock export `d5cc70219d27a573f39a1e6b374def51187bb61fc25d9612fe51e07fba2a905c`; imagen `studiamatch-h3req1:20261009-v3`, ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- No se modificó código de producto. Los cambios propios de esta continuación son un ejecutor de diagnóstico y esta evidencia.

## Acceso desde Windows

Se reutilizó el acceso ya activo; no se recrearon la app ni PostgreSQL para publicarlo.

| Recurso | Identidad | Uso |
|---|---|---|
| URL | `http://127.0.0.1:3333/` | Catálogo público del candidato desde Edge/Chrome de Windows. |
| Detalle sintético | `http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/` | Curso para el recorrido público y de filtros. |
| Proxy | `h3req1-g09-localhost-proxy-r12`, ID `347eb5abd1c2fab9dbac23480f7113c3f78d2eb30a46510b6e8d55dbd267c7bc` | Binding comprobado `127.0.0.1:3333 -> 3330/tcp`; no escucha en interfaces externas. |
| App | `h3req1-g09-uat-app-20261010-r12`, ID `0e3f4b56fff870062788c53879a538efa31963f81ad1be5dbfb49af8cde12fc7` | Pages/workerd del candidato, imagen `studiamatch-h3req1:20261009-v3`. |
| PostgreSQL | `h3req1-g09-uat-pg17-20261010-r12`, ID `4e2891cfad4a` | Dataset UAT sintético asociado al recorrido público. |

HTTP desde Ubuntu/WSL: root y detalle respondieron `200`. En PostgreSQL se verificó una fila para el slug `analitica-aplicada-60000000`: ID `70000000-0000-0000-0000-000000000091`, nombre “Analítica Aplicada”. No se leyeron secretos ni se hicieron escrituras.

El onboarding R6 usa un escenario separado: `h3req1-g09-onboarding-app-20261011-r6`, PostgreSQL 17.11 `h3req1-g09-onboarding-pg17-20261011-r6`, DB sintética `h3_final_uat_onboarding_g09_20261011_r6` y red interna `h3req1-g09-onboarding-net-20261011-r6`. Ese runtime no tiene puerto publicado. No se alteró ni recreó para obtener acceso; sigue aislado y detenido tras el ensayo. Esta distinción evita afirmar que el DB de onboarding es el dataset público R12.

## Servidor, navegador y ventana

| Ensayo | Servidor/datos | Navegador | Ventana |
|---|---|---|---|
| Revisión Windows R12 | Pages/workerd en el contenedor UAT, detrás del proxy local; PostgreSQL 17 UAT con el curso sintético indicado. | Edge o Chrome del responsable al abrir la URL. | Visible en Windows. |
| Onboarding R6 | Pages/workerd + mock Auth/BFF dentro del app R6; PostgreSQL 17.11 y red Docker interna. | Playwright Chromium 1228 dentro del contenedor app. | Headless, sin ventana. |

No se guardaron vídeo ni trazas de red del onboarding: podrían contener material de sesión. Las diez capturas de página se generaron después de limpiar campos de contraseña.

## Resultado onboarding R6

1. El runner R6 alcanzó build, PG17, migraciones locales, readiness y reset HTTP 204; la suite funcional terminó `exit=1`, `ONBOARDING_TEST_FAILED`, `retries=0`. Ese wrapper no conservó caso ni clase del error.
2. La continuación diagnóstica V1 reutilizó el mismo app ID, PG y red; generó `OUTPUT_REJECTED` por un filtro de formato defectuoso. Conserva la captura [FAIL-INV-008](h3req1_g09_onboarding_2026-10-11_r6/run-r6/onboarding-r6-diagnostic/screenshots/FAIL-INV-008.png), que muestra la página en “Validando acceso…”. La prueba sintética del filtro también falló. No se atribuye ese error al producto.
3. El ejecutor se corrigió para persistir solo caso, código/clase allowlisted y respuestas de rutas BFF categorizadas (sin URL/query, bodies, correo ni mensajes crudos). La pasada V2 terminó exit 0, 10/10 PASS, espaciamiento mínimo 20,100 ms y cero retries dentro de la ejecución. Se validó la lista exacta de casos `INV-013, INV-008, INV-001, INV-002, INV-009, INV-007, INV-003, INV-004, INV-005, INV-012`. Las respuestas categorizadas observadas fueron HTTP 200 y callback Auth BFF HTTP 303; los logs sanitizados de runtime no reportaron `error_code`.
4. No hubo cambio funcional entre el fallo anterior y el PASS V2. Por tanto, el PASS actual se conserva, pero la diferencia sigue sin causa demostrada; onboarding no justifica por sí solo cerrar G09. No se hará otra repetición idéntica para borrar ese antecedente.

Evidencia durable:

- Resultado sanitizado y eventos categorizados: `run-r6/onboarding-r6-diagnostic-v2/onboarding-summary-diagnostic.json`.
- Reporte detallado del runner: `run-r6/onboarding-r6-diagnostic-v2/onboarding-result.json`.
- Manifiesto de diez capturas: `run-r6/onboarding-r6-diagnostic-v2/screenshots.sha256`; todos los PNG verifican.
- Capturas: [`INV-001`](h3req1_g09_onboarding_2026-10-11_r6/run-r6/onboarding-r6-diagnostic-v2/screenshots/INV-001.png), [`INV-002`](h3req1_g09_onboarding_2026-10-11_r6/run-r6/onboarding-r6-diagnostic-v2/screenshots/INV-002.png), `INV-003/004/005/007/008/009/012/013.png` en el mismo directorio.
- Captura de diagnóstico fallido, preservada separada: [`FAIL-INV-008`](h3req1_g09_onboarding_2026-10-11_r6/run-r6/onboarding-r6-diagnostic/screenshots/FAIL-INV-008.png).

El runner retomó el contenedor app por ID y lo detuvo de nuevo tras preservar evidencia; no recreó app, base ni red. El PG17 y la red permanecen preservados. R12, `studiamatch-dev`, sus imágenes y volúmenes no se modificaron.

## Impacto en gates

G01–G10 no cambian con este resultado: tablero histórico 70%, cierre local 7/9 = 77.78%, delta 0 pp. G09 sigue parcial porque LOCAL-01..23 no está completo y la intermitencia de onboarding no está explicada. El detalle amplía LOCAL-11, no reemplaza la aceptación de los demás criterios ni el cierre G08.
