# Checkpoint local — contrato editorial H3REQ1

## Continuación 2026-10-31 — corrección del diagnóstico H2 y scope main WIP

Tras login Pro asistido y recarga MCP se confirmó el project ref
`xwhtiqmboljkshrtviyw`. Todas las consultas siguientes fueron SELECT de metadatos
o agregados; sin IDs de curso, filas Auth, secretos, RPC ni writes.

El ledger interno `supabase_migrations.schema_migrations` tiene 23 entradas,
última `20260607221002`. Ese ledger NO es el consumido por nuestro migrador.
El ledger correcto `public.supabase_migrations` tiene 58 entradas y registra
las cinco migraciones `h2-expand-compat`; cero registros H3. Se corrige la
inferencia histórica de H2 parcial/no registrado. No reaplicar ni insertar ledger
por ese diagnóstico anterior. La cohorte elegible, la capturada y el reader
efectivo leído como administrador cuentan 224; digest elegible/capturada idéntico
`sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`;
ceros en las cuatro diferencias de conjuntos. No equivale a prueba anon ni a
workflow verify sobre candidato actual. La evidencia main sigue requiriendo
renovación real; los objetos Admin/RPC, quota, gateway y snapshot H3 siguen
ausentes. No se ejecutó apply.

Scope main: 239 rutas rechazadas coinciden exactamente con el manifest histórico
de Certification; todos sus blobs/modos siguen idénticos a Certification y
source histórico. WIP separado de base `6d73b51b…`: manifest main exacto,
caller de ruta protegida y regresiones. La revisión estática detectó una prueba
push que retenía refs de PR; se corrigió para vaciarlas y añadir negativos de
baseline/ref de push ajeno. Tras recuperación Docker asistida, regresiones/caller
real y comparación main PASS; ShellCheck 0.11.0 PASS; 46 tests Python focales PASS;
scanner PASS; render y candidate-aware/self-test PASS, 752/752 fuentes,
119/119 activos y 433/433 históricos. La revisión estática posterior confirmó
hallazgo resuelto, sin hallazgos abiertos del alcance. No se repite UAT.
Se consolida fix DB Sync y main scope en una rama local; los pins Certification
se renuevan sobre su commit inmutable validado antes de publicar. Sin GO remoto.

## Corrección P1 DB Sync y prevención de nuevo drift de pins

Hallazgo validado en #514:
https://github.com/romelhc95/studiamatch/pull/514#discussion_r4425547640
El bloque `Validate closed Pro manifest offline` exigía el literal
`h3-editorial-expand` en `db_migrate.py`, que lo importa de otro módulo.
Reproducción Docker offline/read-only: missing `['h3-editorial-expand']`, exit 1.
CI ordinario no ejecutaba ese bloque manual y no detectaba el defecto.

Fix aislado desde `b9eb77185f1a037111ce1237820ae6c38b15ea67`: mover, sin cambiar
su contenido, el registro Pro al módulo stdlib existente y consumir el mismo
registro desde migrador y preflight. Workflow coteja conjunto cerrado, tuple
no vacío/único, rutas SQL existentes y pins H3. No importa requests/dotenv ni
clientes DB. Los guards de apply, JIT, main-only H3 y backup permanecen activos.

`tests/test_h2_pro_migration_controls.py` extrae y ejecuta el bloque real del YAML:
seis manifests válidos, cuatro selecciones inválidas, registro alterado, archivo
H2 ausente y hash H3 distinto; prueba aislada `-I -S` sin dependencias. Suite
focal Docker 87/87 PASS (controles H2, manifest H3, credenciales y boundary).
Suite Python exacta de CI: 276 passed/10 subtests passed. Scanner de credenciales
y regresiones de scope/selector/pins PASS; actionlint 1.7.12 PASS. Self-test y
candidate-aware: DOC_GATE_PASS, 752/752 fuentes, 119/119 activos y 433/433
históricos. Security-auditor revisó estáticamente el diff funcional: cero
hallazgos, registros/orden equivalentes y guards JIT preservados; no ejecutó
tests independientes ni incluyó documentación/pins en ese dictamen.
No es runtime Pro ni aplicación SQL. No se repite ninguna aceptación remota.

El refresh de pins usa el commit local inmutable del código corregido para fijar
sus blobs; guard/manifiesto/checkpoint de la actualización quedan en sus rutas
exactas, sin excepciones de carpeta. No se elimina la validación de hashes.
La revisión/CI del nuevo SHA y la disposición exacta del residual son gates
posteriores; #514 no queda aprobado para merge por este fix local.

## Remediación focal CI del PR #512

El HEAD publicado inicial `c6bd818821c41727cd217d352990343ebe23cedf` falló en
`Python Compile And Tests` (un fallo de inventario, 261 tests PASS) y
`Protected Path Integrity` (rutas fuera del matcher). `security-audit` fue
consecuencia. Las URLs de evidencia son los jobs `123876652432` y
`123876652518` del run `40998348079` en `romelhc95/studiamatch`.

Causa: dos módulos de test nuevos contienen patrones de transporte Supabase y
faltaban del inventario exacto. Ocho paths ya incluidos en el paquete estaban
fuera del matcher H3; el fallback legacy tampoco cubría la unión. La corrección
registra únicamente los fixtures como `supabase-pattern-test-only`, agrega ocho
rutas exactas al matcher y prueba vecinos rechazados. No se altera transporte,
credenciales, scanner, SQL ni comportamiento del producto.

Revalidación local Docker sin red y con source read-only: 95 tests de contrato
de credenciales y controles H2/H3 PASS; suite Python exacta de CI 262 tests/10
subtests PASS; revisión de seguridad estática sin hallazgos; shell de scope, selector y pins PASS;
`--compare-candidate` contra la base real `6f059a0b…` PASS. Son resultados locales,
no acreditan el próximo CI. El contenido original aprobado y su disposición
permanecen como historia; la corrección debe identificarse por su propio delta.


## Actualización final del paquete H2/Pro y cierre de remediación local — 2026-10-29 18:57 America/Lima

Este corte supersede los estados anteriores de esta nota. Para la disposición
documental vigente rige únicamente la propuesta del 2026-11-05 23:59 America/Lima,
limitada al residual probado y a permitir solicitar integración protegida a
`desarrollo`; no autoriza producción. Esta es la única propuesta vigente. Las
propuestas de promoción/producción incluidas en cortes posteriores son
históricas y quedan supersedidas; la disposición #509 del 04/11 está consumida,
no se extiende y no resuelve esta huella.

### Estado e inventario

Worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, base/HEAD
`6f059a0b27ef38541a7b62503c78920e621f05c1`. Estado en este corte: 30 paths,
25 modificados y 5 nuevos. El fingerprint estable final, el inventario y los
hashes por archivo se fijan fuera del árbol en
`/tmp/h3req1-production-remediation-20261029-final/`; la propuesta de revisión
se vincula a esos bytes. No se creó commit ni se publicó. Se preservó el WIP de
los otros checkouts.

### Remediación H2/Pro

`scripts/maintenance/h2_pro_preflight_report.py` separa ahora el diagnóstico
read-only de la autorización de apply. Clasifica baseline previo a H2, objetos
H2 parciales fuera del ledger, superficie pública compatible observada,
inconsistencias de ledger/schema y errores de lectura. El estado parcial
observado produce agregados y `REVIEW_REQUIRED`, sin líneas para el futuro JIT;
los estados inconsistentes o errores producen `INCOMPLETE`/`READ_ERROR`. La
superficie compatible no afirma esquema privado completo ni ejecución de la
RPC de verificación. `apply_authorized=false`,
`application_decision=NOT_AUTHORIZED`; no invoca RPC, SQL, DML ni backfill.
Los guards del migrador no cambiaron. El digest etiquetado como cohorte
elegible se calcula sobre IDs elegibles ordenados, no sobre el conjunto público
cuando hay divergencia.

Pruebas en Docker de proyecto, red deshabilitada, árbol read-only: **29/29**
casos del reporte más quince controles/regresiones de lectura/paridad/migrador,
**44/44 PASS**. Se confirma en subprocess que los mensajes de carga del cliente
quedan en `stderr`, para que el artefacto del workflow contenga JSON limpio.
Dos regresiones de agregación confirman que una fila no forma un grupo
duplicado y que dos cursos con igual institución/slug sí forman uno. Tres grupos
de pruebas verifican que GET/RPC no siguen redirects HTTP, incluidas las cinco
llamadas directas en la ruta de paridad de schema, y que las probes de privacidad
H3 fallan cerrado ante HTTP 302/500. Esto evita reenviar `apikey` a otro origen
y tratar errores transitorios como prueba de privacidad. La lógica de duplicados
ya era correcta. Log de pruebas SHA-256
`2bd78775f382ddb2b7640e87a241317b320cbe2badaea3ff041c0eb404ee7ae8`;
`py_compile` separado SHA-256
`70dfa6a2bf0032db1311a455aa076b1fd8cefc461c31853a91323661f6f9dfd9`.
Cubren
baseline, H2 parcial sin registro, superficie compatible como observación,
ledger/schema inconsistente, visibilidad pública divergente y errores HTTP,
red, JSON y payload con forma inválida, sin reflejar filas o mensajes sensibles.
El reporte rechaza URLs con esquema, host, credenciales, puerto, ruta, query o
fragmento ajenos al origen canónico Pro; acepta HTTPS con puerto implícito o 443,
con ruta vacía o `/`.
`py_compile` de lector y tests: PASS. Logs exactos y SHA-256 en
`final-checksums.txt` externo. No se ejecutó el reporte contra Pro ni se repitió
el preflight remoto previo.

### Contrato del reporte y autorización pendiente

El preflight futuro tiene dos privilegios de lectura: publishable para el GET
público `courses?select=id` (solo filas visibles por RLS), y service key del
environment Production para paginar todas las filas de `courses` con columnas
`id,institution_id,slug,is_active,is_verified,url`, todas las filas de
`institution_site_profiles` con `institution_id,production_enabled,notes` y
los nombres de `supabase_migrations`. También hace `limit=0` para comprobar la
existencia de tres tablas públicas H2 y `courses_public_effective`; solo si
existe `crawler_exclusions`, consulta como máximo `id` de una fila. El service
key evade RLS; esas lecturas de filas operativas requieren JIT aunque no haya
escrituras.

El proceso compara internamente IDs y URLs, pero el JSON solo expone conteos,
digest SHA-256 de IDs elegibles ordenados, nombres del manifiesto H2, presencia
booleana, bloqueadores con cantidades y errores sanitizados. No imprime filas,
IDs, slugs, URLs, notas, cuerpos HTTP, secretos ni valores de API keys. No
consulta esquemas privados, invoca RPC, escribe archivos en la base ni hace
DDL/DML/backfill. La importación del cliente queda en `stderr`; `stdout` se
reserva para JSON. El workflow captura el reporte como artifact por 30 días y
ejecuta después un dry-run del migrador (conteo/lista de pendientes), sin apply.
Para el JIT futuro: `workflow_dispatch` en ref `certificacion`, `operation=report`,
`migration_manifest=h2-expand-compat`, `candidate_sha` igual al SHA integrado
vigente, `payload_sha` igual a ese SHA, `apply_authorized=false`,
`backup_pitr_verified=false`, `ddl_authorization_id` vacío,
`h2_expected_eligible_count=0` inerte, digest vacío y
`h2_advisors_reviewed=false`. Es una solicitud de lectura report-only, no un
JIT de aplicación. La solicitud revisable completa está en el checkpoint
externo `approval-requests.md`; permanece pendiente y no fue ejecutada. La SHA
debe fijarse al presentar la solicitud, no se anticipa con una rama local.

### Gate documental y disposición propuesta

El checker integral se mantiene visible con 350 diagnósticos en baseline y 348
en candidato bajo los mismos bytes/configuración, sin diagnósticos candidatos
exclusivos. El checker tiene SHA-256
`f2a95870de748b2e59ee0d988abb0b16125da47c996a7f85841f1113fcebbb75`. Los logs
oficiales y full-list exactos están en `final-checksums.txt`; el self-test/
candidate-aware se reporta por separado y no convierte el FAIL integral en
PASS. Los dos diagnósticos baseline-only se resolvieron y no hubo diagnósticos
nuevos únicos. Los 348 restantes son deuda histórica de trazabilidad; no se
recrearon documentos privados, no se borraron relaciones masivamente y no se
rebajó el checker.

Disposición propuesta, **no aprobada**: huella y logs finales exactos del
paquete; causa: referencias históricas sin fuente autorizada y proyección
candidate-only incompleta; riesgo: trazabilidad histórica incompleta, sin
evidencia de impacto funcional causada por los residuales; owner propuesto
Romel/TL; vencimiento único propuesto **2026-11-05 23:59 America/Lima**. El
alcance solicitado es únicamente reconocer ese residual para poder solicitar
integración protegida a `desarrollo`. No autoriza commit, push, PR, review,
merge, promoción, SQL, workflow, configuración ni deploy. Las disposiciones
#509/#510/#511 no aplican; la fecha #509 04/11 corresponde a una disposición
consumida e histórica. No hay propuesta vigente para `certificacion→main` ni
para producción.

### Revisión de seguridad del diff

Codex Security terminó una revisión diff-scoped del candidato: scan
`c28d2808-5a58-4342-8284-54715649cb95`, snapshot
`codex-security-snapshot/v1:sha256:22f4ea54b05873332bff3d8130c225d6428180ee408ba0a546051093697d02e5`,
12/12 ítems cubiertos, cero hallazgos y cinco superficies sin issue. El reporte
canónico está en
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/6f059a0b27ef38541a7b62503c78920e621f05c1_20261029T235250Z_f_kxu_b3/report.md`.
No es auditoría global ni demuestra grants, esquema o runtime Pro. Se ejecutó
antes de esta edición de cierre; después solo se cambian documentos y borradores,
no código. La huella/hash final se conserva en el checkpoint externo.

### Criterios aceptados, límites y siguiente acción

E1–E6 local **6/6**, Development R1–R4 **4/4** y smoke Certification **1/1**
continúan aceptados y no se repiten. La lectura Pro previa (23 migraciones;
H2 parcial fuera del ledger) se conserva, sin nueva lectura. No se acredita SQL
aplicado, compatibilidad runtime Pro ni aceptación productiva. H2 report/verify,
SQL H3, Pages/BFF, promociones protegidas y smoke con recuperación requieren
autorizaciones independientes. H1 sigue sin FG1/FG2/FG3 ni schedules; H4 sigue
dependiendo de contrato H2 y secuencia H2→H3→H4.

**Siguiente decisión:** revisar el paquete y decidir la disposición propuesta.
Si se aprueba, emitir una autorización separada para commit, push no forzado y
PR a `desarrollo`. No ejecutar acciones remotas con este cierre local.

## Corte anterior — supersedido, 2026-10-29 15:18 America/Lima

**Candidato:** worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`,
rama `codex/h3req1-production-remediation-20261029`, base/HEAD
`6f059a0b27ef38541a7b62503c78920e621f05c1`. El inventario final tiene 27 paths
(23 modificados, 4 nuevos), más amplio que el delta anterior de 13. La lista
ordenada y SHA-256 por ruta se conserva fuera del repositorio en
`/tmp/h3req1-production-remediation-20261029-final/candidate-fingerprint.txt`;
el hash de la huella se incluye en el borrador externo de PR para evitar
autorreferencia. Sin commit, push, PR, merge, SQL, workflow, configuración
remota ni deploy. WIP de otros checkouts preservado.

**Criterios aceptados y no repetidos:** E1–E6 local 6/6, Development R1–R4 4/4
y smoke Certification 1/1 siguen aceptados. No hay checks CI del candidato
porque no se abrió PR. No se reejecutaron smoke, onboarding ni cuotas.

**Gates locales afectados:** con la imagen del proyecto
`studiamatch-h3req1:sync-a57bc415-rebuilt-20261018` y red Docker deshabilitada,
el manifest H3/orden/hashes, entradas inválidas, selector `certificacion→main`,
pins, regresión de interpolación Bash, H2/paridad/boundary, CA4.6, guard,
TypeScript y ESLint pasaron. El rerun final Python de manifest H3, H2/paridad
y boundary fue 21/21 en 0,23 s; CA4.6 Node 1/1 y el test de host Pro 8/8 en
el rerun con cacheprovider deshabilitado. `tests/test_protected_path_scope_guard.sh`
volvió a pasar selector `certificacion→main`, pins positivos/negativos y
rechazo fail-closed de la regresión Bash.
El primer credential scan marcó el identificador/valor sintético del fixture,
no una credencial; el fixture ahora evita patrones de credenciales y el escaneo
exacto de los 27 paths pasó. El self-test con manifest
candidate-aware sobre el árbol actualizado pasó 751/751 fuentes, 119/119 docs
activos y 433/433 históricos. El recheck final volvió a dar candidate-aware
PASS. Sin manifest, el checker oficial terminó exit 1 con 200 diagnósticos
impresos y 148 resumidos; el runner diagnóstico externo, que conserva la
lógica y aumenta el límite de impresión, confirmó los 348. No fue fallo de
self-test. El credential scan exacto de 27 rutas pasó. Tres intentos
instrumentales no cuentan como tests: bootstrap detenido por node_modules
desincronizado; `/usr/bin/python3` sin pytest, antes de colección; y pytest del
venv sin `PYTHONPATH`, con error de importación durante colección. La corrida
válida usó entrypoint explícito, el venv `/opt/venv/bin/pytest` y
`PYTHONPATH=/app`. No se cambiaron permisos del socket ni se modificaron
contenedores o volúmenes ajenos. Los logs y hashes exactos se registran en
`final-checksums.txt` externo.

