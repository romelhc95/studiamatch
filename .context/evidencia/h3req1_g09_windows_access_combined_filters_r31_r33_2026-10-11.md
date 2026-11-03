# Acceso Windows y recorrido de filtros combinados R31–R33 — 2026-10-11

## Candidato, runtime y datos

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el WIP probado es el conjunto
  completo de archivos indicado por el estado vigente.
- URL disponible en Windows: `http://127.0.0.1:3333/`.
- Proxy existente: `h3req1-g09-localhost-proxy-r12`, binding exclusivo
  `127.0.0.1:3333`; enruta al Pages/workerd de
  `h3req1-g09-uat-app-20261010-r12` (`studiamatch-h3req1:20261009-v3`, puerto
  interno 3330). El PostgreSQL sintético existente es
  `h3req1-g09-uat-pg17-20261010-r12`, base
  `h3_final_uat_g09_20261010_r12`.
- Datos visibles: 16 programas, cinco instituciones y el curso sintético
  “Analítica Aplicada”, UUID `70000000-0000-0000-0000-000000000091`, slug
  `analitica-aplicada-60000000`.
- No se recrearon, reiniciaron ni reemplazaron la app, proxy, PostgreSQL o
  fixture para abrir acceso. No se pasaron `.env`, credenciales operativas ni
  valores secretos al proxy. Windows ya tenía verificación PowerShell HTTP 200
  para catálogo y detalle; en esta continuación `curl` desde WSL también dio
  HTTP 200 a través del mismo binding. No se abrió una ventana Windows GUI.

## Ejecución R33

El preflight del runner canónico `tests/h3_local_uat.mjs` coincidió entre
checkout y contenedor, SHA-256
`d6718f0883a47e1141a74401e080e2ccd2d43364591156adb5e604947c8f60b7`.
R33 ejecutó únicamente H3-UAT-053, contra la misma app/fixture: intersección
de texto, área, tipo, institución, modalidad, mínimo/máximo, orden, duración y
banda de precio; comprobó query shareable, una tarjeta coincidente y links al
mismo slug.

| Viewport | Resultado | Aserciones | Errores de consola | Requests fallidos | Captura |
|---|---:|---:|---:|---:|---|
| Desktop 1440×900 | PASS | 3/3 | 0 | 0 | `H3-UAT-053-desktop.png` |
| Tablet 768×1024 | PASS | 3/3 | 0 | 0 | `H3-UAT-053-tablet.png` |
| Móvil 390×844 | PASS | 3/3 | 0 | 0 | `H3-UAT-053-mobile.png` |

Total: 1/1 caso lógico, 3/3 ejecuciones, 9/9 aserciones, tres PNG, cero retries,
exit 0. Playwright Chromium 1228 corrió headless dentro de la app UAT, sin
ventana visible. El caso hizo GETs al catálogo y navegación local. El runner
restableció el namespace sintético del mock entre viewports por el proxy local;
no modificó la fila del curso PG17.

La corrida enfocada no graba vídeo: el runner actual reserva vídeo para el
recorrido integrado H3-UAT-049. El vídeo del recorrido integrado R30 permanece
disponible en `h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r30/H3-UAT-049-desktop.webm`.

## Intentos previos preservados

El preflight de estructura de H3-UAT-053 dio PASS (un caso, tres viewports,
cero retries). R31 y R32 terminaron exit 1 antes de crear ejecuciones o
capturas; sus matrices rojas se preservan y no son fallos de producto:

| Intento | Fase/exit | Causa concreta | Efecto |
|---|---:|---|---|
| R31 | setup / 1 | El comando vació `H3_TEST_RESET_TOKEN`; el runner lo exige para el reset sintético previo a cada viewport. | 0 ejecuciones, 0 capturas; no llamó al mock ni tocó PG17. |
| R32 | reset del mock / 1 | `H3_MOCK_URL` apuntaba a 3001, que no escucha en este runtime. Los puertos activos del fixture son Pages 3330, proxy mock 3331, PostgREST mock 3332 y perímetro 3333. | `fetch failed`, 0 ejecuciones, 0 capturas; no hubo request al servidor. |

R33 corrigió solo el despacho: heredó el token sintético existente sin
imprimirlo y usó el proxy mock local `127.0.0.1:3331`. No se cambió el runner
ni el producto. Los tres resultados de R31–R33 se conservan en
`h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r31/`,
`h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r32/` y
`h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/`.

## Capturas e integridad

- [Desktop](h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/H3-UAT-053-desktop.png)
- [Tablet](h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/H3-UAT-053-tablet.png)
- [Móvil](h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/H3-UAT-053-mobile.png)
- [Matriz R33](h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/h3-expanded-uat-matrix.json)
- [Ejecuciones y aserciones R33](h3req1_g09_uat_2026-10-10_r4/uat-functional-win-access-r33/h3-expanded-uat-executions.json)

SHA-256 de las tres capturas:

| Artefacto | SHA-256 |
|---|---|
| Desktop | `76f4e24d6ead8f2e5ce9754cb102f943cbd8e284988c8ac1c40c9ccb9fd28193` |
| Tablet | `ca8052b0a1aa7eac138e0ee2c8f35af1fc23dedbddcf8fada09585326e62c73d` |
| Móvil | `50a9dc8e7069ceb3bc6c73e678cadac20a3c140a2fa12685b9b87708a9faa5c6` |

R33 confirma el recorrido combinado sobre este candidato y runtime, pero no
cierra G09 ni cambia el porcentaje de gates. G09 mantiene las demás áreas de
aceptación LOCAL-01..23; las fallas de harness R31/R32 quedan diferenciadas
del resultado funcional R33.
