# Checkpoint local — contrato editorial H3REQ1

## Addendum post-merge y aceptación remota R1–R4 — 2026-10-28

**Continuación retomada:** 14:50:14 America/Lima. **Corte remoto R1–R4:**
2026-10-28, desde 14:50 hasta 15:07 America/Lima. El arreglo posterior se prepara
en el worktree separado `codex/h3req1-public-price-projection-20261028`; su gate
local/documental y publicación se registrarán en un addendum final. Se conserva
debajo la historia previa sin cambiar sus resultados.

### Integración, deployment y schema verificados

- PR #508: `https://github.com/romelhc95/studiamatch/pull/508`; aprobado sobre
  `85e9d1b17ca2808ed320ba2c37d893fbf7619dad`, merge en `desarrollo`:
  `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, 2026-10-28 12:39:06
  America/Lima. El head tuvo 16 checks `success` y 2 `skipped`.
- Checkout de evidencia preservado: `/tmp/studiamatch-h3req1-editorial-contract-20261028`,
  rama `codex/h3req1-editorial-contract-20261028`, HEAD local aprobado
  `85e9d1b17ca2808ed320ba2c37d893fbf7619dad`. No se cambió a `desarrollo` ni se
  modificó código; únicamente están modificadas localmente las tres fuentes
  documentales de este corte, sin commit/push.
- Deployment de rama Development: Pages `27d9ebfc-1ff4-4c43-b58f-117d98977cd0`,
  rama `desarrollo`, SHA `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, etapa
  `success`, alias `https://desarrollo.studiamatch-aty.pages.dev`. No confundir
  con el Preview de PR `920821c9-5fdb-4dbb-94d6-6dc1b9e840af`, que corresponde a
  la rama feature y tiene alias propio. No se hizo deploy manual.
- Supabase Free/Development `aqrldlmlszjtgpqiegaa` (instancia compartida con
  Certification): preflight mostró 81 entradas
  de ledger, sin la migration y con columnas/RPC/vista bajo el contrato anterior.
  JIT exacto aprobado y consumido: una aplicación de
  `db/migrations/20261028_h3_editorial_publication_snapshot.sql`, SHA-256
  `2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef`.
  Ledger posterior: 82 entradas; versión `20261028194353`,
  2026-10-28 14:43:53 America/Lima. Postcheck: tres columnas snapshot nullable,
  dos checks validados, firmas/RPC/helper esperados, `security_invoker` en la vista
  pública y grants acordes; ejecución Admin negada a `anon` y permitida a
  `authenticated`/`service_role`. Se comprobó la proyección/shape, sin leer datos de
  otros cursos. Efecto persistente: solo schema, funciones, grants y ledger; sin
  backfill ni escritura de filas de cursos. El schema queda compartido con
  Certification por el proyecto Free; no hubo una operación separada contra un
  ambiente Certification. No repetir la migración.
- La discrepancia app/schema detectada antes de migrar quedó resuelta según el
  contrato verificado; no fue necesario un redeploy. No se operó Pro, Certification
  como destino, escritores, pipeline, FG3, schedules ni promoción.
- Integridad documental: permanece el FAIL integral histórico de 350 diagnósticos
  (349 comunes entre baseline/candidato) y, por separado, el PASS candidate-aware
  exacto del paquete. El merge no dispone ni convierte el FAIL integral en PASS;
  owner de reconciliación/disposición: TL/documentación. No se borraron relaciones
  ni se fabricó evidencia.

### R1–R4: matriz remota antes/después

Denominador fijo: 4. Antes de la pasada había **0/4 criterios aceptados con
evidencia remota del contrato corregido**. Después hay **2/4 = 50%**, delta
**+50 puntos porcentuales**. Las evidencias E1–E6 locales y la pasada MIN-01..06
anterior no se cuentan en esta matriz.

| ID | Criterio | Antes de la pasada | Después de la pasada actual | Tipo y evidencia |
|---|---|---|---|---|
| R1 | Colaborador corrige campo poblado, guarda, recarga y persiste. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | ACEPTADO. | Ejecución remota 2026-10-28. En editor colaborador se cambió `benefits`, guardó (toast correcto), v6→v7 y recargó; marcador exacto persistió. |
| R2 | Antes de publicar, visitante anónimo conserva el último snapshot aprobado. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | FALLÓ. | Ejecución remota 2026-10-28. Preview editorial conservó snapshot, pero ruta anónima dio HTTP 400/SQLSTATE `22P02` antes de renderizar. |
| R3 | Admin publica y visitante sin sesión ve el valor exacto nuevo. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | PENDIENTE. | No se publicó el marcador porque R2 reveló que la proyección pública está fallando; la acción aprobada no se consumió para exponer un cambio no verificable. |
| R4 | Historial/versión y preview distinguen borrador/publicado. | PENDIENTE; sin smoke remoto de este deployment. | ACEPTADO. | Ejecución remota 2026-10-28: diferencia draft/published visible, 8 eventos consultados, disclosure inicialmente cerrado y operable con teclado; insignia v8 32,6 × 26,1 px. |