El build estático Next 16.3.8 terminó PASS en una copia de `/tmp`, con el modo
mock local que ya soporta la aplicación (`NEXT_PUBLIC_H3_MOCK_URL` y
`NEXT_PUBLIC_H3_ALLOW_MOCK_BUILD=true`), generó 17 páginas y no contactó
Supabase. La descarga pública de Geist fue el único egress de la build. Esto
valida compilación/export sintéticos; no es smoke, deployment ni runtime Pro.

**Seguridad del diff:** revisión Codex Security successor completa, 11/11
superficies de seguridad relevantes cubiertas, 0 findings, snapshot
`codex-security-snapshot/v1:sha256:c74d9d9a6abcb1ba90230e9e5e0d4d3268b1f91e504f3c66fc96dfa53a4048d2`,
scan `ae623b31-4065-4f73-8811-cbde81cd39be`. Reutilizó revisiones exactas para
bytes sin cambios; no es auditoría global ni valida runtime, Pro o Production.
El scan anterior encontró dos mejoras de hardening (host canónico Pro y
aserción independiente de fuentes Docker) que ya están parcheadas localmente y
se verificaron en el successor. Reporte sellado bajo
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/`.
El único cambio posterior al snapshot fue la cadena de un fixture de test para
evitar que el credential scanner la interpretara como valor sensible; la
lógica de aplicación quedó idéntica. Ese delta fue revisado manualmente, el
módulo afectado pasó 8/8 y el credential scan exacto de 27 rutas pasó.

**Gate documental, separado por alcance:** self-test/candidate-aware PASS;
checker integral oficial FAIL con 348 diagnósticos candidatos contra 350 en
baseline usando el mismo checker/config. Los dos diagnósticos baseline-only se
corrigen; no aparecen diagnósticos únicos nuevos. Los residuales se agrupan en
79 paths candidate-only repetidos en tres categorías, 88 relaciones sobre 20
paths únicos, 15 exclusiones locales/generadas y 8 referencias a cuatro
documentos privados excluidos con sucesores sanitizados. No se recrearon
fuentes, copiaron documentos privados ni retiraron relaciones masivamente.
Disposición productiva **propuesta y no aprobada**, solo para la huella/log
final de este paquete; owner Romel/TL; riesgo de trazabilidad histórica
incompleta; vencimiento propuesto 2026-11-05 23:59 America/Lima o antes del
primer merge `certificacion→main`, lo que ocurra primero. Las disposiciones de
#509/#510/#511 no la cubren. Candidate-aware PASS no sustituye el FAIL integral.

**H2/Pro y configuración:** se reutiliza la lectura SELECT-only de Pro
`xwhtiqmboljkshrtviyw`: 23 entradas de ledger, objetos H2 parciales fuera de
ledger, cohorte agregada todavía no leída, y faltan objetos snapshot/Admin/H3.
El report H2 existente aborta antes de imprimir agregados por el drift parcial;
requiere corrección local read-only y pruebas antes de que se decida un
`workflow_dispatch report/verify`. No reaplicar H2 por ledger ni invocar
funciones. Manifest H3 de 31 migrations preparado localmente, sin DDL ni
workflow. Pages Production conserva pendientes de host Admin, tres HMACs
distintas, key id respaldado por Pro y binding `ADMIN_QUOTA`. El valor de
`NEXT_SUPABASE_SECRET_KEY` no se leyó; `plain_text` por sí solo no prueba
exposición y no se halló consumidor Pages local. Sin cambios remotos.

**Resultado:** NO-GO de publicación e integración hasta remediar el gate
integral o aprobar una disposición nueva para esta huella. Después requieren
autorización separada commit/push no forzado/PR hacia `desarrollo`; H2
report/verify, workflow de SQL H3, Pages/BFF, promociones protegidas y smoke
Production son gates distintos. H1 no habilita FG1/FG2/FG3 ni schedules; H4
permanece pendiente de contrato H2 y secuencia H2→H3→H4.

## Corte anterior — histórico, 2026-10-29 después de 14:31 America/Lima

## Revalidación del paquete ampliado y cierre local — 2026-10-29, después del corte 14:31 America/Lima

**Candidato e inventario:** worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`,
rama `codex/h3req1-production-remediation-20261029`, base/HEAD
`6f059a0b27ef38541a7b62503c78920e621f05c1`; 27 paths (23 modificados, cuatro
nuevos). No hubo commit, push, PR, merge, SQL, workflow, configuración remota ni
deploy. La huella final y logs completos se guardan fuera del repo en
`/tmp/h3req1-production-remediation-20261029-final/` para no autorreferenciar el
inventario.

**Gates Docker nuevos:** la imagen existente del proyecto
`studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, red deshabilitada, validó
20/20 pruebas Python (manifiesto H3/orden/hashes, selección y entradas inválidas,
guardas H2/paridad, controles de promoción a `main` e interpolación Bash), 1/1
prueba Node CA4.6, guard/selector/pins con positivos y negativos fail-closed,
`tsc --noEmit` y ESLint del editor. La dependencia npm se montó read-only desde
el volumen preexistente; el typecheck usó cache en `/tmp`. El primer typecheck
falló solo por intentar escribir ese cache en una copia read-only y se repitió
con el destino externo: solo cuenta el segundo. `git diff --check` y credential
scan se anotan en el checkpoint externo después del rerun final. actionlint y
ShellCheck son reutilizados, no reejecutados, porque sus inputs no cambiaron.
El primer bootstrap que rechazó node_modules y la primera invocación de tsc no
son resultados de test. No se tocaron permisos del socket, contenedor de
desarrollo ni volúmenes existentes.

**Aceptaciones que permanecen cerradas:** E1–E6 local 6/6, Development R1–R4
4/4 y Certification 1/1. Se reutilizaron; ningún smoke se repitió.

**Gate documental exacto:** self-test/candidate-aware PASS, 751/751 fuentes,
119/119 documentos activos alcanzables, 433/433 históricos enlazados,
9.372 enlaces y 4.696 anchors. Log `selftest-final.log`, SHA-256
`fe816a1b04367ded34f502143d63f501df967178f5674df47ffac23f38f74250`.
Checker integral FAIL: baseline 350, candidato 348, mismo checker SHA-256
`f52eb76ad8ea5c64c3eb32ab4cd76661db5d7a33cd45aeb23311d6dc482d5da1`. La
ejecución candidata vigente reproduce log SHA-256
`0d43cdf829066c459ecffc28eb339b9d889c1a12f9e6dbd38adb0dfb90abbb10`; el
full-list asociado tiene SHA-256
`cb1767e4bdb2abc76d2d411b94b4713be9011d68e3c350008e3f0c86d696d0fe`; los
primeros 200 diagnósticos son iguales. La ejecución baseline vigente confirma
los primeros 200 del full-list baseline (350 total; SHA-256
`eae1107b5eba56ee9c9a9252f51ad241e95adda7328eb8a1ec33724a363524da`).
El candidato elimina los dos diagnósticos baseline-only
`INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT` y `REGISTRY_MARKDOWN_DRIFT`; no
añade diagnósticos únicos. Categorías residuales: 79 `CANDIDATE_ONLY_PATH_MISSING`,
79 `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE`, 79 `SOURCE_PATH_MISSING`, 88
`RELATION_PATH_MISSING`, 15 `EXCLUSION_PATH_MISSING`, cuatro
`DOCUMENT_EXCLUSION_PATH_MISSING` y cuatro `DOC_EXCLUSION_STALE`. Las tres
categorías de 79 son los mismos 79 paths únicos; las 88 relaciones apuntan a 20
paths únicos. Los 15 casos son exclusiones locales/generadas; los ocho casos
finales corresponden a cuatro originales privados excluidos con reemplazo
sanitizado. No se copiaron fuentes privadas, recrearon archivos ni retiraron
relaciones en masa. Disposición residual propuesta, no aprobada: solo este
candidato y su log integral; owner Romel/TL; riesgo de trazabilidad histórica
incompleta; vencimiento propuesto 2026-11-05 23:59 America/Lima o antes del
primer merge `certificacion→main`, lo que ocurra primero. No extiende #509,
#510 ni #511.

**Seguridad y siguientes gates:** el Codex Security scan previo usó snapshot
pre-fix y no acredita el árbol final. El scan de diff final queda separado y su
reporte se localiza desde el checkpoint externo. H2/Pro conserva 23 entradas de
ledger y objetos H2 parciales fuera de ledger; no se ejecutó report/verify ni
SQL. El paquete H3 mantiene 31 migraciones fijadas y hash de inventario
`52a4c8d60edad14af801f630be74a6286fc3e19ea6359940c7a6b5263c3240bd`; sin DDL,
workflow ni backfill. Pages/BFF/Access Production sin cambios y ningún secreto
leído. H1 sigue en preparación, sin FG1/FG2/FG3/schedules; H4 permanece en
preparación hasta evidencia del contrato H2 y secuencia H2→H3→H4.

**Punto de control:** NO-GO para publicación mientras el gate integral no tenga
una remediación demostrada o una disposición humana exacta aprobada. Tras
resolverlo, se necesita autorización independiente para commit, push no
forzado y PR a `desarrollo`; H2 agregado/report-verify, SQL H3 por workflow
protegido, Pages/BFF, cada promoción y smoke productivo requieren solicitudes
separadas. Ningún resultado local declara GO Pro.

## Cierre ampliado y gates de promoción H3REQ1 — corte previo, 2026-10-29 14:02–14:31 America/Lima

**Worktree/candidato:** `/tmp/studiamatch-h3req1-production-remediation-20261029`,
rama `codex/h3req1-production-remediation-20261029`, HEAD/base
`6f059a0b27ef38541a7b62503c78920e621f05c1`. Inventario de 27 paths (23 tracked
modificados y 4 nuevos); creció de 25 únicamente con los handoffs H1/H4.
Huellas finales: `/tmp/h3req1-production-remediation-20261029-final/candidate-fingerprint.txt`
y su hash externo; no se registran sus bytes dentro del propio inventario. Sin
commit, push, PR, merge, SQL, workflow, configuración remota ni deploy.

**Aceptaciones reusadas sin repetición:** E1–E6 local 6/6, Development R1–R4
4/4, Certification smoke 1/1. No se reasignan porcentajes entre matrices.

**Gates locales previos sobre el mismo código:** Docker, red deshabilitada y
checkout read-only: pytest focal 20/20; Node CA4.6 1/1; guard/selector/pins con
casos positivos y negativos fail-closed PASS; `git diff --check`, actionlint,
ShellCheck y credential scan PASS. La última edición posterior fue texto de
documentación en `admin_portal.md`; no cambió entradas de código/tests.

**Intento de cerrar los reruns documentales:** `studiamatch-dev:local` rechazó
el arranque por desajuste de hashes de Node, antes de ejecutar scanner alguno;
no es resultado de test. Se leyó el hash de una segunda imagen del proyecto y
coincidía con ambos manifests (`web/package.json` y `web/package-lock.json`).
La reconstrucción redundante se canceló. Se creó un volumen Docker exclusivo
para preparar Node deps, sin tocar `studiamatch_node_modules`; el daemon quedó
sin responder durante el provisionamiento. `docker info`/run acotados a 12 s
expiraron, y no se ejecutaron suites en esa última operación. No se cambió el
modo/permisos de `docker.sock`. La ruta del checkpoint externo es
`/tmp/h3req1-production-remediation-20261029-final/`.

**Integridad documental:** último self-test/candidate-aware disponible PASS:
751/751 fuentes asignadas, 119/119 documentos activos alcanzables y 433/433
históricos enlazados. Último checker integral oficial disponible FAIL: 348
diagnósticos, frente a 350 en baseline con mismo checker/config. Log previo al
último cambio documental:
`/tmp/h3req1-production-remediation-20261029-final/logs/candidate-final2-integral.log`,
SHA-256 `0d43cdf829066c459ecffc28eb339b9d889c1a12f9e6dbd38adb0dfb90abbb10`.
La última edición de `admin_portal.md` no se revalidó por el bloqueo Docker; el
hash/log anterior no se presenta como ejecución del árbol final exacto. Causas
reconciliadas por rutas únicas: 79 fuentes candidate-only locales sin historia
Git/copia autorizada; 88 relaciones que apuntan a 20 de esas rutas; 15
exclusiones locales/generadas ausentes; 8 diagnósticos sobre cuatro originales
privados excluidos con sucesores sanitizados. No se copiaron fuentes privadas,
no se recrearon artefactos, no se borraron relaciones ni se debilitó el checker.
La disposición para este residual está propuesta, NO aprobada: alcance solo
integral 348 del candidato exacto; owner Romel/TL; riesgo de trazabilidad
histórica incompleta sin señal demostrada de pérdida funcional o exposición;
vencimiento propuesto 2026-11-05 23:59 America/Lima o antes del primer merge
`certificacion→main`, lo que ocurra primero. Requiere decisión humana vinculada
a la nueva huella/log; no extiende #509/#510/#511 ni sustituye candidate-aware.

**Seguridad del diff:** scan Codex Security completado, scope de 11 superficies.
El snapshot inmutable `codex-security-snapshot/v1:sha256:f925f6c4ad7e1b9f0fb063ed05320439c97a6bd6a1f856307525c1b68bf3672c` precede la corrección del shell de workflow y conserva una finding CWE-78/P3.
El código actual pasa inputs por variables de entorno y shell citado; las pruebas
focales del workflow ya habían pasado y el árbol actual se inspeccionó manualmente.
El scan avisa que el worktree cambió mientras corría; no es scan inmutable
post-fix. Reporte generado en:
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/6f059a0b27ef38541a7b62503c78920e621f05c1_20261029T184334Z_f_0npl6f/report.md`.

**H2/Pro y H3:** Pro sigue en preflight SELECT-only: 23 entradas de ledger y
objetos H2 parciales fuera del ledger; no se leyeron ids/filas/cohorte. El
script `h2_pro_preflight_report.py` falla al detectar los objetos parciales
antes de emitir agregados. No está listo un dispatch de report/verify: requiere
delta local read-only que informe drift junto con conteos/digest sin filtrar
datos y tests focales. No reaplicar H2 por ledger. H3 mantiene manifest cerrado
de 31 SQLs, dependencias explícitas y digest de inventario
`52a4c8d60edad14af801f630be74a6286fc3e19ea6359940c7a6b5263c3240bd`; no hubo
DDL/PG17 ni ejecución remota. Hashes/rutas están en el manifest versionado.

**Handoff/operación:** H1 queda `PREPARATION_ONLY_PENDING_H2_H3_PRO_ACCEPTANCE`,
sin FG1/FG2/FG3/schedules. H4 queda
`PREPARATION_ONLY_PENDING_H2_CONTRACT_AND_SEQUENCE`, sin writers ni cambios de
producto. Pages/BFF Production permanece sin cambiar; no se leyeron secretos ni
se reutilizan claves Preview. Las aceptaciones remotas previas siguen cerradas;
no constituyen GO Pro.

**Siguiente gate:** recuperar Docker y correr exacto el self-test/candidate-aware,
integral y credential scan contra los bytes finales. Si el FAIL integral sigue
en 348 sin nuevos diagnósticos, solicitar disposición humana para huella/log
final; solo tras gate resuelto pedir autorización separada de commit/push no
forzado/PR a `desarrollo`. H2 agregado/verificación, SQL H3 mediante workflow
protegido, Pages/Access BFF, cada promoción y smoke productivo requieren JITs
independientes. No hay autorización de merge/promoción/producción en este corte.

## Corte intermedio de remediación local — histórico, 2026-10-29 13:28 America/Lima

### Baseline y alcance del paquete

