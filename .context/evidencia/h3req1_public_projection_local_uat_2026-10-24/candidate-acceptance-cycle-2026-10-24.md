# H3REQ1 — ciclo local duración compuesta y viewport móvil

Fecha del corte: 2026-10-24. Estado: **VALIDADO LOCAL — PENDIENTE REMOTO**.

## Identidad del candidato y alcance

- Worktree: `/home/romel/src/studiamatch-h3req1-duration-mobile-candidate-20261024`.
- Rama: `feat/h3req1-public-duration-mobile-20261024`.
- Base/HEAD antes de commit: `1c69b94606795e33c9fee82e8a8e803f3104c566`.
- Entorno canónico: Docker, static export local servido en `http://localhost:3330`, mock sintético en `http://localhost:3332`; fixtures en PostgreSQL 17 desechable. No se consultó ni escribió Supabase remoto.
- Inspección visual complementaria: Chrome Windows MCP, perfil de pruebas, servidor candidato local `http://localhost:3020/`; no hubo login. Es una observación local separada del runner canónico.
- SHA/ID del deployment Development: ninguno para este candidato. No se hizo push, PR, merge ni deploy.

El delta corrige dos defectos reproducidos: el parser de duración tomaba el primer número aunque fuera una cantidad de horas, y el panel “Más filtros” se salía del viewport angosto. La validación a 320 px también reprodujo un desbordamiento global del footer; `Footer.tsx` ahora permite envolver sus columnas. No se cambió la regla de disponibilidad ni se inventó disponibilidad comercial. El fixture elegible empleado por estos UAT es sintético y local.

## Resultados canónicos

Ejecución final conjunta de `H3-UAT-058` y `H3-UAT-059`: **PASS, 2/2 casos, 6/6 ejecuciones por viewport, 6 capturas, 0 reintentos**. Resultado registrado en [`h3-expanded-uat-matrix.json`](run-canonical-058-059-footer-20261024/h3-expanded/h3-expanded-uat-matrix.json), con manifiesto, ejecuciones, hashes y capturas en el mismo directorio `h3-expanded/`.

| Caso | Criterio | Resultado y cobertura local |
|---|---|---|
| H3-UAT-058 | H3-CA4.11 | PASS desktop 1440, tablet 768 y móvil 390; dentro del escenario móvil también valida ancho 320, lista con filtros abiertos/cerrados, detalle y footer sin overflow horizontal. |
| H3-UAT-059 | H3-CA4.9 | PASS desktop, tablet y móvil; filtros independientes, duración mixta en el filtro corto, “Actualizarme”, reset/query, paginación y estado vacío. El fixture híbrido `32 horas académicas 1 mes aproximadamente.` entra en “Actualizarme”; el de 7 meses no. La regla de rango tiene su comprobación sintética focal separada, no se atribuye a este caso. |

Los nombres de los cursos y datos del resultado provienen de fixtures sintéticos. La ejecución local no cambia el estado de D01–D14, no es aceptación remota y no cierra D06/Admin. Tras desplegar exactamente este código, ambos casos deben repetirse remotamente y junto con un smoke general.

## Evidencia visual local

Chrome Windows MCP inspeccionó `http://localhost:3020/` con ancho real de 320 CSS px. La relectura DOM del servidor local confirmó `documentElement.scrollWidth=320`, `body.scrollWidth=320`; el footer ocupa x=0..320 y `scrollWidth=clientWidth=320`. El panel expandido ocupa x=16..304 dentro del viewport. La fila primaria de filtros tiene `scrollWidth=280` frente a `clientWidth=272`; sus controles permanecen dentro de x=24..260, el documento no se ensancha y no se observó clipping. El dato de 8 px se conserva como overflow interno de contenido de esa fila, no como overflow global del footer ni del viewport. La consola no mostró errores de aplicación. En el DOM se observaron dos inputs públicos sin `id`, `name` ni `aria-label`; esto no fue introducido por el delta ni se amplió el alcance para corregirlo. La interacción directa con una URL de detalle en el Next dev server devolvió un error de rutas estáticas/mock; el runner canónico en el export Docker sí cubrió el detalle responsive, por lo que esa discrepancia local del servidor dev no se contabiliza como fallo del candidato ni como captura de detalle verificada por Chrome.

## Validaciones locales en Docker