- El JIT de prueba cubrió un único curso IDAT, `benefits`, la membresía colaborador
  existente, Admin existente y visitante aislado. La publicación de la marca solo
  habría ocurrido tras verificar R2; como la lectura anónima falló, no se hizo. El
  paquete cubrió la recuperación exacta, auditoría append-only y ningún otro campo,
  disponibilidad, membresía/rol, SQL, pipeline, FG3, schedule, deploy o promoción.
- Preflight UI sanitizado: `Python for Data Analyst`, ID
  `fd47da34-4a65-4a71-bc49-aea6db713500`, publicado, completo, versión v6. El
  campo `benefits` del snapshot y del preview publicado coincide con el original
  aprobado (SHA-256 `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`).
  La página anónima aislada muestra esos mismos cuatro beneficios antes del cambio.
  No se exponen datos de la cuenta colaboradora.
- Páginas de Chrome Windows: Admin página 1; visitante anónimo página 5; colaborador
  en página 6 de contexto aislado. La página 6 se enfocó con `bringToFront:true`; el
  responsable completó login. El editor mostró rol colaborador y no ofreció
  publicación ni administración de miembros. No se reinició onboarding/login.
- R1: el marcador literal fue
  `* [H3REQ1 CA4 — verificación temporal 2026-10-28]`; razón guardada
  `Validación temporal CA4 H3REQ1; restauración inmediata conforme JIT aprobado 2026-10-28.`
  El guardado desde DOM `fill` no habilitó el botón por el estado React; se repitió
  el mismo valor con interacción de teclado. Una primera entrada de razón tampoco
  habilitó el estado y no generó escritura; se completó con teclado y se verificó
  antes de guardar. El valor del marcador persistió después de recargar.
- R2: el lector público mostró el error funcional genérico de conexión. Network del
  pageId anónimo registró request `82`, status 400, body saneado:
  `{"code":"22P02","message":"invalid input syntax for type numeric: \"\""}`.
  Después de la recuperación, una sola comprobación del mismo lector registró
  request `116`, status 400 con el mismo error. No se consultó la fila operativa ni
  otros cursos. La probable causa está en la migración integrada, que hace cast
  directo de `published_editorial_values.price_pen` a NUMERIC cuando la propiedad
  está presente; la fila exacta que lo dispara no se verificó y no se afirma.
- Recuperación: el colaborador volvió a guardar exactamente el original de `benefits`
  (SHA-256 `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`),
  con razón `Restauración del valor original aprobado; recuperación de la verificación H3REQ1 conforme al JIT 2026-10-28.`; v7→v8. Admin comprobó v8 publicado y preview igual al original. No se despublicó: UI no mostró botón publicar al no existir diferencia entre borrador y snapshot. El público no confirmó la recuperación por el error de lectura; no hubo marcador público.
- R4: disclosure de `Historial de auditoría 8` inició cerrado. Al abrir se verificaron
  los 8 eventos disponibles, incluidas las dos escrituras y la publicación histórica;
  IDs de actor omitidos/sanitizados. Se cerró con Space y no quedaron eventos
  desplegados. Preview mostró snapshot publicado y advirtió que un borrador posterior
  requeriría publicación Admin. Insignia `Versión editorial 8`: 32,6 × 26,1 px.
- Acciones persistentes: dos ediciones autorizadas en `benefits` (marcador y
  restauración), dos eventos/aumentos de versión append-only; no se publicó el
  marcador ni se alteró disponibilidad/estado de curso. El JIT de prueba queda
  consumido. La migración inicial también queda consumida; no cubre la corrección.
- No hubo corrección remota, nuevas consultas a la DB, deploy, ni promoción. GO
  Development: **NO**. R1/R4 aceptados; R2 falló y R3 sigue pendiente. Las rutas
  públicas continuaron fallando por el error de tipo tras restaurar el contenido.