Se continúa en el worktree aislado
`/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, desde
`desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`. El delta final actual
abarca 24 paths (20 modificados y 4 nuevos); la huella SHA-256 por path y sus
hashes están en el artefacto temporal de esta sesión, no en Git. Se preservaron
los demás checkouts/WIP. No hubo commit, push, PR, merge, SQL, workflow, Pages/
Access write ni deploy.

### Remediación local y evidencia focal

- **CA4.6:** `auditChanges` ignora una ausencia de `availability_status` solo
  cuando `admin_publish_course` la omite por contrato. Un `null` explícito, un
  cambio editorial o la eliminación permitida siguen apareciendo como cambio.
  La prueba nueva `tests/admin_audit_changes.test.mjs` pasa 1/1 en Docker. El
  hallazgo original es LOW: presentación engañosa en historial; no cambia la
  disponibilidad ni el evento persistido.
- **Selector:** la selección de `certificacion → main` y su push posterior usa
  el acumulado de manifests/diff, conserva pins y rechaza rutas/metadata
  ambiguas. `tests/test_protected_path_scope_guard.sh` pasa los casos positivos,
  negativos y fail-closed en Docker.
- **Manifest H3:** 31 migrations seleccionadas por lista exacta, SHA-256 y
  precedencias verificadas. `db_migrate.py`, `check_db_parity.py` y el workflow
  DB Sync existente lo consumen; el camino es main-only, no acepta selección
  parcial para Pro y exige el prerrequisito H2. No se ejecutó SQL, dispatch ni
  fixture PG17 con DDL.
- Tests de este delta en Docker/red deshabilitada: Python manifest/H2/main
  20/20; Node CA4.6 1/1; guard/selector PASS; actionlint del workflow PASS;
  ShellCheck de los dos scripts cambiados PASS. Estas son validaciones locales,
  no CI remoto. E1–E6 6/6, R1–R4 4/4 y Certification 1/1 se reutilizan sin
  repetición.

### Diagnóstico documental y disposición propuesta

El checker integral se ejecutó con el mismo binario/configuración vigente para
baseline y candidato: baseline 350 diagnósticos; candidato 348. Self-test y
candidate-aware son gates distintos y no neutralizan el FAIL integral. La
comparación previa 349→348 es histórica: el checker vigente también detecta en
baseline un Markdown generado desactualizado. El candidato resuelve dos errores
baseline-only (proyección candidate-only y Markdown desactualizado), no añade
diagnósticos únicos. El residual candidato se agrupa por ruta/categoría, no como
348 trabajos independientes:

| Causa única | Diagnósticos | Evidencia | Tratamiento |
|---|---:|---|---|
| 79 paths candidate-only ausentes en Git; existen solo como archivos locales ignorados/no trackeados en el checkout histórico | 237 | `unique-source-missing-paths.txt`, SHA-256 `0f6421a517ec47aa788c8662a7a30d7fbea0dc6b50681256589ecb11a3a034e3`; `known-copy-check.txt` | No copiar ni fabricar; mantener paths y pedir origen verificable si se desea reconciliar. |
| Relaciones que apuntan a 20 de esas 79 rutas | 88 | Mismo inventario de rutas; son 15 read-classification helpers, 15 tests, 10 tmpfs pairs, 10 npm-audit, 10 identidad Docker, 5 startup recovery, 5 source snapshot, 5 bootstrap lock, 4 dispatch cutover, 3 harvester, 3 Deno lock, 2 overrides y 1 bootstrap config | No borrar ni reasignar por semejanza. |
| Exclusiones locales/generadas/cache ausentes, en 7 registros | 15 | Diagnósticos exactos del checker e inventario externo | Mantener razón/trazabilidad; no recrear outputs. |
| Cuatro exclusiones de documentos históricos privados ausentes y sus stale warnings | 8 | Originals comprobados en checkout histórico; cuatro sucesores sanitizados versionados | No abrir/copiar originals; conservar sucesores sanitizados. |

Logs finales del mismo checker/configuración:
baseline 350:
`/tmp/h3req1-production-remediation-20261029-final/logs/baseline-integral-complete.log`,
SHA-256 `eae1107b5eba56ee9c9a9252f51ad241e95adda7328eb8a1ec33724a363524da`;
candidato 348:
`/tmp/h3req1-production-remediation-20261029-final/logs/candidate-integral-complete.log`,
SHA-256 `1715cb75adaa83c34e96a39b37481d313d3558513c40d48a1f58555225cacfb7`.
El checker normal imprime 200 filas; la copia temporal que generó el detalle
cambió solo el límite de impresión a 10.000 y conservó la misma lógica/exit.
Self-test + candidate-aware del árbol final: PASS, 751/751 fuentes, 119/119
activos, 433/433 históricos; log
`/tmp/h3req1-production-remediation-20261029-final/logs/candidate-scoped-self-test.log`,
SHA-256 `702c32812953a12d71fac23a9b258866b2ee3ab49dd00b4e8578affb2176fa3f`.
El inventario de 79 paths únicos está en
`/tmp/h3req1-production-remediation-20261029/unique-source-missing-paths.txt`,
SHA-256 `0f6421a517ec47aa788c8662a7a30d7fbea0dc6b50681256589ecb11a3a034e3`;
no se recopiaron documentos sensibles. El gate acotado preserva PASS, pero el
integral sigue FAIL y el paquete no se publicará mientras siga pendiente.

**Disposición propuesta, no aprobada ni aplicada:** exclusivamente los 348
diagnósticos integrales de este candidato y su log/huella final; causa,
reconciliación y evidencia arriba. Owner: Romel/TL. Riesgo: trazabilidad de
fuentes históricas incompleta; no hay evidencia de pérdida funcional ni de
exposición de seguridad. Vencimiento propuesto: 2026-11-05 23:59 America/Lima o
antes del primer merge `certificacion → main`, lo que ocurra primero. No extiende
#509/#510/#511. La decisión requiere el SHA/fingerprint final, y la aprobación no
autorizaría publicación por sí sola.

### Pro/H2 y lectura agregada pendiente

Preflight SELECT-only ya completado en `xwhtiqmboljkshrtviyw`: 23 migrations
hasta `20260607221002`; objetos H2 parciales fuera del ledger, `courses` con
SELECT directo público, sin las columnas snapshot y sin objetos Admin/H3. La
cohorte no se leyó.

El script actual `scripts/maintenance/h2_pro_preflight_report.py` lee por service
role los campos de curso necesarios para elegibilidad (`id`, institution, slug,
active/verified, URL) y flags agregados de perfil; consulta IDs visibles con
publishable y solo imprime conteos/digest/metadata. No obstante, cuando encuentra
objetos H2 previos al manifest, aborta antes de emitir el reporte. Por eso todavía
faltan `eligible_count`, `ordered_eligible_ids_digest`, `public_visible_count`,
`missing_from_public_count`, `unexpected_public_count` y grupos duplicados
institution/slug. La matriz no permite inferir esos valores ni decidir re-run.

La verificación local `public.h2_verify_expand_compat(integer,text)` requiere que
ya exista el schema/cohorte; valida elegibles/cohort/effective counts, identidad
exacta (missing/unexpected), digest, 28 columnas de proyección, cero columnas
privadas, `security_invoker`, RLS 3/3 y SELECT directo legacy todavía vigente.
Su implementación es STABLE SECURITY DEFINER con `search_path=pg_catalog,
pg_temp`; la migration local concede EXECUTE solo a service_role y revoca otros
roles. Esto es contrato fuente, no observación ACL remota de esa función. No se
invocó.

Solicitud futura exacta (no ejecutada): corregir primero el camino de reporte para
que, aun con drift parcial, termine entregando solamente esos agregados y metadata
de objetos, sin IDs ni filas; después solicitar aprobación separada para el
`workflow_dispatch` Pro en `xwhtiqmboljkshrtviyw`, `operation=report`, candidato y
SHA inmutables. No usar `apply`. Solo luego de verificar expand/cohorte exactos se
solicitaría autorización separada para invocar `h2_verify_expand_compat`; mantener
el reader legacy durante deploy. H2 expand files: schema compat, seed definitions,
backfill state, capture cohort y RLS cohort; no reaplicar ni marcar ledger por
conteo. Contract public-reader y contract legacy cohort son pasos posteriores.

### Pages/BFF y recuperación Pro

Cloudflare MCP se consultó con proyección server-side limitada a nombre, tipo y
presencia de entradas/bindings; no se devolvieron valores. Pages Production
`studiamatch`/`main` tiene URL y publishable-key bindings; `NEXT_SUPABASE_SECRET_KEY`
aparece `plain_text`, pero no se leyó el valor y el tipo por sí solo no acredita
exposición. No hay consumidor en `web/` ni Pages Functions locales; workflows y
scripts backend usan secrets de ambiente separados. No se retiró la variable.

Delta posterior que requiere JIT por separado: `ADMIN_ALLOWED_HOSTS` con el host
Admin productivo exacto; `ADMIN_QUOTA` service binding a
`studiamatch-admin-quota` tras verificar su Durable Object counter; tres HMAC
keys Production independientes por función y de Preview, por mecanismo seguro;
`ADMIN_RPC_GATEWAY_KEY_ID` respaldado por la fila Pro después de disponer schema.
Access se conserva Admin-only/6h. El rol gateway depende de la tabla de claves H3
y de una activación `pgrst.db_pre_request` con autorización propia; no se
aprovisionó nada ni se copiaron secretos.

**Transición/rollback:** Expand: cotejar H2 y aplicar únicamente cambios forward
compatibles, luego manifest H3 cerrado; Compatibilidad: mantener lector/cohorte
legacy y snapshot/auditoría; Deploy: PR protegido y Pages normal, con runtime y
bindings después de DB/verificación; Contract: retirar legacy solo tras paridad,
aceptación del runtime y estabilidad. Si falla, volver al deployment compatible,
preservar schema/auditoría/cohorte y corregir hacia delante; no borrar historia ni
restaurar datos masivamente.

### Resultado y siguiente decisión

Estado: remediación local de CA4.6/selector y mecanismo H3 preparada; tests focales
PASS; gate integral FAIL; H2 cohorte y report/verify pendientes; configuración
Production no modificada. NO-GO de publicación y producción. Siguiente decisión:
resolver o aprobar una disposición documental nueva, limitada a fingerprint/log
final; solo si el gate permite integrar, autorizar commit, push no forzado y PR a
`desarrollo` en una solicitud separada. El PR no autoriza merge, workflow, SQL,
configuración ni promoción.

## Cortes históricos previos — las observaciones de Pro pendiente/inaccesible quedan supersedidas por el preflight SELECT-only

### Cierre de verificación independiente — 2026-10-29 12:25 America/Lima

Inicio de esta pasada: **12:05 America/Lima**. Cierre: **12:25 America/Lima**.
No hubo modificación de producto/remoto: se conservan los 13 paths locales, sin
commit, push, PR, merge, SQL, workflow, configuración, deploy ni promoción.

GitHub MCP releyó las refs `desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`
y `certificacion@03515dee69fc42b10808d1c67cc4e00ebacd0c40`, ambas protegidas.
`main@70d0f4fee885be0f6780e5d14f466b2a6c897961` es el estado de la lectura previa;
no se abrió un candidato de promoción desde este worktree local.

La integración Supabase disponible no expone `mcp__supabase_pro`; el conector
alternativo denegó nuevamente URL, ledger y listado de tablas para
`xwhtiqmboljkshrtviyw`. Se conserva como evidencia aportada por TL, no revalidada
en esta conexión: 23 versiones reportadas, `course_editorial_state` y
`courses_public_effective` presentes, `admin_members` y
`h3_admin_rpc_gateway_keys` ausentes. No se consultaron filas/Auth/secretos ni se
ejecutó SQL. El script SELECT-only preparado tiene SHA-256
`f29fa1c6028e9fafd52c3a2371ddc4be6557618c5d0efa53f5dd747ac9168161`.

Cloudflare MCP confirmó por metadata la app Access de `admin.studiamatch.com`:
una política allow con un selector de correo y duración `6h`; no se devolvió la
dirección del usuario ni se cambió la política. No se repitió GET de Pages porque
el objeto de proyecto/deployment incluye `env_vars.value`; se reutiliza el estado
sanitizado previo y no se volvió a leer ningún valor secreto.

Docker Node 22, `--network none`, árbol del candidato montado read-only:

- Self-test + candidate-aware: **PASS**, exit 0; 749/749 fuentes asignadas,
  119/119 documentos activos alcanzables, 433/433 históricos enlazados. Log
  `/tmp/h3req1-production-remediation-20261029/final-continuation-candidate-aware.log`,
  SHA-256 `9c5329ebe100b56abd01149581b4a8669768c43a5ba1b822fdb4ef3e1a19feb9`.
- Checker integral/self-test: **FAIL esperado del gate**, exit 1, 348 diagnósticos
  (el output limitado muestra 200 + 148 resumidos); baseline 349 con el mismo
  checker/configuración. El detalle íntegro previamente capturado mantiene el
  desglose por ruta de § “Reconciliación de los 348 diagnósticos”. Log de esta
  corrida `/tmp/h3req1-production-remediation-20261029/final-continuation-integral.log`,
  SHA-256 `302f437b66f9f200494471ef1c2de7ff05b4a7bab433ff69a2c7549bbb4be381`.
- Scanner de credenciales: **PASS** en los 13 paths exactos del delta; log
  `/tmp/h3req1-production-remediation-20261029/final-continuation-credential-scan.log`,
  SHA-256 `c907c408226ecdd488273b9af102a9201a0efaf17a8d58788658a67652ca1396`.
- `git diff --check`: **PASS**. No se repitieron suites de producto: CA4.6 y
  selector no cambiaron desde sus pruebas focales Docker aceptadas; E1–E6 **6/6**,
  Development R1–R4 **4/4** y smoke Certification **1/1** se reutilizan sin
  reejecución.

El error inicial del contenedor de proyecto (`node_modules` fuera de sync) fue de
infraestructura y no ejecutó tests. El comando final usó la imagen Node 22 ya
disponible, vía Docker con permisos normales, sin tocar socket/volúmenes del
producto, con red deshabilitada y source montado read-only. No se convirtió el
FAIL integral en PASS ni se alteró el checker.

### Continuación: reconciliación Pro y fuentes documentales — 2026-10-29

#### Preflight Pro SELECT-only completado

Registro del preflight: **2026-10-29 12:45 America/Lima**.

El MCP WSL `mcp__supabase_pro` quedó visible después de la intervención de Romel.
`get_project_url` confirmó `https://xwhtiqmboljkshrtviyw.supabase.co`; el ref es
`xwhtiqmboljkshrtviyw`. `list_migrations` devolvió 23 versiones: primera
`20260525030610`, última `20260607221002`; ninguna versión H2/H3 posterior aparece
en ese ledger. La lectura estuvo acotada a catálogo de relaciones/columnas,
constraints, funciones (firma, `SECURITY DEFINER`, settings, digest y ACL), vistas,
policies, RLS y privileges. No se consultaron filas operativas, Auth, contenido de
claves ni secretos. Una primera agregación SELECT falló con PostgreSQL `42803`
(`aggregate function calls cannot be nested`); no tuvo efectos. La consulta
corregida y las dos consultas SELECT suplementarias terminaron correctamente.

#### Matriz Pro observada frente al contrato H2/H3