- ESLint focal sobre `HomeContent.tsx`, `supabase.ts` y `Footer.tsx`: exit 0, 0 errores y 9 warnings heredados en líneas no cambiadas. Log: [`eslint.stdout`](run-final-docker-checks-2026-10-24/eslint.stdout).
- TypeScript `npx tsc --noEmit --incremental false`: exit 0. Log: [`typescript.stdout`](run-final-docker-checks-2026-10-24/typescript.stdout).
- `npm run build:mock`: exit 0, static export Next.js 16.3.8 y ruta mock de detalle prerenderizada. Log/hash de salida: [`static-build.stdout`](run-final-docker-checks-2026-10-24/static-build.stdout), [`static-build-artifact.sha256`](run-final-docker-checks-2026-10-24/static-build-artifact.sha256).
- Tests unitarios de sanitización/diagnóstico HTTP: 18/18 PASS. Log: [`uat-helper-unit-tests.stdout`](run-final-docker-checks-2026-10-24/uat-helper-unit-tests.stdout).
- UAT canónicos: 2/2 y 6/6 PASS como se describe arriba. PostgreSQL 17 era desechable; reset/mock usó fixture local. No se leyeron ni registraron el token sintético de reset, credenciales, cookies ni tokens de sesión.
- Gate documental Docker, repetido después del último delta textual: `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`; 734/734 fuentes asignadas/estructurales, 724/734 con todas las dimensiones, 14/14 componentes, 4.777 relaciones locales verificadas, 115/115 documentos activos y 433/433 históricos catalogados/enlazados. El inventario global reporta 9/15 checks remotos verificados y 6/15 pendientes; este gate estructural no los convierte en aceptación remota.
- Codex Security diff scan `660b6013-6caf-41f8-bb95-5a3e968b8186`: completo, 0 findings (0 HIGH/CRITICAL), 4/4 superficies sin issue encontrado. El inventario automático de 38 filas se reconcilió con el scope exacto: 87 paths cambiados/no versionados = 37 modificados incluidos + 50 modificados preservados; dos tests de dependencia ya existentes están en la lista de inclusión solo para trazabilidad y 39 artefactos preservados no están modificados. Ningún path modificado quedó sin clasificar. Se revisaron los 39 paths incluidos y 89 excluidos. La credencial fue escaneada en Docker sobre los 39 paths incluidos: exit 0, `credential scan passed`; no se abrió `.env`.
- Después del snapshot de Codex Security, el delta fue documental: ficha `web_publico.md`, este informe y el cuerpo PR. El código, tests, fixtures y capturas no cambiaron. Se revisaron esas líneas manualmente y se reejecutaron el gate documental con manifiesto candidato y el credential scan sobre los 39 paths incluidos; ambos pasaron. El scan de fuente sigue siendo de alcance local y no acredita runtime remoto.

Las regresiones fallidas anteriores se conservan bajo `run-canonical-058-059-footer-20261024/`: la aserción de reset esperaba un curso en la página 1 aunque estaba en página 2; el fixture de duración mixta estaba en modalidad presencial cuando el objetivo “Actualizarme” solo admite remoto/híbrido. Se corrigió la prueba/fixture, no se debilitó el contrato. Los directorios de backups y arranques fallidos son historia de diagnóstico y no forman parte del paquete PR.

## Revisión de impacto y estados H3REQ1

Fuentes y consumidores afectados: `parseDurationToMonths` alimenta filtros/facetas públicos y ambos consumers de “Actualizarme” en `HomeContent.tsx`; la fila de filtros gobierna el ancla del popover; `Footer.tsx` se comparte por las páginas públicas. El runner y el seed modificados son fixtures/UAT locales. No cambian el contrato Auth/BFF, la proyección de disponibilidad, las escrituras de negocio ni el pipeline FG3.

Estado de casos sin cambio por esta etapa: D03 completo solo para el onboarding observado; D01, D02, D04 y D06 parciales; D05 y D07–D14 pendientes; ningún caso fallido nuevo; los once grupos adicionales permanecen en 0/11 completos. El resultado de UAT 058/059 se registra por separado de la matriz D y no se transfiere a Development.

Se mantienen los seis frentes con denominador fijo: 2/6 cerrados (33,3%), 3/6 en curso (50%) y 1/6 pendiente (16,7%). Este contador describe los frentes operativos, no aceptación contractual.

## Transición y rollback

- **expand:** conservar helper/consumers actuales y admitir formatos históricos junto con unidades compuestas.
- **compatibilidad:** el parser sirve los filtros de duración, facetas y “Actualizarme”; el popover y footer se adaptan a ancho estrecho sin tocar filtros de negocio.
- **deploy:** pendiente de autorización humana para commit, push y PR protegido a `desarrollo`; el push puede crear un Preview automático de Pages. No autoriza merge ni deploy manual.
- **contract:** después de merge/deployment confirmado, ejecutar H3-UAT-058, H3-UAT-059 y smoke público contra el SHA/deployment nuevos.
- **rollback:** revertir como una unidad los cambios de parser y sus dos consumers, el posicionamiento del panel y el wrapping del footer; ejecutar nuevamente los dos UAT afectados. No tocar datos o configuración remotos.

## Paquete de publicación

La lista exacta de paths incluidos/excluidos está en [`candidate-pr-scope-2026-10-24.json`](candidate-pr-scope-2026-10-24.json). El borrador completo basado en la plantilla versionada está en [`candidate-pr-body-2026-10-24.md`](candidate-pr-body-2026-10-24.md). Estos archivos registran preparación, no permiso de publicación.