- El checkpoint siguiente documenta el paquete correctivo local y su contraste
  documental. R1–R4 no se repiten con este arreglo; una nueva pasada remota necesita
  un deployment compatible y JIT exacto independiente.

## Addendum — corrección de proyección pública y gates locales

**Continuación:** retomada desde el checkpoint a las 15:21:49 America/Lima;
reanudada en este turno a las 15:45:48. La hora final se completará al cerrar el
PR. El entorno es `codex/h3req1-public-price-projection-20261028`, basado
en el merge `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`. No se cambió el deployment
Development `27d9ebfc` ni el proyecto Free `aqrldlmlszjtgpqiegaa`.

### Corrección implementada

- La request anónima 82 del smoke R2 falló en la vista efectiva con SQLSTATE
  `22P02` por convertir texto vacío de precio a `NUMERIC`. La fila real no se leyó;
  el vínculo entre el error y el cast integrado está respaldado por el error y la
  definición SQL, pero el contenido exacto de la fila sigue sin verificarse.
- `db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql`
  reemplaza un único fragmento dentro de
  `private.h2_public_courses_effective()`. Solo admite texto decimal con hasta 63
  dígitos enteros y 63 fraccionarios; vacío, formato no decimal y texto mayor se
  proyectan como `NULL`. Valida existencia y ocurrencia exacta; aborta ante drift.
  Reafirma ACL actuales del lector. No toca cursos, snapshots, disponibilidad ni
  auditoría. Se aplicó dos veces únicamente en la base sintética PG17.
- El baseline sintético reprodujo `22P02` antes del guard. La versión corregida pasó
  con ocho filas: vacío, decimal normal, JSON null, texto inválido, decimal de
  63 dígitos, 131073 dígitos que exceden el rango, precio editorial sin snapshot y
  fallback de source legacy. También verificó grants anon/authenticated/service,
  ausencia de `PUBLIC EXECUTE`, `SECURITY DEFINER` y `search_path`.
- El test Python focal pasó `1 passed`; `bash -n` y ShellCheck `0.11.0` pasaron
  sobre el runner final. El primer ShellCheck detectó `SC2034` en el contador de
  readiness; el bucle se cambió a `_` y la revalidación pasó. El binario no existía
  en la imagen de desarrollo; se usó la imagen `koalaman/shellcheck:v0.11.0` ya
  presente localmente, sin red. Sin build frontend: el delta es exclusivamente SQL,
  harnesses y documentación.
- La migración correctiva no se aplicó a Supabase, y no se hizo deploy, publicación
  de curso ni otra prueba funcional remota. No hay nuevos efectos persistentes fuera
  de los commits/documentos locales. La migration requiere revisión y JIT remoto
  nuevo; la pasada R1–R4 anterior quedó consumida.

- Revalidación local de esta continuación: el harness PG17 volvió a pasar con ocho
  fixtures y dos aplicaciones de la migration; `tests/test_h3_public_price_projection_migration.py`
  pasó 1/1 en Docker; ShellCheck 0.11.0 pasó con `-x -P /src`; `actionlint` 1.7.12
  pasó el workflow; la regresión `tests/test_protected_path_scope_guard.sh` pasó con
  positivos y vecinos negativos; `git diff --check` pasó antes y después de este
  update. El checker candidate-aware R21/self-test se ejecutó
  otra vez en Docker después del último cambio documental y pasó: 747/747 fuentes
  asignadas, 119/119 docs activos alcanzables, 433/433 históricos enlazados, cero
  diagnósticos. El intento inicial de invocación ShellCheck omitía `-x` y dio
  únicamente SC1091; al seguir el source con `-x -P /src`, la validación pasó sin
  modificar código.

### Integridad documental

- El workflow `security-audit.yml` selecciona el manifiesto candidate-aware R21
  (`h3req1_public_admin_corrections_2026-10-26/candidate-scope-manifest-2026-10-26.json`)
  si el diff no cambia un manifiesto candidato. El mismo checker/configuración pasa
  en baseline merge (`742/742` fuentes, self-test PASS, 0 diagnósticos) y candidato
  (`747/747`, self-test PASS, 0 diagnósticos). Las cinco fuentes nuevas están
  asignadas al grupo de la migration correctiva.
- El checker integral sin manifiesto falla en baseline y candidato. Se capturaron
  todos los mensajes con el mismo checker/configuración y un ajuste de solo impresión
  en memoria para superar su límite de 200; el estado del checker y el algoritmo de
  validación no se modificaron. Cada árbol tiene 349 diagnósticos reales, 348
  idénticos. El único cambia por las cinco fuentes candidate-only añadidas:
  `299 != 367` en baseline frente a `304 != 367` en candidato. Por tanto el delta
  conserva el FAIL histórico y no reclama PASS integral.