| Objeto requerido | Estado observado | Diferencia / consecuencia | Migración responsable | Dependencia y verificación que falta |
|---|---|---|---|---|
| Ledger `supabase_migrations.schema_migrations` | Existe; 23 versiones hasta `20260607221002` | No registra H2/H3 de agosto–octubre, aunque varios objetos H2 existen. Hay drift ledger/schema; el conteo no identifica apply. | Ninguna aislada; `scripts/maintenance/db_migrate.py` consume el ledger | En candidato inmutable, ejecutar `DB Sync to Production` en modo `report`/`verify`; no insertar marcas ni reaplicar sin comparar efecto de cada archivo. |
| H2 editorial: `courses`, `editorial_field_definitions`, `course_editorial_state`, `course_editorial_audit` | Presentes; columnas y checks editoriales consultados. RLS habilitado. | `availability_status`, override, versión, actor y auditoría existen; no se leyeron filas. `anon/authenticated` no tienen ACL de tabla para estado/audit; definitions permite SELECT filtrado a esos roles y DML a service_role. | `20260827_h2_pro_expand_schema_compat.sql`, `20260827_h2_pro_seed_editorial_field_definitions.sql`, evolución H2 | El expand manifest también incluye backfill/captura; cohort count/digest no se verificó. Cotejar metadatos exactos, ledger y `h2_verify_expand_compat` contra candidato; no ejecutar su RPC aquí. |
| Auditoría append-only | Audit presente, RLS; triggers `prevent_course_editorial_audit_update/delete` habilitados; helper no es SECURITY DEFINER, `search_path=pg_catalog`, ACL service_role/postgres. | ACL de tabla da permisos completos a service_role, mientras policies solo SELECT/INSERT y triggers bloquean UPDATE/DELETE. No se probaron writes. | H2 `20260827_h2_pro_expand_schema_compat.sql` y hardening H2 | Verificar trigger/policies/grants en el workflow H2; no tocar filas ni repetir smoke. |
| Cohorte legacy `private.h2_legacy_public_course_cohort` | Presente; RLS habilitado; anon/auth/service_role sin privilegios de tabla observados. | No se leyeron filas, conteos, IDs ni digests; estado de captura no queda acreditado. | `20260827_h2_pro_expand_schema_compat.sql`, `20260827_h2_pro_capture_legacy_cohort.sql`, `20260827_h2_pro_enable_legacy_cohort_rls.sql` | Requiere conteo/digest aprobados y `h2_verify_expand_compat`; cualquier invocación/apply exige JIT. |
| Reader público H2: `courses_public_effective` + `private.h2_public_courses_effective()` | Vista presente, `security_invoker=true`, SELECT para anon/auth/service_role. Helper SECURITY DEFINER, `search_path=pg_catalog, pg_temp`, EXECUTE explícito para esos roles. | `public.courses` conserva SELECT y DML ACL para anon/auth; sus policies para ambos son SELECT-only y la tabla tiene RLS. No se cuenta con prueba de denegación de writes. El contrato que retira SELECT directo aún no está aplicado. | H2 `20260827_h2_pro_contract_public_reader.sql`; rollback dedicado `20260827_h2_pro_rollback_public_reader_contract.sql` | El contract exige cohorte no vacía, paridad de conteo/digest y frontend compatible. Mantener legacy durante deploy; probar smoke antes de contraer. |
| H2 contrato de cohorte | No confirmado como aplicado; las condiciones de preflight del contract reader no se satisfacen porque SELECT directo sigue permitido. | No retirar cohorte ni policies por suposición. | `20260827_h2_pro_contract_legacy_cohort.sql` | Depende del reader contract y de paridad H2 estricta; verificar cohortes/digest en etapa autorizada. |
| Admin/RBAC: `admin_members`, `admin_invitations`, vistas/colas, secuencias y RPCs | No existen relaciones/seq `admin_*`/`h3_*` ni funciones `public.admin_*`/`private.h3_*`. | Contrato Admin H3 ausente en Pro. `exec_sql(sql_text text)` sí existe: SECURITY DEFINER, `search_path=pg_catalog, public`, EXECUTE solo service_role/postgres. | Base `20260828_h3_admin_auth.sql`, RBAC y contratos/fixes hasta `20261025_h3_admin_members_onboarding_forbidden_status.sql` | H2 public reader primero; después auth/RBAC, editorial/queue, invitaciones/onboarding y fixes en orden de dependencias. Workflow Pro actual no ofrece manifest H3. |
| Quota y gateway firmado | `private.h3_admin_quota_events`, `h3_admin_rpc_gateway_keys`, nonces y todos los RPC `h3_*` ausentes. | No hay base DB para cuota o gateway; aún no se confirma un key id de gateway. No se consultó key material. | `20261002_h3_admin_quota_expand.sql` antes de `20261002_h3_admin_quotas.sql`; `20261004_h3_admin_rpc_signed_gateway_expand.sql` antes de `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | Depende del set completo de RPC Admin. Provisionar key id/secret y binding de cuota solo con JIT independiente. |
| Snapshot publicado y guard de precio | Faltan `published_manual_overrides`, `published_manual_start_date`, `published_editorial_values`; faltan `admin_get_course_editorial`, `admin_update_course`, `admin_publish_course`. El helper H2 actual tiene digest `316b93d8f306a85204b816fe5cacc8e0`; el guard no se infiere por digest. | La proyección snapshot no está habilitada. No hay evidencia de que un borrador se separe de público en Pro. | `20261028_h3_editorial_publication_snapshot.sql` antes de `20261028_h3_public_price_projection_empty_price_guard.sql` | Requiere H2 reader y RPCs Admin; comparar firmas/ACL, columnas/constraints, `search_path` y vista, luego smoke remoto con JIT tras integración. |

RLS/ACL adicional: `public.courses` tiene RLS y las policies observadas para anon/authenticated son SELECT; service_role tiene policy ALL. `course_editorial_state` y audit son service_role-only; `editorial_field_definitions` usa policy pública `is_public=true`. El schema `private` concede USAGE a anon/auth/service para las funciones existentes, pero las tablas privadas no dan privilegios de tabla a esos roles. El ACL general de `public.courses` conserva grants DML a anon/authenticated; la falta de policies de escritura no se trató como prueba de runtime. El resultado completo de estas lecturas está en el transcript MCP de esta sesión; el archivo `/tmp/h3req1-production-remediation-20261029/pro-readonly-schema-preflight.sql` fue un borrador SELECT-only revisado, no se ejecutó en bloque.

#### Delta idempotente y orden preparado, no ejecutado

1. **H2 expand/compatibilidad:** el manifest cerrado `h2-expand-compat` contiene `20260827_h2_pro_expand_schema_compat`, `20260827_h2_pro_seed_editorial_field_definitions`, `20260827_h2_pro_backfill_editorial_state`, `20260827_h2_pro_capture_legacy_cohort` y `20260827_h2_pro_enable_legacy_cohort_rls`. La tabla/columnas ya existen, pero ledger no registra las versiones y no se inspeccionó estado de DML. Primero usar report/verify del candidato inmutable; apply requiere JIT DDL, backup/PITR, candidate/payload SHA, Production approval, conteo/digest de cohorte y review de Advisors. No resembrar/backfillear para demostrar estado.
2. **H2 deploy/contract:** dejar acceso directo legacy compatible durante el deploy normal de Pages; solo después del smoke autorizado y conteo/digest correctos considerar `h2-contract-public-reader`. El retiro posterior de cohorte usa manifest separado y depende del contract reader. `h2-rollback-public-reader-contract` es la ruta versionada de recuperación; no aplicar ahora.
3. **H3 DB:** antes de ejecutar migrations hay que ampliar por PR protegido el manifest cerrado de `DB Sync to Production`/`PRO_MIGRATION_MANIFESTS`; actualmente solo enumera F10-8 y H2. Orden funcional: Admin auth/RBAC → RPCs editoriales/colas e invitación/onboarding con hardening → quota EXPAND antes de wrappers → gateway EXPAND antes del wrapper acotado → snapshot editorial → guard de precio. La selección H3 exacta debe quedar fija por SHA y revisar todas las migrations del contrato; no usar `--only` en Pro ni aplicar la carpeta completa.
4. **H2/H3 verify:** cotejar ledger, firmas/retornos, columnas, constraints, triggers, policies, ACL efectivo, `SECURITY DEFINER`/`search_path`, vistas y advisors; el smoke Business de producción necesita JIT de escrituras separado. PostgreSQL 17 con DDL también requiere su propio JIT. Ningún SQL/fixture, workflow o cambio remoto se ejecutó en esta continuación.

#### Revalidación del checker en el árbol final evaluado — 2026-10-29

Tras actualizar el estado operativo y este checkpoint, se ejecutó de nuevo el
checker sobre el árbol candidato real, montado read-only en Docker Node 22 con
`--network none`; no se evaluó un snapshot anterior.

- Self-test y candidate-aware con el manifiesto exacto
  `.context/evidencia/h3req1_editorial_contract_candidate_scope_2026-10-28.json`:
  **PASS**, exit 0; salida `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`, 749/749 fuentes
  asignadas, 119/119 documentos activos alcanzables y 433/433 históricos
  enlazados. Log
  `/tmp/studiamatch-h3req1-production-remediation-20261029/final-pro-candidate-aware-self-test.log`,
  SHA-256 `48661c4af0bf3cf5db676ec57e728a24f446f5bfad8505ef1437b2c09e288e31`.
- Integral sin manifiesto: **FAIL**, exit 1, 348 diagnósticos; el baseline
  equivalente permanece en 349. El checker imprime 200 y resume 148; la lista
  íntegra candidata sigue archivada en los logs de reconciliación previos. Log
  `/tmp/studiamatch-h3req1-production-remediation-20261029/final-pro-integral.log`, SHA-256
  `3649c26e94e12737569b30f40b2166c1b759f30f7be751c2b2fb48777e10fbda`.
- La primera imagen local `studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`
  abortó antes del checker por `node_modules` fuera de sync; no cuenta como
  resultado. Se conservó el log
  `/tmp/studiamatch-h3req1-production-remediation-20261029/final-pro-project-image-infra-error.log`,
  SHA-256 `c00c0e69db4428db96c230e045f30c459263f7125cee004f81229c370157edb9`.
  La repetición usó la imagen limpia `node:22-bookworm-slim`
  (`sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d`),
  `--network none`, contenedor read-only y el árbol candidato montado read-only.
  Se distingue el error instrumental del resultado real del gate; no se cambió
  el checker ni se convirtió el FAIL integral en PASS.

#### Reconciliación de los 348 diagnósticos integrales por ruta

Se contrastaron rutas con el historial Git alcanzable del candidato y con el
checkout conocido `feat/h3req1-sync-20261002@a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`,
solo mediante rutas, tracking/status y existencia; no se abrieron los contenidos
locales. No se editó ese checkout.

| Grupo único | Diagnósticos | Hallazgo de trazabilidad | Decisión segura |
|---|---:|---|---|
| 79 rutas candidate-only sin archivo en el candidato | 237 (`SOURCE_PATH_MISSING`, `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE`, `CANDIDATE_ONLY_PATH_MISSING`) | `git log --all` del candidato no encuentra una versión; 0/79 están trackeadas en el checkout histórico. Las 79 existen allí como archivos locales no trackeados/ignorados. Familias: 56 `docker_peer_substep_diag`, 2 `docker_peer_phase_diag`, 16 herramientas/tests C03, 2 configs override, 2 bootstrap Deno y 1 test del pipeline. | Son WIP/diagnósticos locales, no fuentes autorizadas del candidato. No copiar ni fabricar; conservar referencias registradas para una conciliación con fuente verificable. Inventario solo de paths: `/tmp/h3req1-production-remediation-20261029/unique-source-missing-paths.txt`. |
| Referencias de relaciones a rutas faltantes | 88 sobre 20 rutas únicas | Las 20 están dentro de las 79 rutas anteriores. Reparto por familia: 15 read-classification helpers, 15 contract tests, 10 tmpfs pair, 10 npm audit, 10 identidad Docker, 5 startup recovery, 5 source snapshot, 5 bootstrap lock, 4 dispatch cutover, 3 harvester, 3 Deno versioned lock, 2 docker overrides, 1 bootstrap config. | No se eliminó ninguna relación. Sin fuente Git verificable no se reasigna a otra ruta por semejanza. |
| Exclusiones de fuentes locales/generadas ausentes en el candidato | 15 | Siete registros cubren 15 paths ausentes: preferencias Obsidian, captura OpenChamber, cache pytest, marcador Syncthing, sentinel del resolver Deno y dos outputs Next/TypeScript. Los paths señalados existen en el checkout histórico; el lock R3 existe también en el candidato, por eso su path no suma diagnóstico. Las razones del registro clasifican preferencias, cache y outputs generados; no son módulos del producto. | No son exclusiones globalmente obsoletas; faltan en este checkout de candidato. Se conservan. El detalle path-only está en `/tmp/h3req1-production-remediation-20261029/known-copy-check.txt`. |
| Cuatro originales de evidencia privada ausentes del candidato | 8 (4 exclusiones documentales + 4 stale) | Los originales son rastreables en el checkout histórico y están excluidos por identificadores personales. Sus cuatro sucesores sanitizados R18 están trackeados en el candidato; no se leyó ni copió ningún original. | Conservar exclusión y sucesores sanitizados. No recrear originales ni borrar la relación. |

El total sigue **348 FAIL** (237 + 88 + 15 + 8); el baseline fue 349. Los
diagnósticos no son 348 tareas independientes: corresponden a las rutas y
familias anteriores. Se conservaron las 79 relaciones fuente y las exclusiones;
no se cambió el checker ni se fabricaron artefactos. `--self-test` y
candidate-aware PASS previos (749/749) no reemplazan el integral. La disposición
de Certification (#511) está consumida y no cubre producción. Para resolverlo
antes de una decisión productiva, la opción mínima es una disposición nueva que
enumere solo el set de diagnósticos archivado, con owner Romel/TL, riesgo de
trazabilidad incompleta y vencimiento propuesto **2026-11-05 23:59 America/Lima o
antes del primer merge `certificacion → main`, lo que ocurra primero**. Aún no se
solicita/aprueba porque falta el SHA inmutable de promoción; al llegar a ese SHA
se debe regenerar el log y limitar la decisión exactamente a sus diagnósticos.

#### H2, Pages/Access, llave legacy y transición de producción

- H2 sigue sin evidencia actual para el candidato productivo: el run
  `33143730910` (`93c802c7`) es anterior y las remediaciones locales aún no tienen
  SHA publicado. Cuando exista un candidato inmutable en `certificacion`, se
  necesita un run nuevo de `DB Sync to Production` con branch/SHA y payload fijados,
  manifest/operación seleccionados por el diff real, y `verify` posterior. Para
  `h2-expand-compat`, `apply` además exige
  `ddl_authorization_id`, `backup_pitr_verified`, conteo/cohort digest exactos,
  Production environment approval, artefacto de evidencia y revisión de Security/
  Performance Advisors. Si el preflight prueba que no falta H2, no se reaplica:
  se ejecuta solo el `verify` compatible.
- Pages `studiamatch` / `main` usa `admin.studiamatch.com`. El delta BFF exacto
  preparado para un JIT posterior: `ADMIN_ALLOWED_HOSTS=admin.studiamatch.com`;
  `ADMIN_QUOTA` como service binding al Worker `studiamatch-admin-quota`; tres
  HMAC keys Production distintas entre sí y de Preview, cada una ≥32 bytes,
  creadas en el mecanismo seguro del ambiente; y
  `ADMIN_RPC_GATEWAY_KEY_ID` igual a un id válido que el preflight Pro confirme.
  Access existente sigue Admin-only/6h, sin cambios. No se copian valores de Free.
- `NEXT_SUPABASE_SECRET_KEY` aparece en Pages Production con tipo `plain_text`;
  el nombre no tiene consumidores en `web/` ni en Pages Functions en el árbol
  actual. Los workflows/scripts backend consumen sus variables separadas del
  ambiente/GitHub. El valor nunca se leyó. Acción preparada: JIT aparte para
  quitar esa variable de Pages Production y verificar solo su ausencia; rollback
  mediante reprovisión desde el almacén seguro, sin recuperar ni imprimir el
  valor actual. Las lecturas de Pages no se refrescaron porque el endpoint de
  proyecto/deployment devuelve el mapa completo `env_vars`, incluido `value`;
  se reutiliza únicamente el metadato sanitizado anterior y el análisis local de
  consumidores.
- **Expand:** cotejar y aplicar migrations forward-only exactas con JIT, sin
  sincronizar cursos operativos. **Compatibilidad:** conservar cohort/reader
  legacy y snapshots; no activar contract hasta probar el nuevo reader.
  **Deploy:** PRs protegidos `desarrollo → certificacion → main` y despliegue
  Pages normal, luego configuración/JIT de runtime. **Contract:** retirar
  compatibilidad solo con H2/H3 gates y estabilidad acreditados. **Rollback:**
  revertir código por PR/deployment previo y restaurar configuración desde
  metadata segura; mantener schema, snapshot y auditoría, sin down migration
  destructiva ni borrado de datos.

**Autorizaciones separadas todavía necesarias:** (a) commit, push no forzado y
PR de los 13 paths locales a `desarrollo`; (b) después del preflight y del
candidato real, JIT de workflow/SQL H2 o H3 si aplica y JIT Cloudflare para BFF,
binding y retiro de la variable legacy; (c) PR protegido a Certification y luego
`certificacion → main`, cada uno con review/merge separados. Este ciclo no ejecutó
ninguna operación protegida. E1–E6 6/6, R1–R4 4/4 y smoke Certification 1/1 se
reutilizan como evidencia cerrada; no se repitieron.

### Alcance, baseline y trabajo preservado

Inicio de esta continuación: **2026-10-29 10:45 America/Lima**. El trabajo se
realiza en `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, HEAD/base
`6f059a0b27ef38541a7b62503c78920e621f05c1` (`desarrollo`). El worktree documental
anterior conserva sus tres documentos locales y el checkout histórico conserva su
WIP; ninguno se sobrescribió ni se convirtió en fuente del candidato.

Aceptaciones reutilizadas sin repetir: E1–E6 local **6/6**, R1–R4 Development
**4/4**, smoke Certification **1/1** con borrador aislado, publicación visible,
auditoría y recuperación. No se recalcula un porcentaje global de H3REQ1.

### CA4.6: contrato de auditoría y corrección mínima

La observación se clasifica **severidad baja (S3)**: error de presentación que
puede sugerir falsamente que el estado de inscripción cambió durante publicación;
no hay mutación de disponibilidad, pérdida de auditoría ni acción sin permiso.
`admin_publish_course` conserva `availability_status` en `old_values` pero lo
omite de `new_values`, porque la RPC no cambia ese estado. La nueva
`web/src/lib/admin-audit-changes.mjs` ignora solo esa ausencia en eventos `publish`
para esa clave; no filtra omisiones generales. `null` explícito permanece
distinguible de clave ausente; una edición editorial real se conserva; al eliminar
un override permitido, el evento `update` conserva valor anterior→base nueva.

La prueba sintética nueva informa:
`admin-audit-changes=PASS|publish-omission=ignored|explicit-null=preserved|editorial-change=preserved|override-removal=preserved`.
No se modificó SQL, disponibilidad, cuentas ni datos remotos. Las pruebas de
aceptación anteriores quedan intactas.

### Selector para promoción certificacion→main

`security-audit.yml` ahora selecciona la unión exacta de manifests/documentos y
del diff completo en PR `certificacion -> main` y en el push posterior a `main`;
conserva `desarrollo -> certificacion`, sus pins, selección única ordinaria y
fallos cerrados. `tests/test_protected_path_scope_guard.sh` cubre ambas rutas y
los casos negativos de pin/baseline/ambigüedad. Docker informó:

```text
promotion-manifest-selector=PASS|development_to_certification=1|certification_to_main=1|postmerge_certification=1|postmerge_main=1|full_diff_and_package_union=1|exact_digests=1|missing_input=fail_closed|invalid_pr_scope=fail_closed|ordinary_PR_ambiguity=fail_closed
promotion-path-pins=PASS|exact_tree=1|neighbor_not_selected=1|wrong_baseline=fail_closed|forged_blob=fail_closed|duplicate=fail_closed|content_drift=fail_closed
```

No se cambió una allowlist ni una branch protection. Main sigue sin verificación
de protección por MCP: `GET /branches/main/protection` devolvió 403
`Resource not accessible by integration`; no se atribuye un estado no observado.

### Gate documental: baseline, candidato y causas