- Logs íntegros:
  `/tmp/studiamatch-h3req1-doc-results/integral-baseline-exact.log` (SHA-256
  `0c2c76acfd4d1a0a549acdde24a470906df85e10ec7ee18ef383cc2d441c3398`) y
  `integral-candidate-exact.log` (SHA-256
  `6c995f7170899885e686bd13de837590d1f356f25fe1a9badad00d763acf7e5e`). Listas
  exactas de 349 errores y diff:
  `baseline-failures-exact.txt` (`dee27d01d01bc722ffa2db96c78e951ef7431bde4e121e41319e7a8ca4ea370c`),
  `candidate-failures-exact.txt` (`51189e74ec28d64f4e22c34c2daeeebc7496702dbd76bb84269d5afc26790b85`),
  `failure-delta-exact.diff` (`6b8aa40f4123df8e72dbf3bee61286bb05fee938bf9c39b038b08f73215a32cb`).
- La primera corrida candidate-aware encontró dos anclas rotas hacia
  `#corte-vigente`, por el cambio documental del título operativo. Se restauró el
  heading canónico `## Corte vigente`; la repetición del mismo gate pasó en baseline
  y candidato. No se borraron relaciones ni se inventaron archivos históricos.

### Estado, autorización y siguiente acción

- Baseline de código: merge real #508 `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`;
  rama aislada `codex/h3req1-public-price-projection-20261028`. El host Development
  mantiene el deployment previo `27d9ebfc` y continúa bloqueado por la lectura
  pública fallida; R1/R4 siguen aceptados, R2 falló y R3 no se ejecutó (2/4).
- Autorizaciones consumidas: solo harness sintético y validaciones Docker locales.
  Ningún JIT remoto nuevo, SQL remoto, escritura Supabase, cuenta real, FG3, writer,
  schedule, deploy o promoción se autorizó ni ejecutó en este delta.
- El scan Codex Security focal quedó completado: ID
  `b4f8c079-a0b5-489d-acae-d941bb1c31ec`, digest
  `codex-security-snapshot/v1:sha256:018d8d187e42a5e75e676c2e63784469c11066fb5e102381de200f93ea681db4`,
  cobertura completa de 15/15 paths, cero findings. El worklist del plugin enumeró
  cuatro paths; los once restantes se inspeccionaron manualmente y quedaron en el
  recibo `artifacts/manual-diff-review.md`. Delegación no disponible fue un warning
  de preflight, no un bloqueo: el agente revisó el diff completo. Reporte:
  `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-public-price-projection-20261028/77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3_20261028T204548Z_rko0su6k/report.md`.
- Pendiente: credential scan y compare-candidate del commit exacto, completar la
  plantilla de PR, commit, push no forzado y PR separado a `desarrollo`. Después
  del PR, detenerse; no mergear, desplegar, aplicar SQL remoto ni repetir R1–R4.

## Registro histórico del candidato y sus gates locales — previo al merge

**Corte:** 2026-10-28, America/Lima. Continuación iniciada a las 11:24:51 (-05:00);
este corte se actualizó a las 11:50:04 (-05:00). El checkpoint anterior cerró a
las 10:08:44 (-05:00). Todos los tiempos usan America/Lima.

## Baseline y estado

- Checkout aislado: `/tmp/studiamatch-h3req1-editorial-contract-20261028`.
- Rama: `codex/h3req1-editorial-contract-20261028`.
- Base: `desarrollo@f39a688f75531d190745225f11524414181ed425`; el HEAD local incluye
  la corrección `393d3543` y la actualización documental de este corte. El remoto
  del PR aún no incluye ninguno de esos commits.
- El primer commit del PR es `475f3dce36dd798035661b2c9190527b7f4712e9`. El
  follow-up `393d354303f0ee620b0199e89d2ed2d6f43cf634` corrige los dos fallos del
  primer CI; está comprometido localmente y espera push no forzado.
- PR #508 abierto hacia `desarrollo`: `https://github.com/romelhc95/studiamatch/pull/508`.
  El remoto aún muestra head `475f3dce36dd798035661b2c9190527b7f4712e9`; su primer
  run CI fue `40727339670`. Los dos fallos reproducibles se corrigieron en paths y
  clasificación de test exactos; no hubo aprobación ni merge.