Se compararon baseline y candidato con el mismo checker/configuración. La corrida
oficial integral informa el total aunque limita su impresión normal a 200 líneas:
baseline **349** diagnósticos y candidato **348**. Para obtener la lista completa
del candidato se usó una copia temporal no versionada del checker que cambió solo
el límite de impresión de 200 a 10000; la lógica de validación y el árbol evaluado
permanecieron iguales. El selector candidate-aware y el self-test pasan para el
manifest exacto, con **749/749** fuentes asignadas; el integral permanece FAIL y
no se reporta PASS. El cambio del selector no degrada la cobertura acumulada.

Desglose candidato (348 ocurrencias):

- 79 paths candidate-only ausentes: cada uno produce `SOURCE_PATH_MISSING`,
  `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE` y `CANDIDATE_ONLY_PATH_MISSING`.
- 88 `RELATION_PATH_MISSING` repartidos en 20 paths únicos ya clasificados
  candidate-only; no se identificó un path de relación fuera de ese grupo.
- 15 referencias `EXCLUSION_PATH_MISSING` a restos locales/generados/cache, no a
  fuentes del candidato de producto.
- 4 `DOCUMENT_EXCLUSION_PATH_MISSING` y 4 `DOC_EXCLUSION_STALE` para referencias
  documentales históricas ausentes.

En el baseline, el JSON canónico esperaba 367 rutas candidate-only, pero el árbol
observado tenía 304 (`304 != 367`), lo que aporta un diagnóstico. Para el candidato
exacto desarrollo@`6f059a0b` + delta local, el JSON registra las cantidades
observadas: 444 fuentes de integración y 305 candidate-only. Así se elimina ese
mismatch específico en el candidato sin reducir cobertura ni borrar relaciones.
El self-test ya no exige la presencia física de dos nombres YAML retirados por
histórico: deriva esas fuentes del registro, exige que permanezcan asignadas y que
toda omisión física sea candidate-only y no seleccionada por el manifest exacto.
No se elimina relación en masa ni se fabrican archivos históricos. Los 348
diagnósticos restantes tienen causas demostradas: 79 rutas de exploración/WIP
histórico ausentes en este candidato (principalmente scripts de prueba/operación);
88 referencias de relaciones que apuntan a esas rutas; 15 exclusiones de artefactos
locales/generados/cache; y cuatro exclusiones de documentos históricos privados
ausentes con cuatro diagnósticos de exclusión obsoleta. El riesgo es que la relación
histórica no se puede verificar desde este árbol actual. Remediación mínima:
reconciliar cada ruta contra el historial Git o una copia autorizada, enlazar
reemplazos sanitizados sin recuperar documentos privados, y retirar solo exclusiones
generadas tras confirmar su origen. Owner: Romel/TL; ninguna disposición de
Certification cubre producción. Registros:
`/tmp/h3req1-production-remediation-20261029/baseline-integral-same-checker.log`,
`/tmp/h3req1-production-remediation-20261029/final-candidate-integral.log` y lista
completa del candidato
`/tmp/h3req1-production-remediation-20261029/final-candidate-full-diagnostics.log`.

### Refs, divergencia e integración local de main

Lecturas GitHub actuales: desarrollo
`6f059a0b27ef38541a7b62503c78920e621f05c1`, certificacion
`03515dee69fc42b10808d1c67cc4e00ebacd0c40`, main
`70d0f4fee885be0f6780e5d14f466b2a6c897961`. Certificación→main está divergida:
certificación 100 commits adelante y 4 detrás, merge base
`c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. La reconstrucción local de esos SHAs
con `git merge-tree` no encontró conflictos; tree sintético
`2028bdc24a720e5a0d19921b559134a9adf77f27`. El diff histórico completo abarca
1.619 paths (aprox. 709.433 adiciones y 149.740 eliminaciones) y 41 archivos de
migración (35 añadidos, 6 modificados); el API Compare expone solo sus primeros
300 archivos. Estos conteos describen un acumulado amplio, no solo H3REQ1.

No se actualizó ninguna rama remota. El tree local y el merge-tree no equivalen a
CI ni a integración autorizada.

### Pro y evidencia H2: corte anterior de las 11:21, actualizado por la continuación superior

Este snapshot registró que la única lectura MCP read-only a Pro
`xwhtiqmboljkshrtviyw` fue denegada y que ledger/schema no se observaron en ese
corte. El bloqueo de autenticación fue superado después según el TL, que reportó
lectura parcial (23 entradas y objetos concretos presentes/ausentes); véase la
actualización superior de esta continuación. El archivo SELECT-only también fue
ampliado después para consultar metadatos de columnas, constraints, policies,
RLS/ACL, funciones y vistas sin datos operativos ni valores de claves.

La evidencia H2 vigente local
`.context/operaciones/h2_main_production_expand_evidence.json` apunta al run
`33143730910`, SHA `93c802c7b0af2339a50ba3b4526fced9e1b3f7fd`; no acredita el
candidato actual. En la comparación con certificacion@`03515dee`, 1.625 paths
cambiaron y 644 quedan fuera del gate de evidencia H2. El workflow que exige el
gate es `DB Sync to Production` (`workflow_dispatch`, branch certificacion,
manifest `h2-expand-compat`, `operation=apply`, candidate/payload SHA fijados,
Production approval y verify/artifact/advisor results). No se ejecutó. Después de
conocer Pro schema/ledger se debe preparar JIT exacto de `apply` o decidir que el
baseline ya satisface H2; una diferencia de archivos no decide ese estado.

### Pages, Access y dependencias de runtime

Cloudflare read-only confirma Pages `studiamatch`, Production branch `main`,
deployment success `2b53bc74-576d-4e12-8b80-2986a857bde7`, SHA
`70d0f4fee885be0f6780e5d14f466b2a6c897961`, host `admin.studiamatch.com`; el
`NEXT_PUBLIC_SUPABASE_URL` reporta únicamente el host Pro
`xwhtiqmboljkshrtviyw.supabase.co`. No se leyeron valores de keys.

Production todavía carece de `ADMIN_ALLOWED_HOSTS`,
`ADMIN_QUOTA_HMAC_KEY`, `ADMIN_RPC_GATEWAY_HMAC_KEY`,
`ADMIN_SESSION_ACTIVITY_HMAC_KEY`, `ADMIN_RPC_GATEWAY_KEY_ID` y binding
`ADMIN_QUOTA`. Preview contiene las tres keys como `secret_text`, un key id,
hosts de preview/desarrollo/certificación, y servicio `ADMIN_QUOTA` →
`studiamatch-admin-quota`. Cloudflare Worker read-only confirma ese script y el DO
`ADMIN_QUOTA_COUNTER` (`AdminQuotaCounter`, sin route pública ni workers.dev).
Código BFF requiere HMAC keys de al menos 32 bytes y rechaza igualdad; la clave
de cuota separada entre ambientes mantiene digests de cuotas separados aunque el
Worker DO sea el backend compartido. Pro debe suministrar el key id ya válido; el
valor se contrasta por metadata SQL sin seleccionar su secreto.

La variable Pages `NEXT_SUPABASE_SECRET_KEY` existe en Production con tipo
`plain_text`; no se accedió a su valor y `rg` no encuentra consumidor bajo `web/`.
Los consumidores visibles de esa variable están en workflows/scripts backend,
que toman credenciales de GitHub/entorno, no del Pages runtime. Se recomienda
retirarla de Pages mediante JIT separado y verificar `web/` sin ella, o corregir
almacenamiento si se demuestra un consumidor; nunca copiar la key de Free.

Cloudflare Access mantiene la app self-hosted Admin para `admin.studiamatch.com`,
sesión 6h y un selector de email; el account tiene IdP Cloudflare y OTP. No hubo
cambio de Access. La configuración mínima futura es `ADMIN_ALLOWED_HOSTS` con
solo `admin.studiamatch.com`, las tres keys de Production distintas entre sí y
distintas a Preview, `ADMIN_RPC_GATEWAY_KEY_ID` igual a un id válido en Pro y el
binding `ADMIN_QUOTA` al servicio indicado. Se mantiene Access Admin-only, sin
colaboradores, comodines ni bypass.

### Matriz breve de gates sin mezclar denominadores

| Gate | Antes de este delta | Resultado local/observado | Acción mínima |
|---|---|---|---|
| CA4.6 audit UI | Publish mostraba disponibilidad omitida como cambio | 4/4 casos sintéticos PASS | Revisión/PR protegido a Development; ninguna escritura remota |
| Selector promoción | No agregaba certificacion→main ni push main | Regresiones y pins PASS en Docker | CI/review del PR cuando se autorice |
| Self-test/candidate-aware documental | Self-test tropezaba con dos rutas históricas; proyección 304/367 | Self-test PASS; 749/749; candidate-aware PASS | Conservar manifests exactos |
| Integral documental | Baseline 349 | Candidato 348; sigue FAIL | Reconciliar diagnósticos o nueva decisión humana para el candidato final |
| Pro ledger/schema | No observado en el snapshot anterior; el preflight SELECT-only superior ya lo completó | 23 entradas hasta `20260607221002`; núcleo H2 parcial fuera de ledger; reader contract no activo; H3 Admin, gateway, quota y columnas snapshot ausentes | No reaplicar por conteo. Reconciliar ledger/schema H2 con report/verify y evidencia de cohorte; preparar después manifest H3 cerrado por SHA y workflow protegido |
| Pages/Access Production | Host público y Access existentes; BFF no configurado | Sin cambios; faltan vars/binding BFF | JIT Cloudflare separado después del cotejo Pro |

### Transición, rollback, autorizaciones y punto de parada

- **Expand:** comprobar Pro ledger/schema con la consulta preparada. Solo crear
  migración forward-only si el drift está demostrado; aplicar una vez con JIT y
  verificar ledger, schema, RPC, views y ACL. Nunca inferir apply por diferencias
  de archivos ni reaplicar las migraciones Free compartidas.
- **Compatibilidad:** mantener el fallback legacy y el snapshot editorial; no
  copiar datos operativos entre Free y Pro. Configurar `ADMIN_QUOTA` y HMAC keys
  independientes por ambiente, sin reutilizar secretos de Free/Preview.
- **Deploy:** la promoción `certificacion -> main` se hace por PR protegido tras
  resolver el gate documental, H2, branch protection, aprobación y CI. Pages
  despliega desde main; no hacer deployment manual.
- **Contract:** después del smoke Production autorizado y estabilidad observada,
  retirar por PR las rutas/flags legacy que el contrato nuevo sustituye. No
  activar FG2/FG3, writers ni schedules en este ciclo.
- **Rollback:** restaurar el deployment Pages previo o revertir mediante PR;
  revertir configuración al snapshot previo usando el mecanismo de Cloudflare sin
  exponer valores; conservar schema, snapshots y auditoría append-only. No borrar
  filas ni ejecutar rollback destructivo; cualquier schema correctivo sería
  forward-only con JIT propio.

No se solicitaron ni consumieron JIT de Pro SQL, Pages, workflow H2, commit/push/PR,
merge, deployment o promoción. El paquete local requiere esas aprobaciones por
separado y detenerse antes de cualquier operación remota.

### Validación local final y paquete de preparación — 2026-10-29

Inicio de la continuación: **10:45 America/Lima**. Fin registrado: **11:21
America/Lima**. Worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`,
rama `codex/h3req1-production-remediation-20261029`, base `desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`.
El delta final contiene 13 paths (11 modificados, 2 nuevos), sin archivos de los
otros worktrees. No hubo commit, push, PR, merge, SQL, workflow remoto, Access,
configuración Pages, deploy ni promoción.

Resultados focales actuales, todos ejecutados en Docker con red deshabilitada y el
checkout de solo lectura:

- `admin_audit_changes.test.mjs`: PASS, cuatro casos — omisión de disponibilidad
  durante `publish`, `null` explícito, cambio editorial y eliminación permitida.
- `test_protected_path_scope_guard.sh`: PASS; selector PR/push de Development→Certification
  y Certification→main, agregación de paquetes + diff completo, hashes/pins y
  negativos de ambigüedad, baseline, input faltante y drift permanecen fail-closed.
- `actionlint 1.7.12`: PASS para `.github/workflows/security-audit.yml`.
- `scan_credentials.sh`: PASS para los 13 paths exactos; no se imprimieron valores.
- ESLint focal del editor/helper y `tsc --noEmit --incremental false`: exit 0.
- `git diff --check`: PASS. Los 13 inputs del paquete son los indicados en la
  sección `scope` del reporte de seguridad.
- Self-test + manifest candidate-aware exacto en Docker: PASS; 749/749 fuentes,
  119/119 documentos activos alcanzables y 433/433 documentos históricos enlazados.
- Checker integral oficial sin manifest: **exit 1, FAIL, 348 diagnósticos** para el
  candidato. Inventario completo conservado por una copia temporal del checker que
  cambia solo el límite de impresión (200→10000), sin alterar validación:
  348 líneas `DOC_GATE_FAIL`. Logs: `baseline-integral-same-checker.log`,
  `final-candidate-integral-closeout.log` y
  `final-candidate-full-diagnostics-closeout.log`, en
  `/tmp/h3req1-production-remediation-20261029/`.

La causa del delta baseline→candidato está acotada: el baseline observó 304 rutas
candidate-only contra un esperado obsoleto de 367, un diagnóstico; el candidato
actual registra 305 rutas candidate-only y 444 fuentes de integración (443 en
baseline), por lo que ese mismatch se corrige. Permanecen 348 diagnósticos: 79
rutas candidate-only ausentes generan 237 fallos de source/path; 88 relaciones
apuntan a 20 de esas rutas; 15 exclusiones corresponden a archivos locales,
generados o cache ausentes; cuatro documentos históricos privados ausentes generan
cuatro referencias documentales y cuatro exclusiones stale. El riesgo es trazabilidad
histórica incompleta. Solución: reconciliar rutas individualmente contra Git o
backups autorizados; apuntar a reemplazos sanitizados sin recuperar privados; retirar
solo exclusiones de artefactos cuya procedencia se confirme. Owner: Romel/TL. No
existe una disposición vigente para producción.

Revisión de seguridad del diff completada sin findings reportables, alcance patch
local; no es una auditoría global ni valida runtime Pro/Cloudflare. Scan
`d708fb6a-742b-45f1-9be9-2101ad7b2022`, base `6f059a0b27ef38541a7b62503c78920e621f05c1`,
snapshot `codex-security-snapshot/v1:sha256:d9e4aa4bd6bfd52cf89f98df5368be46fba717dcd6d2df521fae2676e1380c3c`.
El scan concluyó 11:16:46 UTC, antes de que se guardara esta actualización final
documental; el único delta posterior es prosa de estado/validación. Reporte
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/6f059a0b27ef38541a7b62503c78920e621f05c1_20261029T160407Z_4ofy2nqt/report.md`.
Recibo manual de las correcciones textuales después del snapshot:
`artifacts/03_coverage/manual_post_snapshot_docs_review.md` en el mismo directorio.

### Bloqueos y acciones exactas antes de producción

| Bloqueo | Evidencia/riesgo | Acción y autorización pendiente |
|---|---|---|
| El candidato productivo real todavía no incluye este delta; main no está protegido por una lectura verificada | Desarrollo@`6f059a0b`, Certification@`03515dee`, main@`70d0f4fe`; Certification→main aparece 100 commits adelante/4 detrás, el merge-tree local limpio no equivale a CI. Protection API de main devolvió 403 | Autorizar por separado commit local, push no forzado y PR a `desarrollo`. Después PR protegido desarrollo→certificacion y PR separado certificacion→main; verificar protection, review y CI con SHAs finales. Ningún merge queda autorizado aquí. |
| Gate documental integral | 348 diagnósticos; deuda de referencias históricas; PASS candidate-aware no sustituye FAIL integral | Remediación ruta por ruta verificable o nueva disposición humana específica para el SHA productivo final, con owner, riesgo y vencimiento. No extender #509/#510 ni la disposición de Certification. |
| Pro ledger/schema/H2 | Preflight MCP SELECT-only completado: 23 versiones; objetos H2 presentes pero no anotados en ledger; `courses` aún tiene grants directos de escritura a anon/authenticated; cohort rows/digest no consultados. Admin/H3 y snapshot ausentes. | Pro ya no está bloqueado por acceso. En candidato integrado, ejecutar solo `report/verify`; decidir H2 apply por objetos y ledger, no por conteo. Apply necesita JIT Production, backup/PITR y verificación de cohorte. H3 necesita un manifest cerrado por SHA y un workflow protegido que hoy no existe. Ningún dispatch ni SQL se ejecutó. |
| Runtime BFF/Pages Production incompleto | Pages `studiamatch` main desplegado `2b53bc74`, SHA `70d0f4fe`; faltan hosts Admin, tres HMAC, key-id y binding `ADMIN_QUOTA`. Access Admin-only/6h está vigente. No se leyeron valores de keys | JIT Cloudflare separado para `ADMIN_ALLOWED_HOSTS=admin.studiamatch.com`, tres HMAC aleatorias de ≥32 bytes y distintas entre sí/Preview, `ADMIN_RPC_GATEWAY_KEY_ID` igual a un id activo de Pro y binding al Worker existente `studiamatch-admin-quota`. La configuración se prepara luego del read-only Pro; aplicar por deployment normal autorizado. Access permanece igual. |
| Variable `NEXT_SUPABASE_SECRET_KEY` en Pages Production figura `plain_text` | Metadatos leídos; valor nunca leído; sin consumidor bajo `web/` | JIT aparte para retirarla de Pages Production, verificando consumidores antes/después. No copiar secretos de Free ni incluir valor en solicitudes. |

No se ejecutó nada de lo anterior. Orden de preparación: acceso Pro read-only → decidir H2 con ledger real → integrar el delta por PR protegido en desarrollo y promover por PRs separados → recalcular documentación y gates sobre el SHA final → aprobar/ejecutar SQL solo si el preflight demuestra drift → aplicar JIT Pages y despliegue normal → smoke mínimo Production con JIT de escritura/restauración si toca datos. `expand → compatibilidad → deploy → contract` y rollback están definidos en la sección anterior; no se activa pipeline, writer o schedule.

### Preparación de descripción PR — no publicada

Descripción basada en `.github/pull_request_template.md` preparada en
`/tmp/h3req1-production-remediation-pr-body.md`. La autorización necesaria para
publicar es exacta: commit de estos 13 paths sobre la rama actual, push no forzado
de `codex/h3req1-production-remediation-20261029` y PR hacia `desarrollo` con base
`6f059a0b27ef38541a7b62503c78920e621f05c1`. El CI/Preview automático habitual se
acepta solo bajo esa instrucción; no incluye merge, SQL ni configuración remota.

## Corte histórico — remediación local de promoción por TL previa al PR #510

Revisión posterior de continuidad: la sesión Luna conserva como último mensaje
el NO-GO del 2026-10-29 00:04:23 UTC; no hay continuación nueva acreditada allí.
Lectura GitHub actual confirma Development `941eca49`, Certification `c80f6504`,
main `70d0f4fe`; PR más reciente #509 integrado, sin PR posterior de remediación.
Los 15 archivos de esta rama permanecen WIP local. Se reutilizan las validaciones
anteriores porque no se cambió código ni configuración desde su cierre.

La UI GitHub permitió leer la protección clásica Certification `76533723` después
del 403 del conector: PR obligatorio, 1 aprobación, dismiss stale, aprobación del
último push por otra persona, security-audit, rama actualizada y sin bypass; sin
force pushes/deletions/lock. No se guardó ningún cambio. Se preparó descripción
PR con plantilla completa (`/tmp/h3-certification-pr-body.md`) y propuesta de
autorizaciones (`/tmp/h3-certification-remaining-jit.md`). Se solicitaron por
separado commit/push/PR hacia Development y retirada exclusiva de Certification
del ruleset adicional preservando main y protección clásica. No se presumen
aprobadas; sin respuesta no se ejecutan ni implican merge/promoción.

**Resultado final local:** selector y guard de rutas remediados para preparar el
acumulado completo elegido por el responsable. Suite completa Docker **PASS**,
incluido helper de pins con modo/tipo/objeto. Ensayos sobre refs reales en evento
PR y push posterior a Certification **PASS**: guard de rutas, selección de cuatro
manifiestos, unión de 1.614 paths (incluye el manifest nuevo) y checker/self-test
747/747 fuentes. Scope agregado final SHA-256
`8823ab542c34aea5bafa40afd1de442c132cd3e605a91ce31660b6315afee1d0`.
Los ensayos usaron el clon con WIP superpuesto; no son CI de un commit publicado.
Scanner final de los 15 archivos **PASS** (`credentials-final.log`); evidencia
final revalidada **PASS** (`documentation-final-evidence.log`); `git diff --check`
PASS. Los dos logs están en el mismo directorio de resultados indicado debajo.
Logs finales: `regressions-final.log`, `protected-paths-remediated-final.log`,
`protected-paths-push.log`, `selector-push.log` y `documentation-push.log` en
`/tmp/h3-certification-final-results/`. La revisión focal independiente del último
delta no encontró HIGH/CRITICAL/MEDIUM. No se repitieron pruebas de producto.

Los controles normales conservan su comportamiento. Solo el primer push de
Certification desde baseline `c80…` puede consumir los pins fuente `941…`; no se
autoriza cualquier sucesor ni se cubre `main`. El FAIL integral permanece separado.
Faltan integración protegida de esta remediación (con CI/approval de su HEAD),
disposición o corrección del integral para promoción, hostname/Access/redirects,
verificación de restricciones de rama y autorización/smoke Certification. Es GO
local de los dos controles corregidos; **NO-GO de ejecución de promoción** aún.

Continuación autorizada por el responsable: «Remedia bloqueos que luna tenga para
promover a certificación». Rama aislada
`codex/h3req1-certification-remediation-20261028`, worktree
`/tmp/studiamatch-h3req1-certification-remediation-20261028`, base local integrada
`941eca496676bd11cd0e2796e6c0a34efd62082d`. Se copiaron los siete documentos de
Luna sin modificar su worktree ni convertir su WIP en commit. No hubo commit,
push, PR, merge, writes remotos ni deploy.

### Diagnóstico y corrección

- Fetch de lectura completado: ambos árboles existen. `git rev-list --left-right
  --count c80f6504a3ea353bc2c222df1da09c4b5ba0ae58...941eca496676bd11cd0e2796e6c0a34efd62082d`
  da **9/97**, no 1/97. El diff desde el ancestro común abarca **1.618 archivos**.
  Estos conteos corrigen el corte anterior; no autorizan una resolución automática
  de conflictos ni prueban por sí solos la compatibilidad del merge.
- Ensayo de lectura `git merge-tree <ancestro> c80… 941…`: sin secciones de
  conflicto ni marcadores. Los 9 commits exclusivos de Certification son merges;
  `git diff --name-status <ancestro> c80…` está vacío. Por tanto el árbol destino
  no incorpora un delta de contenido independiente respecto de ese ancestro.
  Esto reduce el riesgo de conflicto textual, sin acreditar runtime/CI.
- Existen cuatro selecciones documentales y **tres** scopes de paths PR en el
  diff de evidencia, no dos. El selector anterior confundía los tipos y rechazaba
  la pluralidad. El cambio local distingue el schema de paths PR únicamente en
  promoción y agrega las cuatro selecciones más el diff completo, con hashes.
  En PRs normales conserva la selección única y el rechazo de ambigüedad.
- Regresiones Docker sin red, candidato read-only:
  `bash tests/test_protected_path_scope_guard.sh` **PASS**, incluidas regresiones
  previas y nuevas de promoción: unión/cobertura, hashes, ausencia de input,
  schema PR inválido y rechazo de ambigüedad normal. Log local:
  `/tmp/h3-certification-selector-tests.log`. Hubo una primera corrida FAIL por
  import ausente del test; se corrigió y revalidó. No se atribuye CI remoto.
  Después se añadió un caso adicional y su guarda: corromper el JSON de un
  manifiesto con rol ya presente en baseline debe fallar aunque su basename sea
  genérico. Tras el reintento humano autorizado, la suite final completa **PASS**;
  log `/tmp/h3-certification-selector-tests-final.log`. La revisión estática del
  bloque final tampoco encontró hallazgos; no se ejecutó CI remoto.
- Revisión focal independiente `security-auditor` de workflow/test: sin hallazgos
  de seguridad reportables; lectura estática sin operaciones remotas. Confirmó
  alcance de ruta, unión/cobertura, hashes, rutas seguras y controles negativos.
  No sustituye el ensayo real ni los gates pendientes.
- El árbol Certification `c80…` **no contiene el checker documental actual**.
  Por ello no es válido afirmar «349 idénticos en baseline/candidato» para esa
  promoción ejecutando comandos nativos equivalentes. Los 349 se refieren al
  baseline Development/candidato de #509; la ausencia del gate antiguo debe
  registrarse en la evaluación del delta real sin inventar un PASS del baseline.

### Configuración remota verificada en lectura

Proyecto Pages real: `studiamatch`, subdominio `studiamatch-aty.pages.dev`.
`ADMIN_ALLOWED_HOSTS` de Preview contiene exclusivamente
`feat-h3req1-sync-20261002.studiamatch-aty.pages.dev` y
`desarrollo.studiamatch-aty.pages.dev`; falta el alias de Certification. El
inventario Access completo de cuenta (4 apps, una página) contiene el host Admin
productivo, un deployment Development antiguo y apps ajenas; **ninguno incluye
certificacion.studiamatch-aty.pages.dev**. Esto reemplaza «Access no verificado»
por «no hay aplicación Access que cubra ese host según inventario leído»; no se
modificó ninguna policy ni se leen identidades/secretos.

La lectura API de ruleset `21255108` confirma que sigue activa con regla `update`
para `certificacion` y `main`. Development fue retirado en la remediación #509.
La ruta normal de merge de Certification debe verificarse antes de abrir/promover
el PR: esa restricción adicional puede reproducir el bloqueo de #509. No se usó
bypass ni se cambió la regla; cualquier remediación de ramas protegidas requiere
su instrucción humana específica, preservando PR/review/checks clásicos.

Paquete remoto a aprobar separadamente: añadir únicamente el hostname
Certification a la variable Preview preservando los dos valores; definir la
cobertura Access del panel y BFF de Certification mediante una policy de cuentas
de prueba autorizadas (sin ampliar a todo el catálogo público ni bypass). Debe
comprobarse también el callback Auth del host y la compatibilidad del Free
compartido antes del deploy. Ninguna autorización SQL se solicita: las dos
migraciones ya están aplicadas. No copiar secretos ni provisionar nuevos por
inferencia. Rollback de configuración: retirar exclusivamente la entrada/recursos
añadidos mediante alcance JIT aprobado, conservando Development y producción.

### Gates pendientes y límite de la ejecución

Las pruebas E1–E6 y R1–R4 siguen 6/6 y 4/4; no se repitieron. No hay un defecto
funcional nuevo acreditado contra CA4. La prueba del selector sobre el delta real
pasó: **4 paquetes / 1.613 paths supervivientes**, baseline `c80…`, HEAD `941…`,
scope SHA-256 `27953739f85650ded346ae2539e5b3e001a4edcda36f84030b516e8efb00eb09`.
El clon contiene los cambios locales superpuestos, no un commit publicado nuevo.
Primera corrida: FAIL `REGISTRY_MARKDOWN_DRIFT`; se regeneró la vista Markdown
desde JSON, se copió al candidato y se revalidó: **PASS**, self-test PASS,
747/747 fuentes, 119/119 documentos activos y 433/433 históricos enlazados.
Log `/tmp/h3-certification-real-promotion-gate-rendered.log`. El agregado usa el
diff de los refs exactos y añade los paquetes completos; los documentos locales
se validan en el mismo árbol superpuesto. Se requiere CI del futuro HEAD para
declarar integración. Queda preparar/publicar el PR con autorización separada y
resolver configuración/promoción/smoke.
El FAIL integral no se convierte en PASS ni se extiende la disposición #509.

La preparación del clon desechable para el ensayo real fue detenida antes de
ejecutarse: auto-review informó «application network permission was revoked» y no
pudo completar la revisión. Es fallo del mecanismo de autorización, no un rechazo
por inseguridad ni defecto del producto. El responsable autorizó reintentar y la
aplicación aceptó los comandos; **incidencia de permiso superada**, sin intervención
adicional necesaria ni elusión. Clon local y Docker se completaron después. No se
declara GO de promoción por esos checks locales.

Se intentó también pytest focal de workflow/security: no ejecutado porque esta
imagen no tiene pytest. No se instalaron dependencias ni se etiquetó ese intento
como PASS; la suite shell/Node/Python propia del selector sí se ejecutó completa.

### Gate completo y decisión de alcance

El wrapper obligatorio en el clon final terminó candidate-aware **exit 0 / PASS**
y modo integral `--self-test` **exit 1 / FAIL**. El integral contiene los 349
diagnósticos heredados más `DOC_SELF_TEST_FAILED` por una fuente diagnóstica
registrada ausente: **350 entradas de fallo**, no una regresión funcional nueva.
El comando previo de comparación sin `--self-test` reportaba 349. Se conservan
ambos modos separados; logs y exits en `/tmp/h3-certification-final-results/`.
El scanner de los 12 archivos modificados pasó en Docker; `git diff --check` PASS.

El ensayo adicional del guard real con `RUNNER_TEMP=/tmp` y baseline `c80…`
terminó **FAIL**: `protected path changed outside allowlists`. La primera corrida
sin RUNNER_TEMP no reprodujo Actions y falló por variable ausente; el segundo
ensayo sí incluyó esa variable y conserva el fallo genuino. Log:
`/tmp/h3-certification-real-protected-paths.log`.

Se enumeraron 1.484 paths del conjunto protegido en el delta real. La comparación
con regex H3/H3-extra y lista exacta local identifica **239 paths fuera de esa
lista H3**: 145 bajo evidencia `h3-expanded`, 23 migrations, más fuentes/config y
documentos anteriores. Algunos tienen cobertura legacy independiente; el fallo
del guard completo demuestra que ese fallback tampoco admite el conjunto.
No se confunden «fuera de lista actual» con «nunca aprobados». Lista diagnóstica:
`/tmp/h3-certification-unadmitted-paths.json`. No se amplió ninguna allowlist.

Este hallazgo afecta al alcance acumulado, más amplio que el arreglo editorial.
El responsable eligió explícitamente «Revisar y preparar el acumulado completo
de Development hacia Certification». Esa decisión habilita su preparación local,
sin merge/SQL/configuración remota. Se agregó el manifest exacto de 239 paths
adicionales con blobs baseline/origen, consumido solo en la ruta de promoción.
El caller fija separadamente baseline `c80…` y origen `941…`; exige ancestry y
modo/tipo/objeto HEAD idénticos al origen en cada path adicional. No usa un patrón
de carpeta ni acepta contenido nuevo por editar el manifest. La entrada del
manifest se admite por nombre exacto para su integración a Development.

Regresiones del primer corte PASS: pins correctos, vecino no seleccionado,
baseline incorrecto, blob falso, duplicado y drift de contenido; log
`/tmp/h3-certification-full-regressions.log`. Guard sobre delta real con ese
manifest PASS: `/tmp/h3-certification-final-results/protected-paths-remediated.log`.
Revisión independiente focal del guard/manifest/tests: sin HIGH/CRITICAL/MEDIUM,
estática sin writes. El endurecimiento posterior de modo/tipo/objeto se incluye
en la revalidación final, cuyos logs quedan en
`/tmp/h3-certification-final-results/`. No se atribuye aprobación funcional de
todo el acumulado ni CI remoto por admitir rutas.

**NO-GO de promoción se mantiene** hasta integrar la remediación, resolver/disponer
el FAIL integral para el candidato exacto y preparar hostname/Access/redirects y
ruta protegida. No hay un nuevo desarrollo funcional de CA4 identificado; sus
pruebas Development permanecen aceptadas. La validación por ambiente en
Certification sigue pendiente. No repetir SQL ya consumido ni invitaciones.

## Preparación de promoción a Certification

**Resultado del corte:** NO-GO — 2026-10-28 18:54 America/Lima.

### Tareas, gates y estado observado

| Gate | Resultado | Evidencia / límite |
|---|---|---|
| Autoridad y WIP | Revisado; WIP conservado | Se leyó `AGENTS.md`, `.context/indice.md`, estado operativo y esta evidencia. Al retomar, el worktree era `/tmp/studiamatch-h3req1-public-price-projection-20261028`, rama `codex/h3req1-public-price-projection-20261028`, HEAD `2b1f533444dab19528d5cb3d912ef6332dc20c41`; estaban modificados localmente estado/evidencia. Ese SHA es HEAD feature de #509, no el merge de desarrollo. El diff documental final se acotó a estado, checkpoint, atestación sanitizada, índice, ficha, navegación de hitos y matriz HITO-003. No se hizo fetch, cambio de rama, reset, commit ni publicación. |
| Promoción Git | NO-GO | Origen remoto confirmado: `desarrollo@941eca496676bd11cd0e2796e6c0a34efd62082d`. Destino: `certificacion@c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. Ancestro común `a6e39b993b2609641d20e9e24c513f35fd711b96`; Desarrollo tiene 97 commits desde ese ancestro y Certification conserva un commit. La promoción acumula cambios anteriores, no solo #508/#509. El objeto de merge `941…` no existe en este checkout, así que el candidato de promoción no fue reconstruido localmente. |
| PR #509 / CI | Evidencia reutilizada, no CI de promoción | #509 está integrado. Su HEAD `2b1f533444dab19528d5cb3d912ef6332dc20c41` recibió aprobación humana; CI de ese HEAD: 16 `success`, 2 `skipped` (`Supabase Preview`, `H2 Main Production Expand Gate`). Esos checks pertenecen al PR #509 y no acreditan el futuro PR a Certification ni el merge SHA. Ambas ramas reportan protegidas; los requisitos detallados de Certification no estuvieron disponibles por la lectura actual. No se usará bypass. |
| Pages | Deployment de Certification obsoleto frente al origen | Development sirve `https://desarrollo.studiamatch-aty.pages.dev`, deployment `87a65f76-b341-4e7c-9e50-ae5f3aa497f2`, `success`, SHA `941…`. Certification sirve `https://certificacion.studiamatch-aty.pages.dev`, deployment `3b28949c-7dfe-4b54-bf7a-0db77339d6ab`, `success`, SHA `c80…` (2026-08-28). El Preview de PR es distinto del deployment de rama. No se pidió ni hizo deploy manual. |
| Free / schema | Compatible; sin SQL pendiente para Certification | Development y Certification comparten Free `aqrldlmlszjtgpqiegaa`; estado `ACTIVE_HEALTHY`, PostgreSQL 17.6.1.166, ledger 83. Incluye `20261028194353` (`20261028_h3_editorial_publication_snapshot`) y `20261028230928` (`20261028_h3_public_price_projection_empty_price_guard`). No reaplicar, backfill ni cambiar datos. Pro es separado y queda fuera de esta etapa. |
| Configuración del hostname | BLOQUEANTE; JIT faltante | La configuración Preview de Cloudflare es compartida por las ramas no productivas. El `ADMIN_ALLOWED_HOSTS` observado contiene el alias feature y `desarrollo.studiamatch-aty.pages.dev`, pero no `certificacion.studiamatch-aty.pages.dev`. No se leyeron valores secretos ni se modificó configuración. El acceso Cloudflare Access para el host de Certification no quedó verificado. |
| Evidencia Development | ACEPTADA, solo en ese ambiente | E1–E6 local: 6/6; R1–R4 remoto Development: antes 2/4, después 4/4 (+50 pp). No son porcentajes globales de H3REQ1 ni prueba de Certification. R2/R3 restauraron y republicaron el `benefits` original; el público quedó sin marcador. |
| Gate documental | BLOQUEANTE sin resolución | El candidate-aware de #509 pasó 747/747 en su propio baseline/candidato. El checker integral de esa comparación falló con 349 diagnósticos en cada lado; 348 iguales, y el único delta reportado fue `INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT` 299→304 frente al esperado 367. Ese contraste no es c80→941. La disposición humana cubre solo #509 y expira antes de Certification. |