- Deployment Development de referencia observado previamente: `d6e7b158-b26f-4504-b445-1facac915269`, host `desarrollo.studiamatch-aty.pages.dev`, SHA `f39a688f75531d190745225f11524414181ed425`. No hay deployment del candidato.
- No se modificó el WIP de otros checkouts. No hubo Supabase, SQL remoto, cuentas,
  sesiones reales, writers, schedules, FG3 remoto ni configuración remota.

## Matriz antes/después E1–E6

Antes: en el baseline `f39a688` no se encontró evidencia que probara los nuevos
comportamientos juntos; el permiso de edición User seguía restringido por
`missing_fields` y la proyección no separaba un snapshot editorial aprobado.
Las pruebas históricas no acreditan el contrato de esta matriz.

| ID | Criterio | Antes del cambio | Después y evidencia nueva | Estado |
|---|---|---|---|---|
| E1 | Colaborador corrige campo poblado, guarda/recarga y vuelve a corregir con auditoría. | Sin prueba del permiso nuevo sobre campos poblados. | Harness PG17 sintético: las dos correcciones persisten en borrador y cada una conserva auditoría/versionado. Log `harness-r4.log`; assertion en `tests/sql/h3_pg17_harness.sql`. | ACEPTADO local |
| E2 | Colaborador no publica ni administra miembros; anónimo rechazado. | Sin ejecución nueva del contrato revisado. | Harness PG17: rol User no puede publicar; anónimo no puede leer la RPC editorial; los RPCs de administración conservan el gate Admin. No se usaron cuentas reales. | ACEPTADO local |
| E3 | Admin publica; el público usa snapshot, que sobrevive borrador posterior, cambio de base/pipeline, expiración y `unknown`. | Sin separación verificada de borrador y snapshot. | Harness PG17: publicación toma la corrección; ediciones ulteriores no se filtran; vencimiento/unknown y cambios base no sustituyen el snapshot; una nueva publicación lo reemplaza. | ACEPTADO local |
| E4 | Versión obsoleta rechazada sin pisar ganador. | No se ejecutó el delta nuevo. | Harness PG17 devuelve conflicto de versión obsoleta y el valor ganador permanece. | ACEPTADO local |
| E5 | Fecha antigua, evidencia vencida y error transitorio no desactivan; retirada inequívoca sí, sin borrar fila. | FG3 podía desactivar por fecha base antigua. | `tests/test_integrity_ping_retirement_contract.py`, 4/4 en Docker: HTTP 503, HTTP 200, fecha antigua y availability vencida/desconocida no desactivan; 404 inicia gracia; 410 reiterado tras más de tres días desactiva sin borrar el curso. | ACEPTADO local, con límite semántico |
| E6 | Historial cerrado/teclado, versión compacta, preview draft/publicado, sin overflow desktop/móvil. | No se había probado el nuevo UI. | Ejecución nueva del candidato de la rama indicada arriba en Chrome Windows del puente; solo fixture sintético local `00000000-0000-4000-8000-000000000001`, servido por Docker en `http://localhost:38741/admin/edit/`. Historial inicialmente cerrado; Enter abrió y mostró el evento sintético; Space lo cerró. Preview mostró exactamente `CURSO SINTÉTICO EN BORRADOR` / `CURSO SINTÉTICO PUBLICADO`. Insignia `v7`: 32,6 px. Escritorio: document/client width 1428/1428; móvil emulado 390×844: 390/390, sin overflow. | ACEPTADO local |

Resultado local de la matriz nueva: antes **0/6** con evidencia del contrato nuevo;
después **6/6 = 100 %**, delta **+100 puntos porcentuales**. E1–E5 son evidencia
local aceptada del checkpoint anterior y E6 es ejecución nueva. Esos números
solo describen E1–E6 locales y no son aceptación remota, seguridad global ni avance
total de H3REQ1. El antiguo 6/6 MIN-01..06 no se reutiliza.

## Evidencia ejecutada y reusada

### Ejecución nueva

- Migration `db/migrations/20261028_h3_editorial_publication_snapshot.sql` aplicada
  dos veces en PostgreSQL 17 desechable y sintético dentro de Docker; pasa la
  idempotencia y el harness termina `h3_pg17_harness_ok`. Log:
  `/tmp/h3req1-editorial-pg17.CfjBsf/harness-r4.log`. El contenedor usa red `none`,
  filesystem PG temporal y fixtures montados de solo lectura; se retiró al terminar.
- Prueba FG3 aislada: `tests/test_integrity_ping_retirement_contract.py`, 4 passed.
- Suite de contrato Admin: `tests/test_h3_admin_queue_ux_contract.py`, reejecutada
  en fixture temporal del contenedor con `PYTHONDONTWRITEBYTECODE=1` y sin cache:
  13/13 PASS. El primer intento del fixture tuvo 11 PASS y 2 errores `FileNotFound`
  porque no incluía `web/functions`; se copió esa ruta desde este SHA y la repetición
  focal pasó completa. No se modificaron fuentes por ese error instrumental.
- `npm run lint`: 0 errores, 9 warnings preexistentes en `HomeContent.tsx`;
  `npx tsc --noEmit`: PASS; `npm run build:mock`: PASS y export estático de
  `/admin/edit/`; `node --check tests/h3_local_uat.mjs`: PASS. Build de Docker con
  acceso de red necesario solo para descargar las fuentes oficiales de Geist.
- Casos source-level y contratos estáticos actualizados, incluidos labels de draft
  y publicación y las nuevas aserciones E6. No se usaron como sustituto del navegador.
- E6 se hizo únicamente con el fixture UUID sintético
  `00000000-0000-4000-8000-000000000001` en
  `http://localhost:38741/admin/edit/`; la respuesta de sesión, curso y auditoría
  fue simulada en memoria. No se emitió RPC de escritura, no se usó cuenta real ni
  pestaña remota. El viewport móvil se emuló en la misma pestaña Windows porque el
  tamaño mínimo de ventana del sistema impedía reducirla a 390 px. La emulación
  recargó el fixture en login; se reinyectó el mismo stub local y se continuó sin
  repetir autenticación. Chrome Windows no permitió guardar una captura en la ruta
  `/tmp` propuesta; la evidencia conservada es DOM/ARIA, resultado de teclado y
  medidas de viewport reproducibles.
- Documentación integral comparada con el mismo checker sin red, misma imagen Docker
  y configuración: baseline `f39a688` y candidato ambos FAIL con 350 diagnósticos
  completos; 349 son idénticos. El inventario se generó con el checker de la misma
  versión en un árbol diagnóstico temporal cuyo único cambio elimina el límite de
  impresión de 200 líneas; la lógica y parámetros de validación no cambian. Se
  confirmará el resultado integral otra vez con el checker original al cierre. El
  único texto que cambia es el contador heredado
  `INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT` (baseline `297 != 367`, candidato
  `299 != 367`) porque el paquete añade dos rutas candidate-only. Los logs completos,
  lista exacta de errores y hashes quedan en
  `/tmp/h3req1-editorial-doc-logs/baseline/diagnostic.log` y
  `/tmp/h3req1-editorial-doc-logs/candidate-diagnostic.log`; las listas exactas y el
  diff están en `baseline/failures-exact.txt`, `candidate-failures-exact.txt`,
  `introduced-failures-exact.txt` y `resolved-failures-exact.txt` bajo ese directorio.
  La lista candidata tiene SHA-256
  `40afdbb5c700d9c18443e6c783307efde32fc3ddc3abeeeee18518066175a0bd`.
  Las clases comunes son `CANDIDATE_ONLY_PATH_MISSING` (79), `RELATION_PATH_MISSING`
  (88), `SOURCE_PATH_MISSING` (79), `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE` (79),
  `EXCLUSION_PATH_MISSING` (15), `DOCUMENT_EXCLUSION_PATH_MISSING` (4),
  `DOC_EXCLUSION_STALE` (4), `DOC_SELF_TEST_FAILED` (1) y un contador de proyección.
  El modo integral permanece FAIL; no se borraron ni fabricaron fuentes históricas.
- El proyecto define `--candidate-manifest` como gate candidate-aware en
  `security-audit.yml`. El manifiesto exacto del paquete está en
  `.context/evidencia/h3req1_editorial_contract_candidate_scope_2026-10-28.json`,
  SHA-256 `819bcc3d7f33883990e23af97b9863afe4cf9b5ca3e35d3672b78be1a4359bde`.
  La corrida final con la nueva entrada del inventario Python pasó: 742/742 fuentes
  asignadas, 119/119 documentos activos alcanzables, 433/433 históricos enlazados;
  self-test y gate PASS. El manifiesto coincide exactamente con las 28 rutas del PR.
  Este resultado acotado sigue separado del FAIL integral.