### Diagnóstico documental aplicado al alcance de promoción

El workflow `.github/workflows/security-audit.yml` selecciona archivos JSON por el nombre basename que contiene `candidate` y `scope`/`manifest`, o por rol `candidate-aware documentation integrity selection`; exige una única selección válida contra `PROTECTED_BASELINE_SHA`. En el delta remoto observado c80→941 aparecen seis archivos: dos `candidate-pr-scope` no tienen el schema (`manifest_role`, `scope.entries`, `package_artifacts`) y detonan `changed candidate-aware documentation manifest has an invalid structure`; cuatro manifests documentales válidos detonan `multiple candidate-aware documentation manifests changed; selection is ambiguous`. Este es un fallo reproducible por la regla actual del selector, no una atribución a los 349 diagnósticos heredados.

La corrección mínima no es eliminar manifests ni reducir alcance: construir un manifest agregador de promoción para el delta completo y adaptar el selector para elegirlo de forma explícita y validar que cubre la unión de los paquetes/manifests afectados, conservando todos los controles. Eso cambia el workflow/gate y requiere un PR focal a `desarrollo`, checks y aprobación propios. No está implementado ni autorizado por esta preparación. Hasta obtener los árboles c80 y 941 juntos tampoco se puede emitir una comparación integral exacta para Certification.

La regla operativa exige PR protegido a la rama destino, aprobación y el check de seguridad requerido; `AGENTS.md` además exige el self-test documental antes de integrar. No se encontró una regla que convierta un candidate-aware PASS de #509 en disposición del FAIL integral. Por ello la disposición #509 no se extiende: para Certification se requiere reconciliar el integral o presentar una disposición humana nueva, limitada al candidato exacto, después de obtener sus logs baseline/candidato. Riesgo residual de la disposición: fuentes y referencias históricas continuarían sin reconciliarse; owner propuesto: Romel/TL de documentación; caducidad propuesta para decisión: antes de promoción a `main` y no después del 04/11/2026 23:59 America/Lima. Esto es una propuesta, no una aprobación ni un waiver vigente.

**Validación Docker de esta actualización documental — 2026-10-28 18:58 America/Lima:** `git diff --check` PASS. Con `node:22-bookworm-slim`, red deshabilitada, mount read-only y el manifest `h3req1_editorial_contract_candidate_scope_2026-10-28.json`, `--self-test --candidate-manifest` PASS: 747/747 fuentes asignadas, 0 diagnósticos del gate; grafo 119/119 docs activos alcanzables, 433/433 históricos enlazados. El checker integral, mismo comando/configuración sin manifest, terminó exit 1 tanto en `git archive HEAD` (baseline local `2b1f533`) como en el worktree candidato: 349 diagnósticos cada uno, diff de líneas `DOC_GATE_FAIL` vacío; contador de proyección candidate-only 304 en ambos. El grafo subió de 9.334 a 9.339 enlaces y de 4.675 a 4.677 anchors por esta actualización; los anchors agregados se revalidaron. Logs reproducibles: `/tmp/h3req1-promotion-prep-20261028/logs/baseline.log` y `candidate.log`. Esto demuestra que los documentos locales no añaden diagnósticos sobre HEAD `2b1f`; no es el contraste de promoción `certificacion@c80… → desarrollo@941…` ni un PASS integral.

Después se actualizaron los resúmenes subordinados de HITO-003 para que el 5/6 histórico de E1–E6 y el estado R178 no parezcan actuales. La pasada final en Docker volvió a validar esos cambios; el candidate-aware sigue PASS y el integral conserva los 349 diagnósticos sin delta frente al baseline local. El paquete conserva NO-GO para el gate integral y la comparación exacta de promoción sigue pendiente.

**Conteos de la revalidación documental final:** candidate-aware PASS, 747/747 fuentes asignadas, 0 diagnósticos, 119/119 documentos activos alcanzables, 433/433 históricos enlazados; grafo 9.343 enlaces/4.679 anchors. Checker integral exit 1, 349 diagnósticos; diff `DOC_GATE_FAIL` baseline local/candidato vacío. Logs finales: `candidate-aware.log`, `baseline.log`, `candidate.log` en `/tmp/h3req1-promotion-prep-20261028/logs/`. Sigue sin ser un gate integral PASS ni una comparación c80→941.

En una corrida intermedia después de resumir HITO-003, el candidate-aware detectó tres `DOC_ORPHAN` (reporte de implementación, revisión de cierre y waiver enlazado transitivamente) porque se habían retirado los enlaces del índice de hitos. Se restauraron los dos enlaces históricos existentes; la corrida final documentada arriba pasó con 119/119 activos alcanzables. No se borró ni alteró la evidencia histórica.

### Matriz breve de CA vigentes y acción mínima

El backlog vigente asigna HITO-003 al criterio cliente `H3-CA4`. Los subcriterios `.1–.11` de la ficha son su descomposición interna histórica; la tabla no crea criterios nuevos ni porcentajes globales.

| CA | Evidencia reutilizable | Estado demostrado | Acción mínima para Certification |
|---|---|---|---|
| `H3-CA4` (panel editorial) | E1–E6 local 6/6; R1–R4 Development 4/4; atestación humana CA4 | ACEPTADO en Development; PENDIENTE en Certification | Destrabar gate documental y hostname; después verificar la ruta desplegada y ejecutar el smoke acotado del contrato. |
| `H3-CA4.1` Auth/RBAC | D01/D02/D06 y aceptaciones humanas de límites; R1/R3 con roles existentes | ACEPTADO en el alcance mínimo de Development | Reutilizar; en Certification validar acceso por el host nuevo y límites de rol solo si el smoke lo toca. |
| `H3-CA4.2` allowlist editorial | Implementación/E1 local; `benefits` poblado en R1–R3 Development | ACEPTADO para el contrato en Development; no es prueba remota exhaustiva de los 13 campos | Un campo poblado representativo; no repetir matriz de 13 campos. |
| `H3-CA4.3` transporte/RPC y controles | Evidencia de seguridad/RPC/cuotas aceptada previamente; no hubo cambios de este contrato en la aceptación | ACEPTADO por evidencia reutilizada, con el alcance/límites históricos | No repetir si código e inputs del transporte permanecen iguales; comprobar solo el BFF en el host de Certification. |
| `H3-CA4.4` cola | MIN-01 aceptado en la pasada mínima anterior | ACEPTADO para Development | Una consulta de pendientes por la sesión autorizada en el smoke de Certification; sin paginación/carga ampliada. |
| `H3-CA4.5` mutaciones | E1–E5 local; R1 edición, R2 borrador aislado del público y R3 publicación efectiva | ACEPTADO en Development | Smoke representativo con JIT y recuperación exacta; no repetir E1–E5 localmente. |
| `H3-CA4.6` auditoría | D09 aceptado; auditoría/versionado en E1/R1/R4 y eventos de la pasada remota | ACEPTADO en Development dentro del alcance verificado | Confirmar que el smoke de Certification deja evento visible a Admin; no repetir auditoría general. |
| `H3-CA4.7` MFA/`aal2` | Decisión humana previa lo dejó fuera del gate | FUERA DE GATE; no pendiente | Ninguna prueba o cambio de factor. |
| `H3-CA4.8` membresías | Aceptación humana del onboarding real y permisos básicos reutilizados | ACEPTADO en el recorrido aceptado; no se repite onboarding | Usar membresía existente; no enviar invitaciones ni cambiar roles. |
| `H3-CA4.9` hostname/Access | Host Development desplegado; deployment Certification antiguo. Allowlist Preview sin alias Certification; Access no verificado | PENDIENTE | Lectura/policy preflight; JIT específico para añadir el alias preservando entries actuales; luego smoke del BFF y la protección. |
| `H3-CA4.10` convergencia | Free compartido; ledger con ambas migraciones H3 | ACEPTADO para Development/Certification en el schema Free; Pro fuera de alcance | No aplicar SQL a Certification; cotejar Pro solo en una futura etapa de producción. |
| `H3-CA4.11` UAT/artefactos | E1–E6 locales 6/6; R1–R4 Development 4/4 | ACEPTADO local y en Development; PENDIENTE por ambiente en Certification | Smoke mínimo tras el PR/deployment; evidence específica del alias y SHA efectivos. |

### Paquete y secuencia sin ejecutar

- **Origen/destino:** `desarrollo@941eca496676bd11cd0e2796e6c0a34efd62082d` → `certificacion@c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. El delta amplio de 97 commits requiere revisión del PR completo; no está aislado a H3REQ1.
- **CI/protecciones:** #509 quedó aprobado y 16 checks success/2 skipped en su HEAD. Ambas ramas aparecen protegidas; detalle de reglas para Certification no verificado. No hubo CI/approval del futuro PR ni bypass.
- **Expand:** schema editorial y guard de precio ya aplicados una vez a Free compartido, versiones `20261028194353` y `20261028230928`; no hay migración Certification separada.
- **Compatibilidad:** mantener snapshots nullable, fallback para cursos sin snapshot, auditoría append-only y comportamiento legacy; no backfill ni contracción antes de estabilización.
- **Deploy:** abrir el PR protegido y dejar que el despliegue normal de rama genere el deployment Certification. No hacer build/deploy manual. Antes se necesita corregir el selector documental y resolver el host allowlist.
- **Contract:** solo tras estabilidad y aceptación autorizada; retirar el fallback legacy mediante delta revisado aparte. No contraer en esta preparación.
- **Rollback:** detener/retirar el código de app mediante PR revert protegido; conservar columnas, snapshots, cursos y auditoría. Si el cambio de allowlist se autoriza y falla, restaurar el valor anterior de `ADMIN_ALLOWED_HOSTS` según su JIT; no borrar datos ni revertir la migración aplicada.
- **Smoke mínimo propuesto:** comprobar deployment/SHA del alias; Admin existente consulta pendientes; colaborador con membresía existente corrige un campo poblado y el público mantiene el snapshot hasta publish; Admin publica; visitante sin sesión ve el valor exacto; historial/version/preview siguen operativos; restaurar y republicar el original incluido en el JIT. No repetir invitación/onboarding, cuotas ni los 14 escenarios. Como Free es compartido, el paquete JIT debe declarar el efecto de cualquier escritura sobre lectores de Development y Certification.

### Acciones no ejecutadas y autorizaciones necesarias

No se hicieron cambios remotos, commit, push, PR, merge, SQL, Auth, Access, configuración Cloudflare, workflow, deploy ni prueba de negocio en Certification. La autorización previa de #509 se consumió y era para otro destino.

1. **Autorización local de preparación de CI/manifiesto y documentación:** el selector necesita una corrección focal con PR a `desarrollo`; esta sesión solo deja diagnóstico. Se requiere instrucción para implementar y validar ese delta. La integración de los docs de aceptación que siguen sin commit también requiere autorización específica de commit/push/PR en una rama basada en SHA `941…`.
2. **JIT Cloudflare Preview:** solo cambiar `ADMIN_ALLOWED_HOSTS` para conservar los valores actuales e incluir `certificacion.studiamatch-aty.pages.dev`; confirmar la aplicación a Preview compartido, efecto en previews y recuperación al valor anterior. Sin modificar secretos, Access policies u otros bindings.
3. **Autorización de promoción:** abrir PR protegido `desarrollo → certificacion` tras resolver los gates, y posteriormente autorización separada de merge; no cubre SQL ni configuración.
4. **JIT de smoke Certification:** un curso/campo/fixture existente y valor de prueba/recovery exactos, roles existentes, lectura anónima, efecto visible debido al Free compartido y republicación restauradora. No reutilizar el JIT Development.

**Decisión de este corte:** NO-GO para solicitar/ejecutar la promoción; sí se completó el diagnóstico y el paquete local de preparación. No hay GO de Certification ni de producción. Hora inicial de esta continuación no quedó registrada al retomar el hilo; corte de verificación local: 2026-10-28 18:54 America/Lima.

## Addendum final — R2/R3 aceptadas y recuperación verificada — 2026-10-28

**Verificación de navegador terminada:** 18:33:18 America/Lima. **Checkpoint
documental cerrado:** 18:34:31 America/Lima. Esta continuación retomó el
checkpoint de las 18:19; la hora exacta de inicio de la sesión del navegador no
quedó expuesta por el puente. Ambiente Free/Development `aqrldlmlszjtgpqiegaa`,
host `desarrollo.studiamatch-aty.pages.dev`, deployment `27d9ebfc`, SHA integrado
`941eca496676bd11cd0e2796e6c0a34efd62082d`. PR #509 permanece integrado. La
migración correctiva de precio ya estaba aplicada una vez bajo su JIT separado:
`20261028230928`, 83 entradas de ledger; no se reejecutó ni se hizo otro cambio
de schema.

### Matriz remota R1–R4

Denominador fijo: 4. Antes de esta pasada: **2/4 = 50%** (R1/R4 aceptados;
R2 había fallado por `22P02`; R3 pendiente). Después: **4/4 = 100%**, delta
**+50 puntos porcentuales**. Se conservan separados los resultados históricos y
el arreglo posterior.

| ID | Resultado de esta pasada | Evidencia nueva / reutilizada |
|---|---|---|
| R1 | ACEPTADO, reutilizado | Edición de colaborador sobre campo poblado, persistencia tras recarga y auditoría de la pasada anterior; inputs/contrato no cambiaron. |
| R2 | ACEPTADO | En page 6 (Chrome Windows, contexto aislado de colaborador), curso ID `fd47da34-4a65-4a71-bc49-aea6db713500`, publicado v8 y `benefits` original. Colaborador guardó el marcador en v9 y recargó. Antes de publicar, page 3 anónima mostró únicamente los cuatro elementos originales; el marcador no se filtró. La lectura `courses_public_effective` respondió 200. |
| R3 | ACEPTADO | Admin publicó el borrador con marcador; tras recargar page 3 anónima, “Qué Incluye” mostró el texto exacto `* [H3REQ1 CA4 — verificación temporal 2026-10-28]` junto a los cuatro elementos originales. El preview Admin indicó “Curso publicado”; la versión avanzó a v10. |
| R4 | ACEPTADO, reutilizado | Historial/versión compacta y preview borrador/publicado aceptados en la pasada previa; no se repitió ese criterio. En esta ejecución el contador de historial llegó a 12 después de guardar/publicar y restaurar/publicar, compatible con registro append-only. |

### Restauración, efectos y recuperación del lector

- El mismo JIT exacto de R2/R3 incluyó restauración. Colaborador guardó el
  `benefits` original, SHA-256
  `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`, y recargó:
  versión v11, borrador original, preview publicado todavía con el marcador y
  aviso de diferencia. Admin republicó el original; versión v12, estado
  Publicado y preview publicado sin marcador.
- La última recarga anónima de page 3 mostró exactamente los cuatro beneficios
  originales, sin el marcador. Network del mismo curso: GET a
  `courses_public_effective` HTTP 200 (reqid 144 en la captura MCP final); la
  lectura de recomendaciones también respondió 200. No volvió a aparecer
  SQLSTATE `22P02`.
- Efectos persistentes limitados al curso/campo autorizados: dos ediciones de
  contenido y dos publicaciones, con versiones v9–v12 y eventos auditados. El
  texto público final quedó restaurado a su valor previo. No se tocaron otros
  campos, disponibilidad, membresías, cursos adicionales, pipeline, FG3,
  schedules, deployments, Pro ni Certification como ambiente de promoción.
- No hubo una nueva espera humana: la intervención Admin y el acceso previo del
  colaborador se completaron en sus sesiones Chrome existentes. No se solicitaron
  credenciales ni códigos.

### Resultado y gates restantes

GO de aceptación remota mínima del contrato corregido en Development: **SÍ**,
limitado a R1–R4 (4/4). No equivale a GO de promoción, producción ni cierre total
de H3REQ1. El FAIL integral del checker documental (349 diagnósticos heredados)
permanece visible; el PASS candidate-aware y la disposición humana exclusiva
para PR #509 siguen separados. Esa disposición es del owner Romel y vence el
04/11/2026 23:59 America/Lima o antes de promover a Certification, lo que ocurra
primero; no es un waiver global ni una aprobación de promoción.

Siguiente acción exacta: antes de cualquier promoción a Certification, resolver
o disponer el gate documental integral por el proceso humano aplicable y obtener
las autorizaciones específicas de promoción. No aplicar otra migración, no probar
remotamente en Certification/Pro y no ejecutar writers/schedules en este corte.

## Addendum — corrección SQL aplicada y lector público recuperado; R2/R3 pendientes — 2026-10-28

**Corte:** 18:19 America/Lima. En el Free compartido
`aqrldlmlszjtgpqiegaa` se aplicó una vez, con JIT exacto, la migración integrada
`db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql`
(SHA-256 `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b`).
Ledger confirmado: versión `20261028230928`, 83 entradas; no se reejecutará.
Verificación de solo lectura: `private.h2_public_courses_effective()` mantiene
`SECURITY DEFINER`, `search_path=pg_catalog, pg_temp`, EXECUTE para
`anon`/`authenticated`/`service_role`, sin EXECUTE para `PUBLIC`; la guarda segura
está presente y el cast numérico directo ya no aparece. La vista
`public.courses_public_effective` sigue como `security_invoker`, llama al helper y
permite SELECT a `anon`/`authenticated`.

En Chrome Windows, contexto anónimo aislado, la ruta del mismo curso IDAT ahora
carga y la request a `courses_public_effective` devuelve HTTP 200. El catálogo
detallado muestra “Python for Data Analyst” y el `benefits` aprobado original, con
sus cuatro elementos; no se volvió a observar `22P02`. Esto prueba recuperación
del lector público, pero no completa R2 sin la edición de borrador controlada.
Estado R1–R4 se conserva en 2/4 (50%) en este corte: R1/R4 aceptados, R2 aún
pendiente de revalidación tras el arreglo y R3 pendiente. La pasada anterior con
2/4 queda como antecedente; no se convierte el error histórico en PASS ni se repiten
R1/R4.

No se escribieron cursos ni se cambió pipeline, cuenta, disponibilidad, despliegue
o Pro. Tras completar el acceso en Chrome Windows, página 6, el editor confirma
curso publicado/completo, versión v8, `benefits` igual al original y los mismos
cuatro elementos en preview público. La página Admin 1 sigue en login; a las 18:14
se pidió al responsable completar acceso Admin. Se preparó y envió JIT nuevo para
R2/R3 y recuperación exacta; está pendiente y ninguna escritura de curso se ha
realizado bajo ese paquete. Siguiente paso: verificar el estado Admin después de la
intervención, esperar el JIT y luego ejecutar solo R2/R3 más la republicación del
original. Este corte se detiene a las 18:19 sin tratar la espera de intervención ni
la autorización pendiente como defecto técnico.

Validación documental local: `git diff --check` pasó. El self-test del checker de
integridad ejecutado en Docker efímero sin red y con worktree read-only terminó
FAIL (código 1), con 747/747 fuentes asignadas y errores de rutas/referencias
históricas; el FAIL integral de 349 diagnósticos y la disposición limitada a #509
siguen visibles, no se alteraron relaciones ni se declaró PASS. El wrapper de imagen
intentó inicializar `node_modules` y falló por volumen fuera de sincronía; el checker
sin dependencias externas se ejecutó directamente en el mismo contenedor aislado.
No se ejecutó un gate candidate-aware nuevo para este addendum documental.

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
reanudada para cerrar el PR a las 16:04 America/Lima; edición documental cerrada
localmente a las 16:07 America/Lima. El entorno es
`codex/h3req1-public-price-projection-20261028`, basado
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
  SHA-256 del archivo integrado: `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b`.
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
  modificar código. `python3 -m py_compile tests/test_h3_public_price_projection_migration.py`
  también pasó en Docker con el bytecode fuera del checkout.

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
- El PR #509 está abierto hacia `desarrollo`: rama
  `codex/h3req1-public-price-projection-20261028`, base
  `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, HEAD observado antes de este checkpoint
  `7cc3280351b3806853e48fd8993315a33619c3f9` (2 commits, 15 paths), URL
  `https://github.com/romelhc95/studiamatch/pull/509`. En ese SHA se leyeron 18
  check runs: 16 `success`, 2 `skipped`, ninguno fallido o pendiente. Cloudflare
  Pages informó `success` para el preview automático; no hubo smoke de negocio.
  `Supabase Preview` y `H2 Main Production Expand Gate` fueron `skipped`. El PR no
  está aprobado ni mergeado.