- El gate integral del proyecto sigue FAIL (exit 1), tanto en baseline como en el
  candidato. No se oculta ni sustituye por el PASS candidate-aware. Ambos árboles
  tienen 350 diagnósticos completos; 349 son idénticos. El delta solo cambia el
  contador de proyección candidate-only (`297 != 367` a `299 != 367`) por las dos
  rutas candidate-only añadidas. No se quitaron relaciones ni se inventaron archivos.
  El checker original imprimió sus primeros 200 mensajes y el resumen de 150 más;
  inventario exacto generado con la misma versión y lógica, sin límite de impresión,
  está en `/tmp/h3req1-editorial-doc-logs/` y su SHA figura arriba. Corridas oficiales:
  `/tmp/h3req1-editorial-final-logs/baseline-integral.log` y
  `/tmp/h3req1-editorial-final-logs/candidate-integral.log` (exit 1/1).
- Guard final validado en Docker sin red con worktree/Git común en solo lectura:
  `bash -n` PASS; `tests/test_protected_path_scope_guard.sh` PASS, incluyendo paths
  exactos del paquete, vecinos negativos y selector de manifests; inventario base
  de 1.196 paths, 13 catálogos/1.173 referencias. ShellCheck 0.11.0 PASS sobre el
  conjunto completo del job `actionlint And shellcheck` (siete archivos) desde la
  imagen local en caché. `git diff --check` PASS.
- Scanner versionado de credenciales del delta pasó para las 28 rutas, en Docker sin
  red. Compilación Python focal de `integrity_ping.py` y su prueba: 2/2 módulos PASS.
  JSON válido; candidate-aware consumió el mismo manifiesto que selecciona el workflow
  CI. El gate integral obligatorio antes de integrar sigue sin resolver por referencias
  históricas y no se declara PASS.

### Evidencia reutilizada

No se repitieron D01–D14, onboarding, invitación, recuperación, cuotas ni pruebas
remotas. No se acreditan como aceptación nueva.

## Acciones persistentes y fallos corregidos

- Efectos persistentes: solo código y documentación del worktree local. No se
  escribieron datos de aplicación; el harness SQL solo usó una base PG17 efímera.
- El guard y su regresión admiten solo las rutas nuevas exactas del paquete. Se añadió
  el manifiesto candidate-aware como path exacto; su vecino negativo continúa rechazado.
  No se ampliaron patrones de carpeta, workflows, permisos ni controles remotos.
- El primer CI del PR encontró dos omisiones atribuibles al delta. `Protected Path
  Integrity` rechazó `web/src/components/admin/CourseLivePreview.tsx` y
  `web/src/components/admin/editorial-ui.tsx`, ausentes del allowlist local de paths
  protegidos. Se añadieron esos dos paths exactos y vecinos negativos. `Python Compile
  And Tests` tuvo 251 PASS y un FAIL porque el test FG3 nuevo usa el cliente Supabase
  bajo fixture y no estaba en `DIRECT_SUPABASE_CONSUMERS`; se clasificó como
  `supabase-data-api-test`. La suite focal local pasó 45/45 en imagen Docker con
  pytest; el compare-candidate y su regresión también pasaron con los nuevos exactos.
  El commit correctivo `393d354303f0ee620b0199e89d2ed2d6f43cf634` está comprometido
  en el checkout local; los checks focales post-commit pasaron en Docker sin red:
  guard/compare-candidate, 49/49 tests Python de los dos contratos afectados y scan
  de credenciales. El gate candidate-aware documental también pasó para el manifiesto
  exacto. El commit aún no se ha enviado y GitHub debe reevaluarlo.
- El primer arranque de PG17 no tenía el modo de autenticación de test requerido;
  se corrigió solo el comando del contenedor. La siguiente ejecución encontró una
  función JSONB no disponible en PG17 y una colisión de fixtures; se corrigió el
  harness sintético y el r4 final pasó.
- La prueba FG3 inicial no tenía `supabase_credentials.py` en su fixture y el fake
  DB esperaba un filtro no usado por la ruta de lectura; se completó el fixture y se
  alineó la expectativa con el lector ilimitado de cursos. Revalidación: 4/4.
- El primer build offline no pudo descargar Geist; además la primera copia Docker
  no montaba `eslint.config.mjs`. Se repitió en Docker con el config presente y red
  solo para fonts: lint/types/build pasaron.
- Sin defecto de producto confirmado por esos fallos instrumentales.

## Seguridad, autorizaciones y límites

- Autorización vigente: implementación/tests Docker/PG17 y commit, push no forzado
  y PR a `desarrollo`, ya consumidos solo para esta feature. PR #508 está abierto.
  El delta correctivo local de 28 rutas pasó los gates focales indicados arriba. La
  acción exacta pendiente es push no forzado del commit `393d3543` y lectura de CI
  para el nuevo SHA.
  La rama protegida no se modificó.
- No autorizados ni ejecutados: aprobación de review, merge, SQL/migración remota,
  Supabase writes, interacción de cuenta real, FG3/pipeline/schedule, deploy manual,
  promoción y pruebas de negocio remotas.
- Revisión Codex Security formal completada: scan diff
  `a39fcd65-8774-40dc-afdf-75ff8654cd52`, snapshot
  `codex-security-snapshot/v1:sha256:9b4506019b938300c6df6a540818c7fa253b01f6d1f9dea43731d12d9222b03b`,
  cinco superficies, cero candidatos/reportables. El resultado corresponde a ese
  snapshot; la herramienta advierte que cambió el worktree mientras corría. Los ajustes
  posteriores de allowlist/inventario son paths/providers exactos, sin ampliar permisos
  de runtime: revisión estática focal, regresiones positivas/negativas y ShellCheck PASS.
  No es escaneo global ni validación remota. Reporte:
  `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-editorial-contract-20261028/f39a688f75531d190745225f11524414181ed425_20261028T132753Z_9o66ixd8/report.md`.
- Revisión focal del delta de seguimiento `475f3dce..393d3543`: los únicos cambios
  de seguridad agregan tres rutas H3 exactas al allowlist, mantienen tres vecinos
  negativos, clasifican el test FG3 como consumidor Data API y lo incluyen en el
  manifiesto candidate-aware. No alteran permisos de runtime ni writers. La revisión
  estática de ese diff se respalda con guard/compare-candidate, scan de credenciales,
  ShellCheck y 49/49 pruebas focales PASS en Docker sin red; no se declara un segundo
  scan formal para este ajuste acotado.
- La vista usa `security_invoker`; la guía oficial de
  [Supabase Views](https://supabase.com/docs/guides/database/views) confirma que
  ese modo comprueba permisos/RLS del rol lector sobre las tablas subyacentes. La
  herramienta no abrió `changelog.md` por su `text/markdown`; el delta no adopta una
  API Supabase nueva.
- Límite FG3: HTTP 200 prueba respuesta HTTP, no pertenencia vigente al catálogo.
  Retirada semántica de páginas 200 queda trazada a H1; no construir crawler en H3.

## Transición y recuperación

- **Expand:** aplicar primero, con JIT DB nuevo, la migration forward-only que crea
  columnas snapshot nullable; no requiere backfill masivo. Mantener firmas/grants y
  compatibilidad de cursos sin snapshot.
- **Compatibilidad:** la lectura conserva el fallback legacy; la primera edición
  captura el valor público anterior antes de separar el nuevo borrador.
- **Deploy:** solo tras revisión/aprobación y autorización separada, aplicar la
  migration en el ambiente objetivo antes del deployment de la app compatible; luego
  hacer el smoke remoto mínimo aprobado: colaborador corrige campo poblado, Admin
  publica, visitante anónimo ve el valor, vencimiento/unknown conserva snapshot,
  historial y versión funcionan. La prueba remota no se autoriza en este ciclo.
- **Contract:** mantener snapshot como fuente pública; retirar la dependencia de
  disponibilidad para proyecto nuevo tras estabilidad y evidencia remota, en un
  paso de promoción separado. La retirada por HTTP 200 sigue fuera de cobertura.
- **Rollback:** restaurar código/RPC de la última versión compatible por deploy o
  migration correctiva; conservar las columnas y eventos append-only. No borrar
  snapshots, filas ni historial con rollback.

## Diferidos y siguiente acción exacta

1. **Revisión del gate documental integral** — owner TL/documentación; riesgo:
   350 referencias históricas/checks del baseline siguen rojos. Punto de revisión:
   antes de integración; el gate CI candidate-aware del paquete es independiente y
   debe pasar. Acción: reconciliar con fuente histórica o disposición canónica, sin
   quitar relaciones ni inventar archivos. El integral no se registra PASS.
2. **Revisión humana y promoción** — owner TL; antes de merge se revisan migración,
   transición y resultados CI. Migración remota, merge, deploy y smoke remoto requieren
   autorización separada y siguen pendientes.
3. **Retirada semántica HTTP 200** — owner H1; riesgo: un URL vivo puede mostrar una
   página que ya no lista el programa. Punto de revisión: diseño/ingesta H1; sin
   crawler universal ni waiver en este paquete.