- El primer intento de push fue detenido por el hook pre-push, que escaneó el árbol
  completo al no existir upstream de la rama e indicó un patrón credential-like en
  `scripts/maintenance/debug_autocad.py`, path sin cambios y fuera del diff. No se
  copió ni modificó el valor. Tras verificar que `origin/desarrollo` coincidía con
  el baseline, se usó temporalmente como upstream según el mecanismo del hook; el
  escaneo del diff real pasó y el push fue no forzado.
- Esta continuación añade solo documentación canónica al PR existente. El commit
  documental genera otro SHA y checks nuevos; tras leerlos se actualizará la
  descripción del PR con la identificación final y resultados efectivos. R1–R4 no
  se repiten. No se hará SQL remoto, merge, deploy ni promoción.

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

## Corte posterior al merge #512 — preparación Desarrollo → Certification — 2026-10-29 23:49 America/Lima

### Tareas y gates

1. Reconciliar merge/refs y despliegue normal Development: PASS.
2. Evaluar candidato real Desarrollo → Certification con selector, pins y
   compatibilidad: NO-GO por el guard de pins obsoletos; no se abrió PR.
3. Evaluar integridad documental: candidate-aware PASS e integral FAIL separado.
4. Preparar la corrección mínima del guard en un worktree aislado y validarla en
   Docker: pruebas focales PASS; todavía no integrada ni publicada.
5. Preservar aceptaciones anteriores: E1–E6 6/6, R1–R4 4/4, smoke Certification
   1/1; no repetidas.

### Merge y deployment verificados

- PR #512 quedó integrado en Desarrollo con merge SHA
  `34469196c5ba4d073b49479f2fb44e84c279dbbb`; HEAD revisado del PR
  `317d5e7bc861e414ea1d806774de973abab9fa7b`. Certification sigue en
  `03515dee69fc42b10808d1c67cc4e00ebacd0c40`.
- CI del HEAD del PR: 16 success, 2 skipped (`Supabase Preview` y
  `H2 Main Production Expand Gate`), cero fallos/pending; aprobación humana
  vigente antes del merge.
- Cloudflare Pages Development: deployment
  `b8255fbf-19e6-4feb-ba06-bb687e079f46`, commit `34469196…`, success, alias
  `desarrollo.studiamatch-aty.pages.dev`. Origen: deployment normal del push de
  GitHub, sin deploy manual.
- Lectura Cloudflare limitada a metadatos de Preview: presentes los nombres de
  `ADMIN_ALLOWED_HOSTS`, HMAC keys, `ADMIN_RPC_GATEWAY_KEY_ID` y binding
  `ADMIN_QUOTA`. No se leyeron valores secretos.

### Candidato real y documentación

- Ancestro común: `6f059a0b27ef38541a7b62503c78920e621f05c1`; divergencia Git:
  10 commits adelante / 3 detrás. Delta certificacion→desarrollo: 31 archivos,
  +3582/−245. `merge-tree` terminó sin conflictos y su tree SHA
  `44478b685611db0b023bb179b9811b2a68658989` coincide con el tree de Desarrollo.
- El selector del workflow, con baseline `certificacion` y source `desarrollo`,
  eligió `.git/h3req1-promotion-documentation.json` y produjo 46 paths
  agregados. Self-test/candidate-aware PASS: 752/752 fuentes, 119/119 documentos
  activos, 433/433 históricos. Log candidate-aware SHA-256
  `94e37a107c94e94cf4d09f854a66d0fff186cee1891bf605bbeff4f36d10a502`.
- Checker integral: FAIL en ambos árboles; Certification 350 diagnósticos,
  Desarrollo 348, cero nuevos exclusivos y dos resueltos. El FAIL no se traduce
  a PASS por el gate acotado. Logs completos: baseline SHA-256
  `fc06f91f08f41752d705723b42e988dee98959fb1417dcb1d2173fe38ae4cc84`, candidato
  `e4326d0a6f3e491b5e95a3f724a9d9706f638a0ce49c39f4a5ea6bc704611cf9`. Listas
  únicas: baseline 350, SHA `416da38b2dd3cb7d4eba5c4742625c5eb24f3762401b1aa4cc3a88e09bb9e867`;
  candidato 348, SHA `e739d874045f360b218d5590fcd0b60cb46c6c248c337cddcce308ff9e1edaa0`.
  No se borraron relaciones ni se fabricaron fuentes.
- La disposición A asociada al paquete #512 cubría solo su candidato y está
  consumida. El responsable aprobó una disposición nueva el 2026-10-30 a las
  01:06 America/Lima para el diff local exacto `e6f072cc6a1e63eebe6cad9136b971917386f19ee1ffe432f4e6ba0902c209ce` (base Desarrollo
  `34469196c5ba4d073b49479f2fb44e84c279dbbb`, cinco paths), limitada a tramitar
  integración protegida a Desarrollo. Owner Romel/TL; riesgo de trazabilidad
  histórica incompleta; vence el 2026-11-05 23:59 America/Lima o antes de
  cualquier promoción a Certification. No convierte el integral FAIL en PASS ni
  autoriza commit, push, PR, review, merge o promoción. Se solicitará por
  separado autorización para commit/push/PR.
- Revalidación documental posterior a A, en Docker/red `none`: el checker se
  ejecutó sobre un archivo temporal derivado de los cinco paths exactos del diff
  y un archive del HEAD base. Resultado `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`,
  752/752 fuentes asignadas, 119/119 documentos activos alcanzables, 433/433
  históricos enlazados, 9.376 links y 4.699 anchors. Log:
  `/tmp/h3req1-a-approved-doc-self-test.log`, SHA-256
  `68349a36e11d1d6c371a497135d3c2a172af0b67db7db9a1f4532da0e8df7de4`.
  El manifest temporal selecciona esos cinco paths y no es artefacto de
  autorización ni de CI. Una invocación sin manifest no se cuenta como gate del
  candidato: incluye 305 fuentes candidate-only no seleccionadas y devuelve
  `DOC_GATE_FAIL`; el integral histórico continúa separado en 348 diagnósticos.

### Bloqueo de pins y corrección local no integrada

- Con refs reales `certificacion@03515dee…` y `desarrollo@34469196…`, el guard
  integrado rechaza la ruta porque su pin de promoción aún requiere baseline
  `c80f6504a3ea353bc2c222df1da09c4b5ba0ae58` y source
  `941eca496676bd11cd0e2796e6c0a34efd62082d`. Log del guard real:
  `/tmp/h3req1-certification-gates-34469196/protected-promotion.log`, SHA-256
  `1768889617e6cfcdb50867af65cb631424810b9cb905fcffceefeacf56e6936b`.
- En el worktree aislado `/tmp/studiamatch-h3req1-certification-review-20261029`
  (base integrada `34469196…`, sin commit), se conservó el contrato de pins. Se
  regeneró el manifiesto para baseline Certification `03515dee…` y source
  Development `34469196…`: 27 paths de blob inmutable. Los cuatro paths del
  candidato que cambiará el follow-up, además del manifiesto de pins, se excluyen
  de las entradas porque esos paths siguen sujetos a allowlists exactos y no pueden
  fijarse contra el árbol source que antecede al propio cambio. La prueba de pins
  no cambia y queda incluida entre los blobs fijados.
- Manifiesto local SHA-256
  `5edc9aa2f0273eb31d7f44640238d32ebf2db582bc836ec00759bc29d84b6797`. El guard
  conserva el gate de `desarrollo -> certificacion`, actualizado al par exacto
  `03515dee…` / `34469196…`; no hay bypass ni fallback a una allowlist abierta.
  La versión anterior del manifiesto sigue preservada en Git en el commit base,
  SHA-256 `3174c54ddb7ee689ccfaec47ee8f20a1c9c18631c2c7adfa4517a8969223d774`.
- Docker/red `none`: comparación del candidato real con los pins regenerados PASS;
  `tests/test_protected_path_scope_guard.sh`, `bash -n`, `git diff --check` y
  credential scan de los cinco paths modificados y el test existente PASS. La
  suite confirma 1.196
  rutas, 13 catálogos/1.173 referencias, selector y agregación de manifests,
  pins exactos, baseline equivocado, blobs falsos, duplicados, drift y negativos.
  El log final de suite y log del guard candidato se guardan en
  `/tmp/h3req1-certification-gates-34469196/final-pin-tests.log` y
  `final-protected-candidate.log`; SHA-256 respectivos:
  `1b5c60290a305231d2e466db3a3fef1b63da0507844f7df6248570615c9a3c69` y
  `3c12cc7d4f66c1ebe2406795845c81cf47bb3fac6debf03e8126959a2c7baa4f`.
  Credential scan: `c907c408226ecdd488273b9af102a9201a0efaf17a8d58788658a67652ca1396`;
  self-test documental: `94e37a107c94e94cf4d09f854a66d0fff186cee1891bf605bbeff4f36d10a502`.
  Checker integral diagnóstico final: `e4326d0a6f3e491b5e95a3f724a9d9706f638a0ce49c39f4a5ea6bc704611cf9`.
  ShellCheck no está disponible en la imagen; debe ejecutarse en CI después de
  que un PR protegido lleve el arreglo a Desarrollo. Esto no acredita el guard
  integrado ni el candidato actual.
- Tras actualizar el índice/estado, el primer self-test señaló el anchor roto del
  enlace al checkpoint; se quitó el fragmento y se repitió. Resultado final en
  Docker/red `none`: `DOC_SELF_TEST_PASS`, 752/752 fuentes asignadas, 119/119
  activos alcanzables, 433/433 históricos enlazados, 9.376 links y 4 paths
  candidate-only en el manifiesto local H3 editorial. `DOC_GATE_PASS`; log
  SHA-256 `94e37a107c94e94cf4d09f854a66d0fff186cee1891bf605bbeff4f36d10a502`.
  Esta pasada valida el índice y la evidencia local; el selector real de la
  promoción, ejecutado antes sobre el diff remoto exacto, seleccionó el agregado
  de 46 paths descrito arriba.
- Checker integral diagnóstico después de las ediciones locales produjo un log
  byte-idéntico al del Desarrollo integrado (`SHA-256
  e4326d0a6f3e491b5e95a3f724a9d9706f638a0ce49c39f4a5ea6bc704611cf9`): conserva
  348 diagnósticos y no agrega nuevos respecto del baseline actual. El baseline
  Certification sigue en 350. El FAIL integral no está resuelto.
- La revisión estática focal del patch se limitó al guard, pins y pruebas: el
  diff solo actualiza los SHAs esperados y blobs del manifest; permanecen el
  anclaje source/baseline, validación de rutas/duplicados, comparación de blobs,
  emisión solo tras validar todo y allowlists runtime sin ampliar. El test
  conserva vecinos negativos. El 2026-10-30 01:23 America/Lima Codex Security
  volvió a rechazar el inicio con `Working-tree contents changed after they were
  selected. Select Uncommitted changes again`; no hubo `scanId` ni scan completo.
  Este bloqueo del launcher no se presenta como ausencia de hallazgos. ShellCheck
  permanece pendiente de CI; no se afirma que el scan externo esté completado.
- Árbol de trabajo local: solo están modificados
  `scripts/security/protected_path_scope_guard.sh` y
  `tests/test_protected_path_scope_guard.sh` al iniciar este checkpoint; después
  se actualizaron localmente también esta evidencia, `estado_del_proyecto.md` e
  `indice.md`. No hubo commit, push, PR, merge, SQL, workflow, configuración ni
  deploy manual.

### Decisión y siguiente acción

**NO-GO para solicitar/crear PR Desarrollo → Certification**: el guard integrado
falla con el baseline efectivo y la corrección todavía no está integrada. La
disposición documental nueva fue aprobada solo para tramitar la integración
protegida a Desarrollo; el permiso de publicación aún falta. Después de integrar
el arreglo, releer las ramas y repetir únicamente selector/pins/gates
documentales afectados. Para Certification, evaluar nuevamente el residual y
obtener disposición y autorizaciones propias del candidato actualizado.

No repetir E1–E6, R1–R4 ni smoke Certification. No hubo aprobación de promoción,
no se ejecutó merge, DB Sync `report`, SQL H2/H3, workflow, cambio Pages/Access ni
deploy manual. Tras un futuro merge autorizado a Certification, verificar el
deployment real y preparar (sin ejecutar) el JIT `DB Sync to Production` con
`operation=report`, `migration_manifest=h2-expand-compat`, SHA/payload exactos y
`apply_authorized=false`.
